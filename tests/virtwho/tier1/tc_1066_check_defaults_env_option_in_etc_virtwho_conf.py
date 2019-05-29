# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133695')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()
        register_config = self.get_register_config()
        register_owner = register_config['owner']
        register_env = register_config['env']

        # case steps
        logger.info(">>>step1: Run virt-who with env setting in /etc/virt-who.conf")
        self.vw_option_enable("[defaults]", virtwho_conf)
        self.vw_option_enable("env", virtwho_conf)
        self.vw_option_update_value("env", register_env, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: Run virt-who with owner and env setting in /etc/virt-who.conf")
        self.vw_option_enable("owner", virtwho_conf)
        self.vw_option_update_value("owner", register_owner, virtwho_conf)
        self.vw_option_update_value("env", register_env, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # case result
        self.vw_case_result(results)
