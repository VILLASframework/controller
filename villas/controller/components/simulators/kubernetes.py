import json
import signal
from copy import deepcopy
import collections
import time

import kubernetes as k8s

from villas.controller.components.simulator import Simulator
from villas.controller.exceptions import SimulationException


def merge(dict1, dict2):
    ''' Return a new dictionary by merging two dictionaries recursively. '''

    result = deepcopy(dict1)

    for key, value in dict2.items():
        if isinstance(value, collections.Mapping):
            result[key] = merge(result.get(key, {}), value)
        elif value is None:
            del result[key]
        else:
            result[key] = deepcopy(dict2[key])

    return result


class KubernetesJob(Simulator):

    def __init__(self, manager, **args):
        super().__init__(**args)

        self.manager = manager

        props = args.get('properties', {})

        # Job template which can be overwritten via start parameter
        self.jobdict = props.get('job')

        self.job = None
        self.pods = set()
        self.cm_name = ''

        self.custom_schema = props.get('schema', {})

    @property
    def schema(self):
        return {
            **self.custom_schema,
            **super().schema
        }

    def _prepare_job(self, job, payload):
        # Create config map
        cm = self._create_config_map(payload)
        self.cm_name = cm.metadata.name

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

        if job.metadata.labels is None:
            job.metadata.labels = {}

        job.metadata.labels.update({
            'controller': 'villas',
            'controller-uuid': self.manager.uuid,
            'uuid': self.uuid
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

        return c.create_namespaced_config_map(
            namespace=self.manager.namespace,
            body=self.cm
        )

    def _delete_job(self):
        if not self.job:
            return

        b = k8s.client.BatchV1Api()
        c = k8s.client.CoreV1Api()
        body = k8s.client.V1DeleteOptions(propagation_policy='Background')

        try:
            self.job = b.delete_namespaced_job(
                namespace=self.manager.namespace,
                name=self.job.metadata.name,
                body=body)
            c.delete_namespaced_config_map(
                namespace=self.manager.namespace,
                name=self.cm_name,
                body=body)
        except k8s.client.exceptions.ApiException as e:
            raise SimulationException(self, 'Kubernetes API error',
                                      error=str(e))

        self.pods.clear()

        self.job = None
        self.properties['job_name'] = None
        self.properties['pod_names'] = []

    def start(self, message):
        self._delete_job()

        payload = message.payload
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
        # job isn't immediately deleted
        # let the user see something is happening
        time.sleep(3)
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

    def pause(self, message):
        self._send_signal(signal.SIGSTOP)
        self.change_state('paused')

    def resume(self, message):
        self._send_signal(signal.SIGCONT)
        self.change_state('running')

    def reset(self, message):
        self._delete_job()
        super().reset(message)

        self.change_state('idle')

    def on_delete(self):
        self._delete_job()
