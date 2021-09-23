import threading

from villas.node.node import Node
from villas.controller.components.manager import Manager
from villas.controller.components.gateways.villas_node import VILLASnodeGateway


class VILLASnodeManager(Manager):

    def __init__(self, **args):

        self.autostart = args.get('autostart', False)
        self.api_url = args.get('url', 'http://localhost:8080') + '/api/v1'
        self.api_url_external = args.get('url_external', self.api_url)

        args['api_url'] = args.get('url', 'http://localhost:8080')

        self.node = Node(**args)

        self._status = self.node.status

        args['uuid'] = self._status.get('uuid')

        super().__init__(**args)

        self.thread_stop = threading.Event()
        self.thread = threading.Thread(target=self.reconcile_periodically)
        self.thread.start()

    def reconcile_periodically(self):
        while not self.thread_stop.wait(2):
            self.reconcile()

    def reconcile(self):
        try:
            for node in self.node.nodes:
                self.logger.debug('Found node %s on gateway: %s',
                                  node['name'], node)

                if node['uuid'] in self.components:
                    ic = self.components[node['uuid']]

                    # Update state
                    ic.change_state(node['state'])
                else:
                    ic = VILLASnodeGateway(self, node)

                    self.add_component(ic)

            self.change_state('running')

        except Exception as e:
            self.change_state('error', error=str(e))

    @property
    def status(self):
        return {
            **super().status,
            'villas_node_version': self.node.get_version()
        }

    def on_ready(self):
        if self.autostart and not self.node.is_running():
            self.start()

        try:
            self._status = self.node.status
        except Exception:
            self.change_state('error', error='VILLASnode not installed')

        super().on_ready()

    def on_shutdown(self):
        self.thread_stop.set()
        self.thread.join()

        return super().on_shutdown()

    def start(self, message):
        self.node.start()

        self.change_state('starting')

    def stop(self, message):
        if self.node.is_running():
            self.node.stop()

        self.change_state('idle')

        # Once the gateway shutsdown, all the gateway nodes are also shutdown
        for node in self.nodes:
            node.change_state('shutdown')

    def pause(self, message):
        self.node.pause()

        self.change_state('paused')

        # Once the gateway shutsdown, all the gateway nodes are also shutdown
        for node in self.nodes:
            node.change_state('paused')

    def resume(self, message):
        self.node.resume()

    def reset(self, message):
        self.node.restart()
