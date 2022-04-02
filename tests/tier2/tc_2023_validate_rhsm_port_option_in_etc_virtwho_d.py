# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136628')
        hypervisor_type = self.get_config('hypervisor_type')
        compose_id = self.get_config('rhel_compose')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        register_server = register_config['server']
        register_username = register_config['username']
        register_password = register_config['password']
        register_prefix = register_config['prefix']
        self.system_unregister(self.ssh_host())
        self.vw_option_disable("port", "/etc/rhsm/rhsm.conf")

        # Case Steps
        try:
            logger.info(">>>step1: run virt-who with rhsm_hostname, rhsm_port, rhsm_prefix good value")
            self.vw_option_add("rhsm_hostname", register_server, config_file)
            self.vw_option_add("rhsm_port", "443", config_file)
            self.vw_option_add("rhsm_prefix", register_prefix, config_file)
            self.vw_option_add("rhsm_username", register_username, config_file)
            self.vw_option_add("rhsm_password", register_password, config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step1', []).append(res)

            logger.info(">>>step2: run virt-who with rhsm_port=123")
            self.vw_option_update_value("rhsm_port", "123", config_file)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error='1|2', exp_thread=1, exp_send=0)
            error_msg = ["Connection refused|"
                         "Connection timed out"]
            res2 = self.msg_validation(rhsm_output, error_msg)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)

            logger.info(">>>step3: run virt-who with rhsm_port null value")
            self.vw_option_update_value("rhsm_port", " ", config_file)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res1)

            logger.info(">>>step4: run virt-who with rhsm_port disable")
            self.vw_option_disable("rhsm_port", config_file)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step4', []).append(res1)

        except:
            results.setdefault('step', []).append(False)
            pass

        finally:
            self.vw_option_enable("port", "/etc/rhsm/rhsm.conf")

        # Case Result
        self.vw_case_result(results)
