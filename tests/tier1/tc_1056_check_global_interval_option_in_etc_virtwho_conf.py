# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133685")
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
        logger.info(">>>step1: enable interval and set to 10 in /etc/virt-who.conf")
        self.vw_option_enable("interval", virtwho_conf)
        self.vw_option_update_value("interval", "10", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(
            data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600
        )
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: enable interval and set to 60 in /etc/virt-who.conf")
        self.vw_option_update_value("interval", "60", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(
            data,
            exp_error=0,
            exp_thread=1,
            exp_send=1,
            exp_interval=60,
            exp_loopnum=1,
            exp_looptime=60,
        )
        results.setdefault("step2", []).append(res)

        logger.info(">>>step3: enable interval and set to 120 in /etc/virt-who.conf")
        self.vw_option_update_value("interval", "120", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(
            data,
            exp_error=0,
            exp_thread=1,
            exp_send=1,
            exp_interval=120,
            exp_loopnum=1,
            exp_looptime=120,
        )
        results.setdefault("step3", []).append(res)

        # case result
        self.vw_case_result(results)
