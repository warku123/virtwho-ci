# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133746")
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: restart virt-who service, check status and thread")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "start")
        thread_num = self.vw_callback_thread_num()
        results.setdefault("step1", []).append(thread_num == 1)
        results.setdefault("step1", []).append(self.vw_service_status() == "running")
        logger.info("virt-who thread number is: {0}".format(thread_num))

        logger.info(
            ">>>step2: restart rhsmcertd service , check virt-who status and thread"
        )
        ret, output = self.run_service(self.ssh_host(), "rhsmcertd", "restart")
        thread_num = self.vw_callback_thread_num()
        results.setdefault("step2", []).append(thread_num == 1)
        results.setdefault("step2", []).append(self.vw_service_status() == "running")
        logger.info("virt-who thread number is: {0}".format(thread_num))

        logger.info(
            ">>>step3: restart virt-who service again , check virt-who status and thread"
        )
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step3", []).append(res)

        # case result
        self.vw_case_result(results)
