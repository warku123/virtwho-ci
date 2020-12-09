# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133662')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '1.31.0':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        sysconf_file = "/etc/sysconfig/virt-who"
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info('>>>step1: Run virt-who with "VIRTWHO_DEBUG=1"')
        self.vw_option_enable("VIRTWHO_DEBUG", filename=sysconf_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=sysconf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info('>>>step2: Run virt-who with "VIRTWHO_DEBUG=0"')
        self.vw_option_update_value("VIRTWHO_DEBUG", "0", filename=sysconf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info('>>>step3: Run virt-who with "VIRTWHO_DEBUG" disabled')
        self.vw_option_disable("VIRTWHO_DEBUG", filename=sysconf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        # case result
        self.vw_case_result(results)
