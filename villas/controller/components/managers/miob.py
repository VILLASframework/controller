import psutil
import usb.core

from villas.controller.components.managers.generic import GenericManager


class MiobManager(GenericManager):

    @property
    def usb_devices(self):
        devs = []
        for cfg in usb.core.find(find_all=True):
            dev = {
                'vendor_id': cfg.idVendor,
                'product_id': cfg.idProduct,
            }

            m = {
                'product': cfg.iProduct,
                'serial_no': cfg.iSerialNumber,
                'manufacturer': cfg.iManufacturer
            }

            for k, v in m.items():
                try:
                    dev[k] = usb.util.get_string(cfg, v)
                except ValueError:
                    pass

            devs.append(dev)

        return devs

    @property
    def status(self):
        disks = [p._asdict() for p in psutil.disk_partitions()]
        for d in disks:
            try:
                d['usage'] = psutil.disk_usage(d['mountpoint'])._asdict()
            except Exception:
                pass

        nic_addrs = psutil.net_if_addrs()
        nic_stats = psutil.net_if_stats()
        nics = {}
        for name, ctr in psutil.net_io_counters(pernic=True).items():
            nics[name] = ctr._asdict()

            nics[name]['statistics'] = nic_stats[name]._asdict()
            nics[name]['addresses'] = [a._asdict() for a in nic_addrs[name]]

        usb = self.usb_devices
        freq = psutil.cpu_freq()

        s = {
            'cpu': {
                'physical_cores': psutil.cpu_count(logical=False),
                'usage': psutil.cpu_percent(interval=1, percpu=True),
                'loadavg': psutil.getloadavg(),
                'frequency': freq._asdict() if freq else {}
            },
            'memory': psutil.virtual_memory()._asdict(),
            'swap': psutil.swap_memory()._asdict(),
            'users': [u._asdict() for u in psutil.users()],
            'disks': disks,
            'nics': nics,
            'sensors': {
                'fans': {name: [fan._asdict() for fan in fans]
                         for name, fans in psutil.sensors_fans().items()},
                'temperatures': {name: [temp._asdict() for temp in temps]
                                 for name, temps in
                                 psutil.sensors_temperatures().items()}
            },
            'boottime': psutil.boot_time(),
            'processes': len(psutil.pids()),
            'usb': usb,
            'fpga': {
                'jtag_available': len([d for d in usb
                                       if d['vendor_id'] == 0x0403
                                       and d['product_id'] == 0x6014]) > 0
            }
        }

        status = super().status
        status['status'].update(s)

        return status
