from villas.controller.components.managers.kubernetes import KubernetesManager
from villas.controller.components.simulators.kubernetes import KubernetesJob


class KubernetesManagerSimple(KubernetesManager):

    create_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'title': 'Simple Kubernetes Job',
        'type': 'object',
        'required': [
            'image',
        ],
        'properties': {
            'uuid': {
                'type': 'string',
                'title': 'UUID',
                'default': '8dfd03b2-1c78-11ec-9621-0242ac130002'
            },
            'jobname': {
                'type': 'string',
                'title': 'Job name',
                'default': 'myJob'
            },
            'activeDeadlineSeconds': {
                'type': 'number',
                'title': 'activeDeadlineSeconds',
                'default': 3600
            },
            'image': {
                'type': 'string',
                'title': 'Image',
                'default': 'perl'
            },
            'containername': {
                'type': 'string',
                'title': 'Container name',
                'default': 'myContainer'
            }
        }
    }

    parameters_simple = {
        'type': 'kubernetes',
        'category': 'simulator',
        'uuid': None,
        'name': 'Kubernetes Simulator',
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
                                    'name': ''
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

    def create(self, message):
        print(message.payload)
        params = message.payload.get('parameters', {})
        jobname = params.get('jobname', 'noname')
        adls = params.get('activeDeadlineSeconds', 3600)
        contName = params.get('containername', 'noname')
        image = params.get('image')
        name = params.get('name')
        uuid = params.get('uuid')

        if image is None:
            self.logger.error('No image given, will try super.create')
            super().create(message)
            return

        parameters = self.parameters_simple
        job = parameters['properties']['job']
        job['metadata']['name'] = jobname
        job['spec']['activeDeadlineSeconds'] = adls
        job['spec']['template']['spec']['containers'][0]['name'] = contName
        job['spec']['template']['spec']['containers'][0]['image'] = image

        parameters['job'] = job

        if name:
            parameters['name'] = name

        if uuid:
            parameters['uuid'] = uuid

        print(parameters)

        comp = KubernetesJob(self, **parameters)
        self.add_component(comp)

    def __init__(self, **args):
        super().__init__(**args)
