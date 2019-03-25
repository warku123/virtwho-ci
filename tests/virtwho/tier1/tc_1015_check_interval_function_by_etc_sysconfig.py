# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133655')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        option_tested = "VIRTWHO_INTERVAL"
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)

        # case steps
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

        # case result
        self.vw_case_result(results)
