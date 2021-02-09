import threading

from villas.node.node import Node
from villas.controller.components.controller import Controller
from villas.controller.components.gateways.villas_node import VILLASnodeGateway


class VILLASnodeController(Controller):

    def __init__(self, **args):

        self.node = Node(**args)
        self.status = self.node.status

        self.autostart = args.get('autostart', False)

        self.thread_stop = threading.Event()
        self.thread = threading.Thread(target=self.reconcile_periodically)
        self.thread.start()

        args['uuid'] = self.status['uuid']

        super().__init__(**args)

    def __del__(self):
        self.thread_stop.set()
        self.thread.join()

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
    def state(self):
        return {
            'villas_node_version': self.status['version'],

            **super().state
        }

    def on_ready(self):
        try:
            self.status = self.node.status
        except Exception:
            self.change_state('error', error='VILLASnode not installed')

        if self.autostart and not self.node.is_running():
            self.start()

        super().on_ready()

    def start(self, message=None):
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
