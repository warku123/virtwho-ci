# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133661')
        self.vw_case_init()

        # case config
        results = dict()
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            config_name = "virtwho-config"
            config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
            self.vw_etc_d_mode_create(config_name, config_file)
            cmd = "virt-who"
            cmd_debug = "virt-who -d"
        else:
            cmd = self.vw_cli_base()
            cmd_debug = self.vw_cli_base() + '-d'

        # case steps
        logger.info(">>>step1: Run virt-who by cli with -d option")
        data, tty_output, rhsm_output = self.vw_start(cmd_debug, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: Run virt-who by cli without -d option")
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # case result
        self.vw_case_result(results)
