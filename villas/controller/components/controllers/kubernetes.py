import signal
import time
import threading
import kubernetes as k8s

from villas.controller.controller import Controller


class KubernetesController(Controller):

    def __init__(self, **args):
        super().__init__(**args)

        # try:
        k8s.config.load_kube_config()
        # except:
        #   k8s.config.load_incluster_config()

        self.namespace = args.get('namespace', 'default')
        self.job_dict = args.get('spec', {})

        self.job = k8s.utils.create_from_dict(self.job_dict)
        self.check_job()

        self.ressource = None

        self.thread_stop = threading.Event()

        self.pod_watcher_thread = threading.Thread(
            target=self._run_pod_watcher)
        self.event_watcher_thread = threading.Thread(
            target=self._run_event_watcher)

        self.pod_watcher_thread.start()
        self.event_watcher_thread.start()

    def __del__(self):
        self.thread_stop.set()

        self.pod_watcher_thread.join()
        self.event_watcher_thread.join()

    def check_job_body(self):
        if len(self.job.spec.containers) != 1:
            raise RuntimeError('Unsupported job spec')

    def start(self, message):
        b = k8s.client.BatchV1Api()
        self.ressource = b.create_namespaced_job(
            namespace=self.namespace,
            body=self.job)

    def stop(self, message):
        b = k8s.client.BatchV1Api()
        self.ressource = b.delete_namespaced_job(
            namespace=self.namespace,
            name=self.name)

    def pause(self, message):
        self.send_signal(signal.SIGSTOP)

    def resume(self, message):
        self.send_signal(signal.SIGCONT)

    def shutdown(self, message):
        pass

    def reset(self, message):
        self.started = time.time()

    def _run_event_watcher(self):
        w = k8s.watch.Watch()
        c = k8s.client.CoreV1Api()

        for event in w.stream(c.list_namespaced_event,
                              namespace=self.namespace):
            self.logger.info(event)

    def _run_pod_watcher(self):
        w = k8s.watch.Watch()
        c = k8s.client.CoreV1Api()

        for status in w.stream(c.list_namespaced_pod_status,
                               self.name, namespace=self.namespace):
            self.logger.info(status)

    def send_signal(self, sig):
        core_v1 = k8s.client.api.CoreV1Api()
        resp = k8s.stream.stream(core_v1.connect_get_namespaced_pod_exec,
                                 self.name, self.namespace,
                                 command=['kill', f'-{sig}', '1'],
                                 stderr=False, stdin=False,
                                 stdout=False, tty=False)

        self.logger.debug('Send signal %d to container: %s', sig, resp)
