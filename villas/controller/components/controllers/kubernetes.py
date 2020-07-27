from ..controller import Controller

import asyncio
import threading
import kubernetes as k8s

k8s_core_v1 = k8s.client.CoreV1Api()
k8s_batch_v1 = k8s.client.BatchV1Api()

class KubernetesController(Controller):

    def __init__(self, **args):
        super().__init__(**args)

        #k8s.config.load_kube_config()
        #k8s.config.load_incluster_config

        self.config = args['config']
        self.body = args['spec']
        self.namespace = args['namespace']

        self.check_job_body()

        self.ressource = None

        self.start_job_watcher()
        self.start_pod_watcher()

        self.thread_stop = threading.Event()
        self.job_watcher_thread = threading.Thread(target = self._run_job_watcher)
        self.pod_watcher_thread = threading.Thread(target = self._run_pod_watcher)
        self.job_watcher_thread.start()
        self.pod_watcher_thread.start()

    def __del__(self):
        self.thread_stop.set()
        self.thread.join()

    def check_job_body(self):
        if len(self.body.spec.containers) != 1:
            raise RuntimeError("Unsupported job spec")

    def start(self, message):
        self.ressource = k8s_batch_v1.create_namespaced_job(namespace=self.namespace, body=self.body)

    def stop(self, message):
        self.ressource = k8s_batch_v1.delete_namespaced_job(namespace=self.namespace, name=self.name)

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

        for event in w.stream(k8s_core_v1.list_event_for_all_namespaces, namespace=self.namespace):
            self.logger.info(event)

    def _run_job_watcher(self):
        w = k8s.watch.Watch()

        k8s_core_v1.read_namespaced_pod_status()
        for event in w.stream(k8s_core_v1.read_namespaced_pod_status, namespace=self.namespace):
            self.logger.info(event)

    def _run_pod_watcher(self, pod):
        w = k8s.watch.Watch()

        for event in w.stream(k8s_core_v1.list_event_for_all_namespaces, namespace=self.namespace):
            self.logger.info(event)

    def start_watches(self):
        pass

    def send_signal(self, sig):
        resp = k8s.stream.stream(api_instance.connect_get_namespaced_pod_exec,
                    self.name,
                    self.namespace,
                    command=[ 'kill', '-%d' % sig, '1' ],
                    stderr=False, stdin=False,
                    stdout=False, tty=False)
        
        self.logger.debug("Send signal %d to container: %s", sig, resp)
