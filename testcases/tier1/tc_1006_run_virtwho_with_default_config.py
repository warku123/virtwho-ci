# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133660")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        trigger_name = self.get_exported_param("TRIGGER_NAME")
        if "trigger-rhev" in trigger_name:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % trigger_name)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        self.vw_pkg_uninstall()
        self.vw_pkg_install()
        steps = {'step1':'service', 'step2':'cli'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who %s by default" % (step, option))
            if option == "service":
                data, tty_output, rhsm_output = self.vw_start()
            else:
                data, tty_output, rhsm_output = self.vw_start(cli="virt-who")
            if "libvirt-local" in mode or "vdsm" in mode:
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=False)
            else:
                res1 = self.op_normal_value(data, exp_error=2, exp_thread=1, exp_send=0)
                res2 = self.vw_msg_search(rhsm_output, 'Error in libvirt backend', exp_exist=True)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == '__main__':
    unittest.main()

# ===changelog===
# - 2018/06/01 <shyan@redhat.com>
# - Case created and support to run against rhel6/7/8
