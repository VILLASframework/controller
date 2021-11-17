from villas.controller.components.managers.kubernetes import KubernetesManager
from villas.controller.components.simulators.kubernetes import KubernetesJob


class KubernetesManagerSimple(KubernetesManager):

    parameters_simple = {
        'type': 'kubernetes',
        'category': 'simulator',
        'uuid': None,
        'name': '',
        'properties': {
            'job': {
                'apiVersion': 'batch/v1',
                'kind': 'Job',
                'metadata': {
                    'name': ''
                },
                'spec': {
                    'activeDeadlineSeconds': 3600,
                    'backoffLimit': 0,
                    'template': {
                        'spec': {
                            'restartPolicy': 'Never',
                            'containers': [
                                {
                                    'image': '',
                                    'name': 'jobcontainer'
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

    def create(self, payload):
        self.logger.info(payload)
        params = payload.get('parameters', {})
        sim_name = payload.get('name', 'Kubernetes Simulator')
        jobname = params.get('jobname', 'noname')
        adls = params.get('activeDeadlineSeconds', 3600)
        image = params.get('image')
        name = params.get('name')
        uuid = params.get('uuid')

        if image is None:
            self.logger.error('No image given, will try super.create')
            super().create(payload)
            return

        parameters = self.parameters_simple
        parameters['name'] = sim_name
        job = parameters['properties']['job']
        job['metadata']['name'] = jobname
        job['spec']['activeDeadlineSeconds'] = adls
        job['spec']['template']['spec']['containers'][0]['image'] = image

        parameters['job'] = job

        if name:
            parameters['name'] = name

        if uuid:
            parameters['uuid'] = uuid

        self.logger.info(parameters)

        comp = KubernetesJob(self, **parameters)
        self.add_component(comp)

    def __init__(self, **args):
        super().__init__(**args)
