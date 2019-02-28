# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134061")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virt_type = {
                'libvirt-local'     :'kvm',
                'libvirt-remote'    :'kvm',
                'vdsm'              :'ovirt',
                'rhevm'             :'ovirt',
                'esx'               :'vmware',
                'hyperv'            :'hyperv',
                'xen'               :'xen',
                }

        # Case Steps
        logger.info(">>>step1: check virt.uuid fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.uuid"
        ret, output = self.runcmd(cmd, self.ssh_guest(), desc="check virt.uuid")
        logger.info(output)
        virt_uuid = output.split(':')[1].strip()
        results.setdefault('step1', []).append(virt_uuid is not None and virt_uuid !="")

        logger.info(">>>step2: check virt.host_type fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.host_type"
        ret, output = self.runcmd(cmd, self.ssh_guest(), desc="check virt.uuid")
        logger.info(output)
        virt_host_type = output.split(':')[1].strip()
        results.setdefault('step2', []).append(virt_type[mode.lower()] in virt_host_type)

        logger.info(">>>step3: check virt.is_guest fact by subscription-manager in guest")
        cmd = "subscription-manager facts --list | grep virt.is_guest"
        ret, output = self.runcmd(cmd, self.ssh_guest(), desc="check virt.uuid")
        logger.info(output)
        virt_is_guest = output.split(':')[1].strip()
        results.setdefault('step3', []).append(virt_is_guest == "True")

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
