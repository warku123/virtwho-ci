# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: run virt-who by default
        :Polarion_Id: RHEL-133660
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        trigger_type = config.virtwho.trigger_type
        hypervisor_type = config.hypervisor.type
        if "trigger-rhev" in trigger_type:
            self.vw_case_skip("skipped - this case is not avaialbe for {0}".format(trigger_type))
        self.vw_case_init()

        # Case Config
        results = dict()
        self.pkg_uninstall(self.ssh_host(), 'virt-who')
        self.pkg_install(self.ssh_host(), 'virt-who')
        steps = {'step1':'service', 'step2':'cli'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who {1} by default".format(step, option))
            if option == "service":
                data, tty_output, rhsm_output = self.vw_start()
            else:
                data, tty_output, rhsm_output = self.vw_start(cli="virt-who")
            if "libvirt-local" in hypervisor_type or "vdsm" in hypervisor_type:
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=False)
            else:
                res1 = self.op_normal_value(data, exp_error=2, exp_thread=1, exp_send=0)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=True)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # Case Result
        self.vw_case_result(results)
