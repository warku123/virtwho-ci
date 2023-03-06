# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133705")
        hypervisor_type = self.get_config("hypervisor_type")
        if hypervisor_type in ("libvirt-local", "vdsm"):
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
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        register_type = register_config["type"]
        register_owner = register_config["owner"]
        if "esx" in hypervisor_type or "rhevm" in hypervisor_type:
            steps = {"step1": "uuid", "step2": "hostname", "step3": "hwuuid"}
        else:
            steps = {"step1": "uuid", "step2": "hostname"}

        # case steps
        for step, option in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(
                ">>>{0}: run virt-who with hypervisor_id={1}".format(step, option)
            )
            self.vw_option_add("hypervisor_id", option, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
                hypervisor_display = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
                hypervisor_display = host_name
            else:
                hypervisorId = host_uuid
                hypervisor_display = host_uuid
            if hypervisorId in data[register_owner].keys():
                logger.info("Succeeded to search hypervisorId:{0}".format(hypervisorId))
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to search hypervisorId:{0}".format(hypervisorId))
                results.setdefault(step, []).append(False)
            if "satellite" in register_type:
                host_display = self.satellite_hosts_get(
                    self.ssh_host(),
                    register_config,
                    host_name,
                    host_uuid,
                    host_hwuuid,
                    desc="get host display name",
                )
                host_display_name = host_display["name"]
            else:
                hypervisor_display = host_name
                host_display = self.stage_consumer_get(
                    self.ssh_host(), register_config, host_name, host_uuid
                )
                host_display_name = host_display["name"]
            if hypervisor_display or hypervisor_display.lower() in host_display_name:
                logger.info(
                    "Succeeded to search hypervisorDisplay:{0}".format(
                        hypervisor_display
                    )
                )
                results.setdefault(step, []).append(True)
            else:
                logger.error(
                    "Failed to search hypervisorDisplay:{0}".format(hypervisor_display)
                )
                results.setdefault(step, []).append(False)
            self.vw_option_del("hypervisor_id", filename=config_file)
            self.vw_web_host_delete(host_name, hypervisorId)
        if "stage" in register_type:
            self.stage_consumer_clean(self.ssh_host(), register_config)

        # case result
        self.vw_case_result(results)
