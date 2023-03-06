# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-134055")
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
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        register_config = self.get_register_config()
        register_type = register_config["type"]
        vdc_physical_sku = register_config["vdc"]
        vdc_virtual_sku = register_config["vdc_bonus"]

        # case steps
        logger.info(">>>step1: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        physical_pool_id = sku_attrs["pool_id"]
        self.vw_web_attach(host_name, host_uuid, physical_pool_id)

        logger.info(">>>step3: attach virtual sku by pool_id in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        virtual_pool_id = sku_attrs["pool_id"]
        self.system_sku_attach(self.ssh_guest(), pool_id=virtual_pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault("step3", []).append(res)

        logger.info(">>>step4: check repo status in host")
        hypervisor_type = self.get_config("hypervisor_type")
        if "libvirt-local" in hypervisor_type or "vdsm" in hypervisor_type:
            cmd = "subscription-manager repos --list"
            ret, output = self.runcmd(cmd, self.ssh_host())
            res = self.vw_msg_search(
                output, "no repositories available", exp_exist=True
            )
            results.setdefault("step4", []).append(res)
        else:
            logger.warning(
                "skip this step, it's not available for mode {0}".format(
                    hypervisor_type
                )
            )

        logger.info(">>>step5: check repo status in guest")
        cmd = "subscription-manager repos --list"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        if "stage" in register_type:
            res = self.vw_msg_search(output, "Available Repositories", exp_exist=True)
        else:
            res = self.vw_msg_search(
                output, "no repositories available", exp_exist=True
            )
        results.setdefault("step5", []).append(res)

        logger.info(">>>step6: check subscription status in guest")
        cmd = "subscription-manager status"
        ret, output = self.runcmd(cmd, self.ssh_guest())
        res1 = self.vw_msg_search(output, "Overall Status: Current", exp_exist=True)
        res2 = self.vw_msg_search(output, "Invalid", exp_exist=False)
        results.setdefault("step6", []).append(res1)
        results.setdefault("step6", []).append(res2)

        # case result
        self.vw_case_result(results)
