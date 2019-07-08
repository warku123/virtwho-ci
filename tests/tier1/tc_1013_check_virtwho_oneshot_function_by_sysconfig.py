# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133651')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()        

        # case steps
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

        # case result
        self.vw_case_result(results)
