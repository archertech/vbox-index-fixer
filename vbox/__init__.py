
import json
import os
import re
import subprocess

PATH_TO_VBOXMANAGE = os.environ.get('VBOXMANAGE_PATH', '/usr/local/bin/VBoxManage')

class VBoxCommandException(Exception):
    pass

class VBoxMachineListException(VBoxCommandException):
    pass

class VBoxMetadataException(VBoxCommandException):
    pass

class VBoxParameterException(VBoxCommandException):
    pass


class VirtualBox(object):

    not_set_value = '<not set>'
    none_value = 'none'
    true_value = 'on'
    false_value = 'off'

    def destroy(self, vm_uuid):
        if not vm_uuid:
            raise VBoxParameterException('You must specify a VM\'s UUID to destroy it')

        self.shutdown(vm_uuid)
        self._vbox_cmd(['unregistervm', '--delete', vm_uuid])

    def shutdown(self, vm_uuid):
        if not vm_uuid:
            raise VBoxParameterException('You must specify a VM\'s UUID to shut it down')

        self._vbox_cmd(['controlvm', vm_uuid, 'poweroff'])

    def suspended(self, with_meta=True):
        return self._vm_list(with_meta=with_meta, state='suspend')

    def poweredoff(self, with_meta=True):
        return self._vm_list(with_meta=with_meta, state='poweroff')

    def running(self, with_meta=True):
        return self._vm_list(with_meta=with_meta, state='running')

    def machines(self, with_meta=True):
        return self._vm_list(with_meta=with_meta)

    def _vm_list(self, with_meta=False, state=None):
        vms = {}
        for vm in iter(self._vbox_cmd(['list', 'vms']).readline, ''):
            m = re.match(r'^"(.*)" {(.*)}$', vm)
            if m:
                if with_meta or state:
                    meta = self.meta(m.group(1))
                    if state and meta.state != state:
                        continue
                    if with_meta:
                        vms.update({m.group(1): meta})
                    else:
                        vms.update({m.group(1): m.group(2)})
                else:
                    vms.update({m.group(1): m.group(2)})
            else:
                raise VBoxMachineListException('VBoxManage output didn\'t match: {}'.format(vm))

        return vms


    def _vbox_cmd(self, command):
        real_command = [PATH_TO_VBOXMANAGE]
        if isinstance(command, list):
            for piece in command:
                real_command.append(piece)
        else:
            real_command.append(command)
        process = subprocess.Popen(real_command, stdout=subprocess.PIPE)
        return process.stdout


    def meta(self, machine_id_or_name):
        meta = {}
        for var in iter(self._vbox_cmd(['showvminfo', '{}'.format(machine_id_or_name), '--machinereadable']).readline, ''):
            m = re.match(r'^"?(.*)"?="?(.*?)"?$', var)
            if m:
                key = m.group(1)
                value = m.group(2)
                if value == self.none_value or value == self.not_set_value:
                    value = None
                elif value == self.true_value:
                    value = True
                elif value == self.false_value:
                    value = False
                meta.update({key: value})
            else:
                raise VBoxMetadataException('VBoxManage output didn\'t match: {}'.format(var))

        return VBoxMachineMetadata(meta)


