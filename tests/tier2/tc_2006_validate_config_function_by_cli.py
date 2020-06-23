# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136710')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        guest_uuid = self.get_hypervisor_guestuuid()
        self.vw_option_enable("[global]", filename="/etc/virt-who.conf")
        self.vw_option_enable("interval", filename="/etc/virt-who.conf")
        self.vw_option_update_value("interval", '120', filename="/etc/virt-who.conf")
        self.vw_option_enable("debug", filename="/etc/virt-who.conf")
        self.vw_option_update_value("debug", 'True', filename="/etc/virt-who.conf")
        self.vw_option_enable("[defaults]", filename="/etc/virt-who.conf")
        self.vw_option_enable("owner", filename="/etc/virt-who.conf")
        self.vw_option_update_value("owner", 'xxx', filename="/etc/virt-who.conf")
        self.vw_option_enable("env", filename="/etc/virt-who.conf")
        self.vw_option_update_value("env", 'xxx', filename="/etc/virt-who.conf")

        # Case Steps
        logger.info(">>>step1: configure two same mode in different path then run virt-who -c")
        config_name_1 = "virtwho-config-1"
        config_name_2 = "virtwho-config-2"
        config_file_1 = "/etc/virt-who.d/{0}.conf".format(config_name_1)
        config_file_2 = "/root/{0}.conf".format(config_name_2)
        self.vw_etc_d_mode_create(config_name_1, config_file_1)
        self.vw_etc_d_mode_create(config_name_2, config_file_2)
        cmd = "virt-who -c {0} -i 60".format(config_file_2)
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: check virt-who didn't run config_file_1")
        num = rhsm_output.count('"guestId": "{0}"'.format(guest_uuid))
        logger.info("Actual mapping info num: {0}".format(num))
        logger.info("Expected mapping info num: 1 for sat63 above and stage")
        results.setdefault('step2', []).append(num == 1)

        logger.info(">>>step3: check '#virt-who -o -c' with wrong config file")
        wrong_file = "xxx"
        error_msg = "No valid configuration file provided using -c/--config"
        cmd = "virt-who -d -o -c {0}".format(wrong_file)
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=0)
        res1 = self.op_normal_value(data, exp_error=2, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(tty_output, error_msg, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: run virt-who with -c option multiple times")
        self.vw_etc_d_delete_all()
        config_file_1 = "/root/{0}.conf".format(config_name_1)
        self.vw_etc_d_mode_create(config_name_1, config_file_1)
        cmd = "virt-who -c {0} -c {1}".format(config_file_1, config_file_2)
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120)
        results.setdefault('step4', []).append(res)

        logger.info(">>>step5: check virt-who has run both config")
        num = rhsm_output.count('"guestId": "{0}"'.format(guest_uuid))
        logger.info("Actual mapping info num: {0}".format(num))
        register_type = self.get_config('hypervisor_type')
        if "satellite62" in register_type:
            logger.info("Expected mapping info num: 1 for sat62")
            results.setdefault('step5', []).append(num == 1)
        else:
            logger.info("Expected mapping info num: 2 for sat63 above and stage")
            results.setdefault('step5', []).append(num == 2)


        # Case Result
        self.vw_case_result(results)