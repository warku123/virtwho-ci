# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136632")
        hypervisor_type = self.get_config("hypervisor_type")
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
        register_config = self.get_register_config()
        register_server = register_config["server"]
        register_username = register_config["username"]
        register_password = register_config["password"]
        register_prefix = register_config["prefix"]
        self.system_unregister(self.ssh_host())

        # Case Steps
        logger.info(">>>step1: run virt-who with rhsm_encrypted_password good value")
        encrypted_value = self.vw_encrypted(register_password)
        self.vw_option_add("rhsm_hostname", register_server, config_file)
        self.vw_option_add("rhsm_port", "443", config_file)
        self.vw_option_add("rhsm_prefix", register_prefix, config_file)
        self.vw_option_add("rhsm_username", register_username, config_file)
        self.vw_option_add("rhsm_encrypted_password", encrypted_value, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: run virt-who with rhsm_encrypted_password=xxxxxx")
        error_msg = "Communication with subscription manager failed"
        self.vw_option_update_value("rhsm_encrypted_password", "xxxxxx", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, error_msg, exp_exist=True)
        results.setdefault("step2", []).append(res1)
        results.setdefault("step2", []).append(res2)

        logger.info(">>>step3: skip this step")
        # logger.info(">>>step3: run virt-who with rhsm_encrypted_password=红帽©¥®ðπ∉")
        # self.vw_option_update_value("rhsm_encrypted_password", "红帽©¥®ðπ∉", config_file)
        # data, tty_output, rhsm_output = self.vw_start()
        # res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        # res2 = self.vw_msg_search(rhsm_output, "codec can't decode", exp_exist=True)
        # results.setdefault('step3', []).append(res1)
        # results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: run virt-who with rhsm_encrypted_password null value")
        error_msg = 'Option "rhsm_encrypted_password" cannot be decrypted'
        self.vw_option_update_value("rhsm_encrypted_password", " ", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, error_msg, exp_exist=True)
        results.setdefault("step4", []).append(res1)
        results.setdefault("step4", []).append(res2)

        # Case Result
        self.vw_case_result(results)
