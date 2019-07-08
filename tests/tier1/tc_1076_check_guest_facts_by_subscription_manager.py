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
        virt_type = {
                'libvirt-local'     :'kvm',
                'libvirt-remote'    :'kvm',
                'vdsm'              :'rhev',
                'rhevm'             :'rhev',
                'esx'               :'vmware',
                'hyperv'            :'hyperv',
                'xen'               :'xen',
                'kubevirt'          :'kvm',
                }

        # case steps
        logger.info(">>>step1: check virt.uuid fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.uuid"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        logger.info(output)
        virt_uuid = output.split(':')[1].strip()
        results.setdefault('step1', []).append(virt_uuid is not None and virt_uuid !="")

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
