# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-134083")
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
        register_config = self.get_register_config()
        register_type = register_config["type"]
        register_owner = register_config["owner"]
        vdc_physical_sku = register_config["vdc"]
        vdc_virtual_sku = register_config["vdc_bonus"]
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()

        # case steps
        logger.info(
            ">>>step1: stop virt-who, re-register guest again to create temporary bonus"
        )
        self.vw_thread_clean()
        self.vw_web_host_delete(host_name, host_uuid)
        self.system_unregister(self.ssh_guest())
        self.system_register(self.ssh_guest(), register_type, register_config)

        logger.info(">>>step2: check temporary bonus pool exist in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        sub_type = sku_attrs["sub_type"]
        if "Temporary" in sub_type:
            logger.info("{0}, Temporary pool is exist in guest".format(sub_type))
            results.setdefault("step2", []).append(True)
        else:
            logger.error("{0}, Temporary pool is not exist in guest".format(sub_type))
            results.setdefault("step2", []).append(False)

        logger.info(">>>step3: attach temporary bonus pool in guest")
        pool_id = sku_attrs["pool_id"]
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        res2 = self.vw_msg_search(
            output, "using a temporary unmapped guest subscription", exp_exist=True
        )
        results.setdefault("step3", []).append(res1)
        results.setdefault("step3", []).append(res2)

        # case result
        self.vw_case_result(results)
