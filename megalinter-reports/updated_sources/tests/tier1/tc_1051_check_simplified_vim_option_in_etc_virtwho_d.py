# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133705")
        hypervisor_type = self.get_config("hypervisor_type")
        if "esx" not in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        host_hwuuid = self.get_hypervisor_hwuuid()

        # case steps
        logger.info(">>>step1: run virt-who with without simplified_vim option")
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(s1)

        logger.info(">>>step2: run virt-who with simplified_vim=true")
        self.vw_option_add("simplified_vim", "true", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step2", []).append(s1)

        logger.info(">>>step3: run virt-who with simplified_vim=false")
        self.vw_option_update_value("simplified_vim", "false", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step3", []).append(s1)

        # case result
        self.vw_case_result(results)
