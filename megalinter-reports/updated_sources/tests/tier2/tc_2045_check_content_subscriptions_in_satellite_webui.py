# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-137101")
        hypervisor_type = self.get_config("hypervisor_type")
        register_type = self.get_config("register_type")
        if "stage" in register_type:
            self.vw_case_skip(register_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        admin_user = register_config["username"]
        admin_passwd = register_config["password"]
        server = register_config["server"]
        vdc_physical_sku = register_config["vdc"]
        vdc_virtual_sku = register_config["vdc_bonus"]
        default_org = register_config["owner"]
        api = register_config["api"]

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(
            ">>>step2: attach physical vdc for hypervisor, then check subscriptions"
        )
        physical_sku_attrs = self.system_sku_attr(
            self.ssh_host(), vdc_physical_sku, "physical"
        )
        physical_pool_id = physical_sku_attrs["pool_id"]
        self.vw_web_attach(host_name, host_uuid, physical_pool_id)
        virtual_sku_attrs = self.system_sku_attr(
            self.ssh_guest(), vdc_virtual_sku, "virtual"
        )
        virtual_pool_id = virtual_sku_attrs["pool_id"]
        katello_id = self.satellite_katello_id(
            self.ssh_host(), register_config, virtual_pool_id
        )
        default_org_id = self.satellite_org_id_get(
            self.ssh_host(), register_config, default_org
        )

        name_list = []
        if "libvirt-local" in hypervisor_type or "vdsm" in hypervisor_type:
            name_list = ["{0}".format(host_name)]
        else:
            key1 = "virt-who-{0}".format(host_name)
            key2 = "virt-who-{0}".format(host_uuid)
            name_list = [key1, key2, key1.lower(), key2.lower()]
        cmd = "curl -X GET -s -k -u {0}:{1} {2}/katello/api/organizations/{3}/subscriptions/{4}".format(
            admin_user, admin_passwd, api, default_org_id, katello_id
        )
        ret, output = self.runcmd(cmd, self.ssh_host())
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None:
            if (
                output["type"] == "STACK_DERIVED"
                and output["virt_only"] is True
                and any(key in output["hypervisor"]["name"] for key in name_list)
            ):
                logger.info("succeeded to check bonus pool coming from %s" % name_list)
                results.setdefault("step2", []).append(True)
            else:
                logger.error("failed to check bonus pool coming from %s" % name_list)
                results.setdefault("step2", []).append(False)
            if (
                output["available"] == -1
                and output["quantity"] == -1
                and output["consumed"] == 0
            ):
                logger.info(
                    "succeeded to check consumed status is '0 out of Unlimitted'"
                )
                results.setdefault("step2", []).append(True)
            else:
                logger.error("failed to check consumed status is '0 out of Unlimitted'")
                results.setdefault("step2", []).append(False)
        else:
            logger.error("failed to get subscritons info")
            results.setdefault("step2", []).append(False)

        logger.info(">>>step3: attach bonus vdc for guest, then check subscriptions")
        self.system_sku_attach(self.ssh_guest(), pool_id=virtual_pool_id)
        time.sleep(60)
        for i in range(3):
            ret, output = self.runcmd(cmd, self.ssh_host())
            output = self.is_json(output.strip())
            if ret == 0 and output is not False and output is not None:
                if (
                    output["available"] == -2
                    or output["available"] == -1
                    and output["quantity"] == -1
                    and output["consumed"] == 1
                ):
                    logger.info(
                        "succeeded to check consumed status is '1 out of Unlimitted'"
                    )
                    results.setdefault("step3", []).append(True)
                    break
                logger.warning("webui has not been refreshed, try again after 60s...")
                time.sleep(60)
        if "step3" not in results.keys():
            logger.error("failed to check consumed status")
            results.setdefault("step3", []).append(False)

        # Case Result
        self.vw_case_result(results)
