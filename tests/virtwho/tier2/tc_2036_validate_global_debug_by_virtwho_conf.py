# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136721')
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        logger.info(">>>step: run with debug value is null in /etc/virt-who.conf")
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", '', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step', []).append(res1)
        results.setdefault('step', []).append(res2)

        # Case Result
        self.vw_case_result(results)
