# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133651")
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

        # Case Step
        logger.info('>>>step1: Run virt-who with "VIRTWHO_ONE_SHOT=1"')
        self.vw_option_enable("VIRTWHO_ONE_SHOT", filename=config_file)
        self.vw_option_update_value("VIRTWHO_ONE_SHOT", "1", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=True)
        res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info('>>>step2: Run virt-who with "VIRTWHO_ONE_SHOT=0"')
        self.vw_option_update_value("VIRTWHO_ONE_SHOT", "0", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=False)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info('>>>step3: Run virt-who with "VIRTWHO_ONE_SHOT" disabled')
        self.vw_option_disable("VIRTWHO_ONE_SHOT", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=False)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/05/31 Yuefen<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
