import dpsimpy
import math
from threading import Thread
import os

from villas.controller.components.simulator import Simulator


class DPsimSimulator(Simulator):

    def __init__(self, **args):
        self.sim = None
        self.thread = Thread(target=self.sim_loop)
        self.count = 0
        self.current = 0
        super().__init__(**args)

    @property
    def headers(self):
        headers = super().headers

        headers['type'] = 'dpsim'
        headers['version'] = '0.1.0'

        return headers

    def load_cim(self, fp):
        if fp is not None:
            name = self.params.get("name",str(os.urandom(6).hex()))
            freq = self.params.get("system-freq",50)
            domain_str = self.params.get("solver-domain","SP")
            solver_str = self.params.get("solver-type","MNA")
            duration = self.params.get("duration",10)
            timestep = self.params.get("timestep",1)
            
            reader = dpsimpy.CIMReader(name)
            files = list(map(lambda x: f'{fp}/{x}',os.listdir(fp)))
            
            
            if domain_str == "SP":
                domain = dpsimpy.Domain.SP
            elif domain_str == "DP":
                domain = dpsimpy.Domain.DP
            else :
                domain = dpsimpy.Domain.EMT

            if solver_str == "MNA":
                solver = dpsimpy.Solver.MNA
            else:
                solver = dpsimpy.Solver.NRP
            
            system = reader.loadCIM(freq, files, domain, dpsimpy.PhaseType.Single, dpsimpy.GeneratorType.PVNode)
            self.sim = dpsimpy.Simulation(name)
            self.sim.set_system(system)
            self.sim.set_domain(domain)
            self.sim.set_solver(solver)
            self.sim.set_time_step(timestep)
            self.sim.set_final_time(duration)
            self.count = math.trunc(duration/timestep)
            logger = dpsimpy.Logger(name)
            for node in system.nodes:
                logger.log_attribute(node.name()+'.V', 'v', node)
            self.sim.add_logger(logger)
            self.logger.info(self.sim)
            for file in files:
                os.unlink(file)

    def start(self, payload):
        try:
            super().start(payload)
        except:
            self.logger.error('Failed to validate start parameter payload')
            self.results = None
            self.model = None
            self.change_state('error')
            return
        fp = self.download_model()
        if fp:
            self.load_cim(fp)

        try:
            self.change_state('starting')
            self.logger.info('Starting simulation...')
            self.logger.info(self.sim)
            if self.sim.start() is None:
                self.change_state('running')
                self.thread.start()
            else:
                self.change_to_error('failed to start simulation')
                self.logger.warn('Attempt to start simulator failed.'
                                 'State is %s', self._state)

        except Exception as e:
            self.logger.warn('Attempted to start non-stopped simulator.'
                             'State is %s', self._state)

    def reset(self,payload):
        try:
            self.change_state('resetting')
        except Exception as e:
            self.change_state('error')
        else:
            self.change_state('idle')
            self.sim = None
            self.current = 0
            self.thread = Thread(target=self.sim_loop)

    def stop(self):
        if self._state == 'running':
            self.logger.info('Stopping simulation...')

            if self.sim:
                if self.current < self.count:
                    self.sim.stop()
                self.change_state('stopping')
                self.sim = None
                self.current = 0
                self.upload_results()
                self.logger.warn('State changed to ' + self._state)
            else:
                self.change_state('error')
                self.logger.warn('Attempt to stop simulator failed.'
                                 'State is %s', self._state)
        else:
            self.logger.warn('Attempted to stop non-stopped simulator.'
                             'State is %s', self._state)

    def pause(self, payload):
        if self._state == 'running':
            self.logger.info('Pausing simulation...')
            self._state = 'pausing'

            try:
                if self.sim and self.sim.pause() is None:
                    self.change_state('paused')
                    self.logger.warn('State changed to ' + self._state)
                    self.thread = Thread(target=self.sim_loop)
                else:
                    self.logger.warn('Attempted to pause simulator failed.')
                    self.change_state('unknown')

            except SystemError as e:
                self.logger.warn('Attempted to pause simulator failed.'
                                 'Error is ' + str(e))
                self.change_state('unknown')

        else:
            self.logger.warn('Attempted to pause non-running simulator.'
                             'State is ' + self._state)

    def resume(self, payload):
        if self._state == 'paused':
            self.logger.info('Resuming simulation...')
            self._state = 'resuming'

            try:
                if self.sim and self.sim.start() is None:
                    self.change_state('running')
                    self.logger.warn('State changed to %s', self._state)
                else:
                    self.logger.warn('Attempted to resume simulator failed.')
                    self.change_state('unknown')

            except SystemError as e:
                self.logger.warn('Attempted to pause simulator failed. '
                                 'Error is %s', str(e))
                self.change_state('unknown')

        else:
            self.logger.warn('Attempted to resume non-paused simulator.'
                             'State is %s', self._state)
    
    
    def sim_loop(self):
        while self.current<self.count and self._state == 'running':
            self.current+=1
            self.sim.next()
        
        if self._state == 'running':
            self.stop()
        
        