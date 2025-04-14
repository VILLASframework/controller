import os
import threading
import time
import kubernetes as k8s
from urllib3.exceptions import ProtocolError

from villas.controller.components.manager import Manager
from villas.controller.components.simulators.kubernetes import KubernetesJob


def _match(a, b):
    if a == b:
        return True
    elif len(a) < len(b):
        return a in b
    elif len(b) < len(a):
        return b in a


class KubernetesManager(Manager):

    def __init__(self, **args):
        super().__init__(**args)

        if os.environ.get('KUBECONFIG'):
            k8s.config.load_kube_config()
        else:
            k8s.config.load_incluster_config()

        # the namespace in which to create the jobs
        # and to watch for events
        self.namespace = os.environ.get('NAMESPACE')
        self.namespace = ''.join([self.namespace, '-controller'])

        # name and UID of the pod in which this controller is running
        # used in kubernetes simulator to set the owner reference
        self.my_pod_name = os.environ.get('POD_NAME')
        self.my_pod_uid = os.environ.get('POD_UID')

        self.thread_stop = threading.Event()

        self.pod_watcher_thread = threading.Thread(
            target=self._run_pod_watcher)
        self.job_watcher_thread = threading.Thread(
            target=self._run_job_watcher)
        self.event_watcher_thread = threading.Thread(
            target=self._run_event_watcher)

        self.event_watcher_thread.setDaemon(True)
        self.event_watcher_thread.start()

        # Not used yet, can support more complex logic
        # self.pod_watcher_thread.start()
        # self.job_watcher_thread.start()

    def _run_pod_watcher(self):
        w = k8s.watch.Watch()
        c = k8s.client.CoreV1Api()

        for sts in w.stream(c.list_namespaced_pod,
                            namespace=self.namespace):
            stso = sts.get('object')
            typ = sts.get('type')

            self.logger.info('%s Pod: %s', typ, stso.metadata.name)

    def _run_job_watcher(self):
        w = k8s.watch.Watch()
        b = k8s.client.BatchV1Api()

        for sts in w.stream(b.list_namespaced_job,
                            namespace=self.namespace):
            stso = sts.get('object')
            typ = sts.get('type')

            self.logger.info('%s Job: %s', typ, stso.metadata.name)

    def _run_event_watcher(self):
        while not self.thread_stop.is_set():
            w = k8s.watch.Watch()
            c = k8s.client.CoreV1Api()

            try:
                for e in w.stream(c.list_namespaced_event,
                                  namespace=self.namespace,
                                  timeout_seconds=5):

                    if self.thread_stop.is_set():
                        return

                    eo = e.get('object')

                    self.logger.info('Event: %s (reason=%s)', eo.message,
                                     eo.reason)

                    for uuid in self.components:
                        comp = self.components[uuid]

                        if not comp.job:
                            continue

                        if _match(comp.job.metadata.name,
                                  eo.involved_object.name):
                            if comp._state == 'stopping':
                                # incoming events are old repetitions
                                continue

                            if eo.reason == 'Completed':
                                comp.change_state('stopping', True)
                            elif eo.reason == 'Started':
                                comp.pods.add(eo.involved_object.name)
                                comp.change_state('running', True)
                            elif eo.reason == 'BackoffLimitExceeded':
                                comp.change_to_error('failed to start job',
                                                     reason=eo.reason)
                            elif eo.reason == 'Failed':
                                if comp._state == 'running':
                                    comp.change_to_error('failed to start job',
                                                         error=eo.reason)
                                elif comp._state == 'starting':
                                    # wait for BackoffLimitExceeded event
                                    continue
                            else:
                                self.logger.info('Reason \'%s\' not handled '
                                                 'for kubernetes simulator',
                                                 eo.reason)

            except ProtocolError:
                self.logger.warn('Connection to kubernetes broken, \
                                    attempting reconnect..')
                time.sleep(1)

    def create(self, payload):
        parameters = payload.get('parameters', {})
        comp = KubernetesJob(self, **parameters)

        self.add_component(comp)

    def delete(self, payload):
        parameters = payload.get('parameters')
        uuid = parameters.get('uuid')

        try:
            comp = self.components[uuid]

            comp.on_delete()
            self.remove_component(comp)

        except KeyError:
            self.logger.error('There is no component with UUID: %s', uuid)

    def on_shutdown(self):
        self.logger.info('Stopping Kubernetes watchers')
        self.thread_stop.set()

        if self.pod_watcher_thread.is_alive():
            self.pod_watcher_thread.join()

        if self.job_watcher_thread.is_alive():
            self.job_watcher_thread.join()

        if self.event_watcher_thread.is_alive():
            self.event_watcher_thread.join()

        return super().on_shutdown()
