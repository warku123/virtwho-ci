# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-171210")
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        vdc_virtual_sku = register_config["vdc_bonus"]

        # case steps
        logger.info(">>>step1: check virtual temporary sku exist in guest")
        self.vw_thread_clean()
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        sku_type = sku_attrs["sub_type"]
        sku_id = sku_attrs["sku_id"]
        pool_id = sku_attrs["pool_id"]
        results.setdefault("step1", []).append("Temporary" in sku_type)
        results.setdefault("step1", []).append(vdc_virtual_sku in sku_id)

        logger.info(">>>step2: attach virtual temporary sku in guest")
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        results.setdefault("step2", []).append(
            self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        )
        results.setdefault("step2", []).append(
            self.vw_msg_search(output, "Subscription Type: .*Temporary", exp_exist=True)
        )
        results.setdefault("step2", []).append(
            self.vw_msg_search(
                output,
                "Status Details: .*temporary unmapped guest subscription",
                exp_exist=True,
            )
        )

        logger.info(">>>step3: start virt-who service")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step3", []).append(res)

        logger.info(">>>step4: check temporary sku is changed to stable in guest")
        output = self.system_sku_consumed(self.ssh_guest())
        virtual_sku = ["RH00049|RH00050"]
        results.setdefault("step4", []).append(
            self.msg_validation(output, virtual_sku, exp_exist=True)
        )
        results.setdefault("step4", []).append(
            self.vw_msg_search(
                output, "Subscription Type: .*Temporary", exp_exist=False
            )
        )
        results.setdefault("step4", []).append(
            self.vw_msg_search(
                output, "Status Details: .*Subscription is current", exp_exist=True
            )
        )

        # case result
        self.vw_case_result(results)
