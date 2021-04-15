import json
import signal
from copy import deepcopy
import collections

import kubernetes as k8s

from villas.controller.components.simulator import Simulator


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

        # Job template which can be overwritten via start parameter
        self.job = args.get('job')

    def __del__(self):
        pass

    def _prepare_job(self, job, parameters):
        c = k8s.client.CoreV1Api()

        cm = self._create_config_map(parameters)

        v = k8s.client.V1Volume(
            name='parameters',
            config_map=c.V1ConfigMapVolumeSource(
                name=cm.metadata.name
            )
        )

        vm = k8s.client.V1VolumeMount(
            name='parameters',
            mount_path='/config/',
            read_only=True
        )

        job.spec.template.spec.volumes.append(v)

        for c in job.spec.template.spec.containers:
            c.volume_mounts.append(vm)
            c.env.append(c.V1EnvVar(
                name='VILLAS_PARAMETERS_FILE',
                value='/config/parameters.json'
            ))

        return merge(job, {
            'metadata': {
                'name': None,
                'generateName': job.get('metadata').get('name') + '-',
                'labels': {
                    'controller': 'villas',
                    'controller-uuid': self.manager.uuid,
                    'uuid': self.uuid
                }
            }
        })

    def _create_config_map(self, parameters):
        c = k8s.client.CoreV1Api()

        self.cm = c.V1ConfigMap(
            metadata=c.V1ObjectMeta(
                generate_name='job-parameters-'
            ),
            data={
                'parameters.json': json.dumps(parameters)
            }
        )

        return c.create_namespaced_config_map(
            namespace=self.manager.namespace,
            body=self.cm
        )

    def start(self, message):
        job = message.payload.get('job', {})
        parameters = message.payload.get('parameters', {})

        job = merge(self.job, job)
        job = self._prepare_job(self.job, parameters)

        b = k8s.client.BatchV1Api()
        self.job = b.create_namespaced_job(
            namespace=self.manager.namespace,
            body=job)

    def stop(self, message):
        b = k8s.client.BatchV1Api()
        self.job = b.delete_namespaced_job(
            namespace=self.manager.namespace,
            name=self.job.metadata.name)

    def _send_signal(self, sig):
        c = k8s.client.api.CoreV1Api()
        resp = k8s.stream.stream(c.connect_get_namespaced_pod_exec,
                                 self.job.metadata.name, self.namespace,
                                 command=['kill', f'-{sig}', '1'],
                                 stderr=False, stdin=False,
                                 stdout=False, tty=False)

        self.logger.debug('Send signal %d to container: %s', sig, resp)

    def pause(self, message):
        self._send_signal(signal.SIGSTOP)

    def resume(self, message):
        self._send_signal(signal.SIGCONT)
