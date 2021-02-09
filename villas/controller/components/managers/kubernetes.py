import signal
import os
import json
import threading
import kubernetes as k8s
import collections
from copy import deepcopy

from villas.controller.components.manager import Manager
from villas.controller.component import Component


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


class KubernetesJob(Component):

    def __init__(self, controller, props):
        super().__init__(**props)

        self.controller = controller

        self.pod = props.get('pod')

    def __del__(self):
        pass

    def _prepare_pod(self, pod, parameters):
        c = k8s.client.CoreV1Api()

        cm = self._create_config_map(parameters)

        v = c.V1Volume(
            name='parameters',
            config_map=c.V1ConfigMapVolumeSource(
                name=cm.metadata.name
            )
        )

        vm = c.V1VolumeMount(
            name='parameters',
            mount_path='/config/',
            read_only=True
        )

        pod.spec.volumes.append(v)

        for c in pod.spec.containers:
            c.volume_mounts.append(vm)

        return merge(pod, {
            'metadata': {
                'name': None,
                'generateName': pod.get('metadata').get('name') + '-',
                'labels': {
                    'controller': 'villas',
                    'controller-uuid': self.controller.uuid,
                    'uuid': self.uuid
                }
            }
        })

    def _create_config_map(self, parameters):
        c = k8s.client.CoreV1Api()

        self.cm = c.V1ConfigMap(
            metadata=c.V1ObjectMeta(
                generate_name='pod-parameters-'
            ),
            data={
                'parameters.json': json.dumps(parameters)
            }
        )

        return c.create_namespaced_config_map(
            namespace=self.controller.namespace,
            body=self.cm
        )

    def start(self, message):
        parameters = message.payload.get('parameters', {})

        pod = self._prepare_pod(self.pod, parameters)

        c = k8s.client.CoreV1Api()
        self.pod = c.create_namespaced_pod(
            namespace=self.controller.namespace,
            body=pod)

    def stop(self, message):
        c = k8s.client.CoreV1Api()
        self.pod = c.delete_namespaced_pod(
            namespace=self.controller.namespace,
            name=self.pod.metadata.name)

    def _send_signal(self, sig):
        c = k8s.client.api.CoreV1Api()
        resp = k8s.stream.stream(c.connect_get_namespaced_pod_exec,
                                 self.pod.metadata.name, self.namespace,
                                 command=['kill', f'-{sig}', '1'],
                                 stderr=False, stdin=False,
                                 stdout=False, tty=False)

        self.logger.debug('Send signal %d to container: %s', sig, resp)

    def pause(self, message):
        self._send_signal(signal.SIGSTOP)

    def resume(self, message):
        self._send_signal(signal.SIGCONT)


class KubernetesManager(Manager):

    def __init__(self, **args):
        super().__init__(**args)

        self.thread_stop = threading.Event()

        self.pod_watcher_thread = threading.Thread(
            target=self._run_pod_watcher)
        self.event_watcher_thread = threading.Thread(
            target=self._run_event_watcher)

        if os.environ.get('KUBECONFIG'):
            k8s.config.load_kube_config()
        else:
            k8s.config.load_incluster_config()

        self.namespace = args.get('namespace', 'default')

        self._check_namespace(self.namespace)

        self.pod_watcher_thread.start()
        self.event_watcher_thread.start()

    def __del__(self):
        self.logger.info('Stopping Kubernetes watchers')
        self.thread_stop.set()

        if self.pod_watcher_thread.is_alive():
            self.pod_watcher_thread.join()

        if self.event_watcher_thread.is_alive():
            self.event_watcher_thread.join()

    def _check_namespace(self, ns):
        c = k8s.client.CoreV1Api()

        namespaces = c.list_namespace()
        for namespace in namespaces.items:
            if namespace.metadata.name == ns:
                return

        raise RuntimeError(f'Namespace {ns} does not exist')

    def _run_event_watcher(self):
        w = k8s.watch.Watch()
        c = k8s.client.CoreV1Api()

        for e in w.stream(c.list_namespaced_event,
                          namespace=self.namespace):
            eo = e.get('object')

            self.logger.info('Event: %s (reason=%s)', eo.message, eo.reason)

    def _run_pod_watcher(self):
        w = k8s.watch.Watch()
        c = k8s.client.CoreV1Api()

        for sts in w.stream(c.list_namespaced_pod,
                            namespace=self.namespace):
            stso = sts.get('object')
            typ = sts.get('type')

            self.logger.info('%s Pod: %s', typ, stso.metadata.name)

    def create(self, message):
        parameters = message.payload.get('parameters')

        ic = KubernetesJob(self, parameters)

        self.add_component(ic)
