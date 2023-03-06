# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-174862")
        configs = self.get_hypervisor_config()
        if self.pkg_check(self.ssh_host(), "virt-who")[9:15] < "0.24.6":
            self.vw_case_skip("virt-who version")
        hypervisor_type = configs["type"]
        if hypervisor_type in ("libvirt-local", "vdsm"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_option_add("hypervisor_id", "uuid", config_file)
        register_config = self.get_register_config()
        register_owner = register_config["owner"]
        host_uuid = self.get_hypervisor_hostuuid()
        facts_items = ["socket", "type", "dmi", "version"]
        if hypervisor_type in ("esx", "rhevm", "ahv"):
            facts_items.append("cluster")
        type_values = {
            "kubevirt": "qemu",
            "xen": "XenServer",
            "hyperv": "hyperv",
            "esx": "VMware ESXi",
            "libvirt-remote": "QEMU",
            "rhevm": "qemu",
            "ahv": "AHV",
        }
        if hypervisor_type == "ahv" and deploy.ahv.api_version == "v2":
            type_values["ahv"] = "kKvm"

        cluster_values = {
            "esx": deploy.vcenter.cluster,
            "rhevm": deploy.rhevm.cluster,
            "ahv": deploy.ahv.cluster,
        }

        # Case Steps
        logger.info(">>>step1: run virt-who to get facts from mapping")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res1)
        if host_uuid in data[register_owner].keys():
            facts_dic = data[register_owner][host_uuid]
            logger.info("succeeded to get hypervisor facts dict: {0}".format(facts_dic))
            results.setdefault("step1", []).append(True)
        else:
            raise FailException("failed to get hypervisor facts")

        logger.info(">>>step2: check all facts item exiting")
        for item in facts_items:
            if item in facts_dic.keys() and facts_dic[item] is not None:
                logger.info(
                    "succeeded to check {0}={1} in {2} facts".format(
                        item, facts_dic[item], hypervisor_type
                    )
                )
                results.setdefault("step2", []).append(True)
            else:
                logger.error("no '{0}' in {1} facts".format(item, hypervisor_type))
                results.setdefault("step2", []).append(False)

        logger.info(">>>step3: check hypervisor.type value")
        type_value = type_values[hypervisor_type]
        if facts_dic["type"] == type_value:
            logger.info("succeeded to check hypervisor.type={0}".format(type_value))
            results.setdefault("step3", []).append(True)
        else:
            logger.error("hypervisor.type is not {0}".format(type_value))
            results.setdefault("step3", []).append(False)

        logger.info(">>>step4: check dmi.system.uuid value")
        if hypervisor_type == "rhevm":
            host_hwuuid = self.get_hypervisor_hwuuid()
            dmi = host_hwuuid
        else:
            dmi = host_uuid
        if facts_dic["dmi"] == dmi:
            logger.info("succeeded to check dmi.system.uuid={0}".format(host_uuid))
            results.setdefault("step4", []).append(True)
        else:
            logger.error("dmi.system.uuid is not {0}".format(host_uuid))
            results.setdefault("step4", []).append(False)

        if hypervisor_type in ("esx", "rhevm", "ahv"):
            logger.info(">>>step5: check hypervisor.cluster value")
            cluster_value = cluster_values[hypervisor_type]
            if facts_dic["cluster"] == cluster_value:
                logger.info(
                    "succeeded to check hypervisor.cluster={0}".format(cluster_value)
                )
                results.setdefault("step5", []).append(True)
            else:
                logger.error("hypervisor.cluster is not {0}".format(cluster_value))
                results.setdefault("step5", []).append(False)

        # Case Result
        self.vw_case_result(results)
