# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133745")
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info(">>>step1: config mode, check report send and no error msg ")
        self.vw_etc_d_mode_create(config_name, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: check guest attributes by curl")
        register_config = self.get_register_config()
        register_type = register_config["type"]
        username = register_config["username"]
        password = register_config["password"]
        owner = register_config["owner"]
        api = register_config["api"]
        if "stage" in register_type:
            registered_id = self.stage_consumer_uuid(
                self.ssh_host(), register_config, host_name, host_uuid
            )
            cmd = "curl -s -k -u {0}:{1} {2}/consumers/{3}/guestids/{4}".format(
                username, password, api, registered_id, guest_uuid
            )
            ret, output = self.runcmd(cmd, self.ssh_host())
            if guest_uuid in output and "guestId" in output and "attributes" in output:
                logger.info("Succeeded to check the guest attributes by curl")
                results.setdefault("step2", []).append(True)
            else:
                logger.error("Failed to check the guest attributes by curl")
                results.setdefault("step2", []).append(False)
        if "satellite" in register_type:
            guest_registered_id = self.satellite_host_id(
                self.ssh_host(), register_config, guest_name, guest_uuid
            )
            cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}".format(
                username, password, api, guest_registered_id
            )
            ret, output = self.runcmd(cmd, self.ssh_host())
            attr1 = '"id":{0}'.format(guest_registered_id)
            if attr1 in output and guest_name in output:
                logger.info("Succeeded to check the guest attributes by curl")
                results.setdefault("step2", []).append(True)
            else:
                logger.error("Failed to check the guest attributes by curl")
                results.setdefault("step2", []).append(False)

        # case result
        self.vw_case_result(results)
