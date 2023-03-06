# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-137014")
        hypervisor_type = self.get_config("hypervisor_type")
        if hypervisor_type in ("libvirt-local", "vdsm"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", "True", virtwho_conf)
        config_name_1 = "virtwho-config-1"
        config_file_1 = "/root/{0}.conf".format(config_name_1)
        self.vw_etc_d_mode_create(config_name_1, config_file_1)
        config_name_2 = "virtwho-config-2"
        config_file_2 = "/etc/virt-who.d/{0}.conf".format(config_name_2)
        self.vw_etc_d_mode_create(config_name_2, config_file_2)
        guest_uuid = self.get_hypervisor_guestuuid()

        # Case Steps
        logger.info(">>>step1: 'configs' is valid file")
        self.vw_option_enable("configs", virtwho_conf)
        self.vw_option_update_value("configs", config_file_1, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res1)
        # check virt-who didn't run config_file_2
        num = rhsm_output.count('"guestId": "{0}"'.format(guest_uuid))
        logger.info("Actual mapping info num: {0}".format(num))
        logger.info("Expected mapping info num: 1 for sat63 above and stage")
        results.setdefault("step1", []).append(num == 1)

        logger.info(">>>step2: 'configs' is null value")
        self.vw_option_update_value("configs", "", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step2", []).append(res1)
        # check virt-who has run config_file_2
        num = rhsm_output.count('"guestId": "{0}"'.format(guest_uuid))
        logger.info("Actual mapping info num: {0}".format(num))
        logger.info("Expected mapping info num: 1 for sat63 above and stage")
        results.setdefault("step2", []).append(num == 1)

        logger.info(">>>step3: 'configs' is wrong value")
        self.vw_option_update_value("configs", "xxxxxx", virtwho_conf)
        error_msg_1 = "Unable to read configuration file"
        error_msg_2 = "No valid configuration file provided using -c/--config"
        data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
        res1 = self.op_normal_value(data, exp_error=2, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, error_msg_1, exp_exist=True)
        res3 = self.vw_msg_search(rhsm_output, error_msg_2, exp_exist=True)
        results.setdefault("step3", []).append(res1)
        results.setdefault("step3", []).append(res2)
        results.setdefault("step3", []).append(res3)

        # Case Result
        self.vw_case_result(results)
