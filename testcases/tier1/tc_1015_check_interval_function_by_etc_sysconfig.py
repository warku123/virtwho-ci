# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133655")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        option_tested = "VIRTWHO_INTERVAL"
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)

        # Case Steps
        logger.info(">>>step1: disable VIRTWHO_INTERVAL option")
        self.vw_option_disable(option_tested, filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: enable VIRTWHO_INTERVAL and set to 10")
        self.vw_option_enable(option_tested, filename=config_file)
        self.vw_option_update_value(option_tested, '10', filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: enable VIRTWHO_INTERVAL and set to 60")
        self.vw_option_enable(option_tested, filename=config_file)
        self.vw_option_update_value(option_tested, '60', filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step4: enable VIRTWHO_INTERVAL and set to 120")
        self.vw_option_enable(option_tested, filename=config_file)
        self.vw_option_update_value(option_tested, '120', filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120, exp_loopnum=1, exp_looptime=120)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/05/21 Eko<hsun@redhat.com>
#- Case created to validate owner option
