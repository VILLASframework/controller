from villas.controller.components.managers.kubernetes import KubernetesManager
from villas.controller.components.simulators.kubernetes import KubernetesJob

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
                'backoffLimit': 2,
                'template': {
                    'spec': {
                        'restartPolicy': 'Never',
                        'containers': [
                            {
                                'image': '',
                                'imagePullPolicy': 'Always',
                                'name': 'jobcontainer',
                                'securityContext': {
                                    'privileged': True
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
}


class KubernetesManagerSimple(KubernetesManager):

    def __init__(self, **args):
        super().__init__(**args)

    def create(self, payload):
        params = payload.get('parameters', {})
        sim_name = payload.get('name', 'Kubernetes Simulator')
        jobname = params.get('jobname', 'noname')
        adls = params.get('activeDeadlineSeconds', 3600)
        if type(adls) is str:
            adls = int(adls)
        image = params.get('image')
        name = params.get('name')
        uuid = params.get('uuid')
        self.logger.info('uuid:')
        self.logger.info(uuid)

        if image is None:
            self.logger.error('No image given, will try super.create')
            super().create(payload)
            return

        parameters = parameters_simple
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

        comp = KubernetesJob(self, **parameters)
        self.add_component(comp)
