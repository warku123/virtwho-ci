# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133686")
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", "True", virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info('>>>step1: Run virt-who with "onestho=True"')
        self.vw_option_enable("oneshot", virtwho_conf)
        self.vw_option_update_value("oneshot", "True", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=True)
        res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info('>>>step2: Run virt-who with "oneshot=False"')
        self.vw_option_update_value("oneshot", "False", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=False)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step2", []).append(res)

        logger.info('>>>step3: Run virt-who with "oneshot" disabled')
        self.vw_option_disable("oneshot", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=False)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step3", []).append(res)

        # case result
        self.vw_case_result(results)
