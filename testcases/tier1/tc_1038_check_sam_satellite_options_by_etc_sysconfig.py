# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133701")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)
        steps = {'step1':'VIRTWHO_SAM', 'step2':'VIRTWHO_SATELLITE6'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s" % (step, option))
            self.vw_option_enable(option, filename=config_file)
            self.vw_option_update_value(option, '1', filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            self.vw_option_disable(option, filename=config_file)

        # Case Result
        notes = list()
        notes.append("This case will be deprecated as bug https://bugzilla.redhat.com/show_bug.cgi?id=1368341")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/11 Eko<hsun@redhat.com>
#- Case created to validate sam/satellite options
