# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133660')
        trigger_type = self.get_config('trigger_type')
        hypervisor_type = self.get_config('hypervisor_type')
        if trigger_type in ('trigger-rhev', 'trigger-brew', 'trigger-multiarch'):
            self.vw_case_skip(trigger_type)
        pkg_info = self.pkg_info(self.ssh_host(), 'virt-who')
        if "none" in pkg_info.get("Signature"):
            self.vw_case_skip('Scratch Build')
        self.vw_case_init()

        # case config
        results = dict()
        self.pkg_uninstall(self.ssh_host(), 'virt-who')
        self.pkg_install(self.ssh_host(), 'virt-who')
        steps = {'step1':'service', 'step2':'cli'}

        # case steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who {1} by default".format(step, option))
            if option == "service":
                data, tty_output, rhsm_output = self.vw_start()
            else:
                data, tty_output, rhsm_output = self.vw_start(cli="virt-who")
            if hypervisor_type in ('libvirt-local', 'vdsm'):
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=False)
            else:
                res1 = self.op_normal_value(data, exp_error=2, exp_thread=1, exp_send=0)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=True)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # case result
        self.vw_case_result(results)