class VBoxMachineMetadata(VirtualBox):
    boolean_keys = [
        'pagefusion',
        'hpet',
        'pae',
        'longmode',
        'triplefaultreset',
        'apic',
        'x2apic',
        'rtcuseutc',
        'hwvirtex',
        'nestedpaging',
        'largepages',
        'vtxvpid',
        'vtxux',
        'accelerate3d',
        'accelerate2dvideo',
        'teleporterenabled',
        'tracing-enabled',
        'tracing-allow-vm-access',
        'autostart-enabled',
        'cableconnected1',
        'cableconnected2',
        'cableconnected3',
        'cableconnected4',
        'cableconnected5',
        'cableconnected6',
        'cableconnected7',
        'cableconnected8',
        'uart1',
        'uart2',
        'uart3',
        'uart4',
        'lpt1',
        'lpt2',
        'vrde',
        'usb',
        'ehci',
        'xhci',
        'vcpenabled'
    ]


    def __init__(self, metadata):
        self.net = {}
        for num in [1, 2, 3, 4, 5, 6, 7, 8]:
            ifacedata = {}
            if 'nic{}'.format(num) in metadata and metadata['nic{}'.format(num)]:
                ifacedata = {
                    'type': metadata['nic{}'.format(num)],
                    'connected': metadata['cableconnected{}'.format(num)],
                    'model': metadata['nictype{}'.format(num)],
                    'speed': metadata['nicspeed{}'.format(num)],
                    'mac': metadata['macaddress{}'.format(num)],
                }
            self.net.update({(num - 1): ifacedata})

        self.name = metadata['name']
        self.groups = metadata['groups']
        self.ostype = metadata['ostype']
        self.uuid = metadata['UUID']

        self.config_file = metadata['CfgFile']
        self.snapshot_folder = metadata['SnapFldr']
        self.log_folders = metadata['LogFldr']

        self.hardwareuuid = metadata['hardwareuuid']
        self.memory = metadata['memory']
        self.pagefusion = metadata['pagefusion']
        self.vram = metadata['vram']
        self.cpuexecutioncap = metadata['cpuexecutioncap']
        self.hpet = metadata['hpet']
        self.chipset = metadata['chipset']
        self.firmware = metadata['firmware']
        self.cpus = metadata['cpus']
        self.pae = metadata['pae']
        self.longmode = metadata['longmode']
        self.triplefaultreset = metadata['triplefaultreset']
        self.apic = metadata['apic']
        self.x2apic = metadata['x2apic']
        self.cpuid_portability_level = metadata['cpuid-portability-level']

        self.boot = {
            'menu': metadata['bootmenu'],
            'devices': {
                '0': metadata['boot1'],
                '1': metadata['boot2'],
                '2': metadata['boot3'],
                '3': metadata['boot4']
            }
        }

        self.acpi = metadata['acpi']
        self.ioapic = metadata['ioapic']
        self.biosapic = metadata['biosapic']
        self.biossystemtimeoffset = metadata['biossystemtimeoffset']
        self.rtcuseutc = metadata['rtcuseutc']
        self.hwvirtex = metadata['hwvirtex']
        self.nestedpaging = metadata['nestedpaging']
        self.largepages = metadata['largepages']
        self.vtxvpid = metadata['vtxvpid']
        self.vtxux = metadata['vtxux']
        self.paravirtprovider = metadata['paravirtprovider']
        self.effparavirtprovider = metadata['effparavirtprovider']
        self.state = metadata['VMState']
        self.state_change_time = metadata['VMStateChangeTime']
        self.monitorcount = metadata['monitorcount']
        self.accelerate3d = metadata['accelerate3d']
        self.accelerate2dvideo = metadata['accelerate2dvideo']

        self.teleporter = {
            'enabled': metadata['teleporterenabled'],
            'port': metadata['teleporterport'],
            'address': metadata['teleporteraddress'],
            'password': metadata['teleporterpassword']
        }

        self.tracing = {
            'enabled': metadata['tracing-enabled'],
            'allow-vm-access': metadata['tracing-allow-vm-access'],
            'config': metadata['tracing-config']
        }

        self.autostart = {
            'enabled': metadata['autostart-enabled'],
            'delay': metadata['autostart-delay']
        }

        self.controllers = {}
        for num in [0, 1, 2, 3, 4]:
            if 'storagecontrollername{}'.format(num) in metadata:
                controller = {
                    'name': metadata['storagecontrollername0'],
                    'type': metadata['storagecontrollertype0'],
                    'instance': metadata['storagecontrollerinstance0'],
                    'maxports': metadata['storagecontrollermaxportcount0'],
                    'ports': metadata['storagecontrollerportcount0'],
                    'bootable': metadata['storagecontrollerbootable0'],
                    'devices': {}
                }
                for dev in [0, 1, 2, 3, 4, 5, 6, 7]:
                    if 'IDE Controller-{}-{}'.format(num, dev) in metadata:
                        controller['devices'].update({dev: {
                            'vmdk': metadata['IDE Controller-{}-{}'.format(num, dev)],
                            'uuid': metadata['IDE Controller-ImageUUID-{}-{}'.format(num, dev)]
                        }})
                self.controllers.update({num: controller})

        self.defaultfrontend = metadata['defaultfrontend']
        self.mtu = metadata['mtu']
        self.sockSnd = metadata['sockSnd']
        self.sockRcv = metadata['sockRcv']
        self.tcpWndSnd = metadata['tcpWndSnd']
        self.tcpWndRcv = metadata['tcpWndRcv']

        self.forwarding = {}
        for num in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if 'Forwarding({})'.format(num) in metadata:
                pieces = metadata['Forwarding({})'.format(num)].split(',')
                self.forwarding.update({num: {
                    'type': pieces[0],
                    'protocol': pieces[1],
                    'host_ip': pieces[2],
                    'host_port': pieces[3],
                    'guest_ip': pieces[4],
                    'guest_port': pieces[5]
                }})

        self.hidpointing = metadata['hidpointing']
        self.hidkeyboard = metadata['hidkeyboard']
        self.audio = metadata['audio']
        self.clipboard = metadata['clipboard']
        self.draganddrop = metadata['draganddrop']
        self.vrde = metadata['vrde']
        self.usb = metadata['usb']
        self.ehci = metadata['ehci']
        self.xhci = metadata['xhci']
        self.guest_memory_balloon = metadata['GuestMemoryBalloon']

        self.uart = {
            '0': metadata['uart1'],
            '1': metadata['uart2'],
            '2': metadata['uart3'],
            '4': metadata['uart4']
        }
        self.lpt = {
            '0': metadata['lpt1'],
            '1': metadata['lpt2']
        }

        # Only checking to 8, because really, if you have more than a couple shared folders
        # you're probably better off sharing _one_ higher level folder
        self.shared_folders = {}
        for num in [1, 2, 3, 4, 5, 6, 7, 8]:
            if 'SharedFolderNameMachineMapping{}'.format(num) in metadata:
                self.shared_folders.update({
                    (num-1): {
                        'guest_path': metadata['SharedFolderNameMachineMapping{}'.format(num)],
                        'host_path': metadata['SharedFolderPathMachineMapping{}'.format(num)]
                    }
                })

        self.vcp = {
            'enabled': metadata['vcpenabled'],
            'screens': metadata['vcpscreens'],
            'file': metadata['vcpfile'],
            'width': metadata['vcpwidth'],
            'height': metadata['vcpheight'],
            'rate': metadata['vcprate'],
            'fps': metadata['vcpfps']
        }
