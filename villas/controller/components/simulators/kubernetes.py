from __future__ import annotations
from typing import TYPE_CHECKING
import json
import signal

import kubernetes as k8s

from villas.controller.components.simulator import Simulator
from villas.controller.exceptions import SimulationException
from villas.controller.util import merge

if TYPE_CHECKING:
    from villas.controller.components.managers.kubernetes \
        import KubernetesManager


class KubernetesJob(Simulator):

    def __init__(self, manager: KubernetesManager, **args):
        super().__init__(**args)

        self.manager = manager

        props = args.get('properties', {})

        # Job template which can be overwritten via start parameter
        self.jobdict = props.get('job')

        self.job = None
        self.pods = set()

        self.custom_schema = props.get('schema', {})

    @property
    def status(self):
        status = super().status

        status['status']['pod_names'] = list(self.pods)

        return status

    @property
    def schema(self):
        if (super().schema):
            return {
                **self.custom_schema,
                **super().schema
            }
        else:
            return {
                **self.custom_schema
            }

    def _owner(self):
        if self.manager.my_pod_name and self.manager.my_pod_uid:
            return k8s.client.V1OwnerReference(
                kind='Pod',
                name=self.manager.my_pod_name,
                uid=self.manager.my_pod_uid,
                api_version='v1'
            )

        return None

    def _prepare_job(self, job, payload):
        # Create config map
        cm = self._create_config_map(payload)

        # Create volumes
        v = k8s.client.V1Volume(
            name='payload',
            config_map=k8s.client.V1ConfigMapVolumeSource(
                name=cm.metadata.name
            )
        )

        vm = k8s.client.V1VolumeMount(
            name='payload',
            mount_path='/config/',
            read_only=True
        )

        env = k8s.client.V1EnvVar(
            name='VILLAS_PAYLOAD_FILE',
            value='/config/payload.json'
        )

        # add volumes to kubernetes job
        v1 = k8s.client.CoreV1Api()
        job = v1.api_client._ApiClient__deserialize(job, 'V1Job')

        if job.spec.template.spec.volumes is not None:
            job.spec.template.spec.volumes.append(v)
        else:
            job.spec.template.spec.volumes = [v]

        for c in job.spec.template.spec.containers:
            c.volume_mounts = [vm]
            if c.env is not None:
                c.env.append(env)
            else:
                c.env = [env]

        # Use generated names only
        name = job.metadata.name or 'villas-job'
        job.metadata.generate_name = name + '-'
        job.metadata.name = None

#        if o := self._owner():
#            job.metadata.owner_references = [o]

        if job.metadata.labels is None:
            job.metadata.labels = {}

        job.metadata.labels.update({
            'app.kubernetes.io/part-of': 'villas',
            'app.kubernetes.io/managed-by': 'villas-controller',
            'app.kubernetes.io/component': 'infrastructure-component',

            'villas.fein-aachen.org/ic-manager-uuid': self.manager.uuid,
            'villas.fein-aachen.org/ic-uuid': self.uuid
        })

        if job.metadata.annotations is None:
            job.metadata.annotations = {}

        job.metadata.annotations.update({
            'villas.fein-aachen.org/name': self.name,
            'villas.fein-aachen.org/location': self.location,
            'villas.fein-aachen.org/realm': self.realm
        })

        return job

    def _create_config_map(self, payload):
        c = k8s.client.CoreV1Api()

        self.cm = k8s.client.V1ConfigMap(
            metadata=k8s.client.V1ObjectMeta(
                generate_name='job-payload-'
            ),
            data={
                'payload.json': json.dumps(payload)
            }
        )

#        if o := self._owner():
#            self.cm.metadata.owner_references = [o]

        return c.create_namespaced_config_map(
            namespace=self.manager.namespace,
            body=self.cm
        )

    def _delete_job(self):
        if not self.job:
            return

        b = k8s.client.BatchV1Api()
        body = k8s.client.V1DeleteOptions(propagation_policy='Background')

        try:
            self.job = b.delete_namespaced_job(
                namespace=self.manager.namespace,
                name=self.job.metadata.name,
                body=body)
        except k8s.client.exceptions.ApiException as e:
            if e.status == 404:
                # Job does not exist, treat as already deleted
                return
            else:
                raise SimulationException(self, 'Kubernetes API error',
                                          error=str(e))

        self.pods.clear()

        self.job = None
        self.properties['job_name'] = None
        self.properties['pod_names'] = []

    def start(self, payload):
        # Delete prior job
        self._delete_job()

        job = payload.get('job', {})
        job = merge(self.jobdict, job)
        v1job = self._prepare_job(job, payload)

        b = k8s.client.BatchV1Api()
        try:
            self.job = b.create_namespaced_job(
                namespace=self.manager.namespace,
                body=v1job)
        except k8s.client.exceptions.ApiException as e:
            raise SimulationException(self, 'Kubernetes API error',
                                      error=str(e))

        self.properties['job_name'] = self.job.metadata.name
        self.properties['namespace'] = self.manager.namespace

    def stop(self, message):
        self.change_state('stopping', True)
        self._delete_job()
        self.change_state('idle')

    def _send_signal(self, sig):
        for pod in self.pods:
            self._send_signal_to_pod(sig, pod)

    def _send_signal_to_pod(self, sig, podname):
        c = k8s.client.CoreV1Api()
        try:
            resp = k8s.stream.stream(c.connect_get_namespaced_pod_exec,
                                     podname, self.manager.namespace,
                                     command=['kill', f'-{sig}', '1'],
                                     stderr=True, stdin=False,
                                     stdout=True, tty=False)

        except k8s.client.exceptions.ApiException as e:
            raise SimulationException(self, 'Kubernetes API error',
                                      error=str(e))

        self.logger.debug('Sent signal %d to container: %s', sig, resp)

    def pause(self, payload):
        self._send_signal(signal.SIGSTOP)
        self.change_state('paused')

    def resume(self, payload):
        self._send_signal(signal.SIGCONT)
        self.change_state('running')

    def reset(self, payload):
        self.change_state('resetting', True)
        self._delete_job()
        super().reset(payload)

        self.change_state('idle')

    def on_delete(self):
        self._delete_job()
