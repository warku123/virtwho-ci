# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-134060")
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
        vdc_physical_sku = register_config["vdc"]
        vdc_virtual_sku = register_config["vdc_bonus"]

        # case steps
        logger.info(">>>step1: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        pool_id = sku_attrs["pool_id"]
        self.vw_web_attach(host_name, host_uuid, pool_id)

        logger.info(">>>step3: attach virtual sku by pool_id in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        pool_id = sku_attrs["pool_id"]
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault("step3", []).append(res)

        logger.info(">>>step4: no available virtual vdc sku listed in guest ")
        output = self.system_sku_attr(
            self.ssh_guest(), vdc_virtual_sku, "virtual", exp_exist=False
        )
        res = self.vw_msg_search(str(output), vdc_virtual_sku, exp_exist=False)
        results.setdefault("step4", []).append(res)

        # case result
        notes = list()
        server_type = self.get_config("register_type")
        if "stage" in server_type:
            notes.append(
                "Bug(Step*): Failed to synchronize cache for repo 'rhel-8-for-x86_64-baseos-rpms'"
            )
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1719177")
        self.vw_case_result(results, notes)
