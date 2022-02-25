# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134061')
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()
        virt_type = {
                'libvirt-local'     :'kvm',
                'libvirt-remote'    :'kvm',
                'vdsm'              :'rhev',
                'rhevm'             :'rhev',
                'esx'               :'vmware',
                'hyperv'            :'hyperv',
                'xen'               :'xen',
                'kubevirt'          :'kvm',
                'ahv'               :'kvm'
                }

        # case steps
        logger.info(">>>step1: check virt.uuid fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.uuid"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        logger.info(output)
        virt_uuid = output.split(':')[1].strip()
        results.setdefault('step1', []).append(virt_uuid.lower() == guest_uuid.lower())

        logger.info(">>>step2: check virt.host_type fact by subscription-manager in guest")
        hypervisor_type = self.get_config('hypervisor_type')
        cmd = "subscription-manager facts --list | grep virt.host_type"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        logger.info(output)
        virt_host_type = output.split(':')[1].strip()
        results.setdefault('step2', []).append(virt_type[hypervisor_type.lower()] in virt_host_type)

        logger.info(">>>step3: check virt.is_guest fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.is_guest"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        logger.info(output)
        virt_is_guest = output.split(':')[1].strip()
        results.setdefault('step3', []).append(virt_is_guest == "True")

        # case result
        self.vw_case_result(results)
