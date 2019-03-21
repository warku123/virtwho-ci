# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133662')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()

        # Case Steps
        logger.info('>>>step1: Run virt-who with "VIRTWHO_DEBUG=1"')
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info('>>>step2: Run virt-who with "VIRTWHO_DEBUG=0"')
        self.vw_option_update_value("VIRTWHO_DEBUG", "0", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info('>>>step3: Run virt-who with "VIRTWHO_DEBUG" disabled')
        self.vw_option_disable("VIRTWHO_DEBUG", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        # Case Result
        self.vw_case_result(results)
