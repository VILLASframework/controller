from villas.controller.components.managers.kubernetes import KubernetesManager
from villas.controller.components.simulators.kubernetes import KubernetesJob


def build_parameters(sim_name, jobname, image, adls=3600, privileged=False, name=None, uuid=None):
    parameters = {
        'type': 'kubernetes',
        'category': 'simulator',
        'uuid': uuid,
        'name': name or sim_name,
        'properties': {
            'job': {
                'apiVersion': 'batch/v1',
                'kind': 'Job',
                'metadata': {
                    'name': jobname
                },
                'spec': {
                    'activeDeadlineSeconds': adls,
                    'backoffLimit': 2,
                    'template': {
                        'spec': {
                            'restartPolicy': 'Never',
                            'containers': [
                                {
                                    'image': image,
                                    'imagePullPolicy': 'Always',
                                    'name': 'jobcontainer',
                                    'securityContext': {
                                        'privileged': privileged
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
    return parameters

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
        privileged = params.get('privileged', False)
        uuid = params.get('uuid')
        self.logger.info('uuid:')
        self.logger.info(uuid)

        if image is None:
            self.logger.error('No image given, will try super.create')
            super().create(payload)
            return

        parameters = build_parameters(
            sim_name=sim_name,
            jobname=jobname,
            image=image,
            adls=adls,
            privileged=privileged,
            name=name,
            uuid=uuid
        )

        comp = KubernetesJob(self, **parameters)
        self.add_component(comp)
