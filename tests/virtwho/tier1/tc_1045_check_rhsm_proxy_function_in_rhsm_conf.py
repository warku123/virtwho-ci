# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133691')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        register_type = register_config['type']
        register_server = register_config['server']
        register_username = register_config['username']
        register_password = register_config['password']
        register_prefix = register_config['prefix']
        proxy_server = "10.73.3.248"
        proxy_port = "3128"
        rhsm_conf = "/etc/rhsm/rhsm.conf"

        # Case Steps
        logger.info(">>>step1: set /etc/rhsm/rhsm.conf with good proxy_hostname and proxy_port")
        self.vw_option_update_value("proxy_hostname", proxy_server, filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", proxy_port, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(proxy_server), exp_exist=True)
        results.setdefault('step1', []).append(s2)
        s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server), exp_exist=True)
        results.setdefault('step1', []).append(s3)

        logger.info(">>>step2: set /etc/rhsm/rhsm.conf with wrong proxy_port")
        self.vw_option_update_value("proxy_port", "9999", filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        results.setdefault('step2', []).append(s1)

        logger.info(">>>step3: set /etc/rhsm/rhsm.conf with wrong proxy_port and no_proxy")
        self.vw_option_update_value("no_proxy", register_server, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(s1)
        self.vw_option_update_value("no_proxy", "", filename=rhsm_conf)

        logger.info(">>>step4: set /etc/rhsm/rhsm.conf with wrong proxy_port and set NO_PROXY in /etc/sysconfig/virt-who")
        self.vw_option_add("NO_PROXY", register_server, filename="/etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(s1)
        self.vw_option_del("NO_PROXY", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("proxy_hostname", "", filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", "", filename=rhsm_conf)

        logger.info(">>>step5: set /etc/virt-who.d/ with good rhsm_proxy_hostname and rhsm_proxy_port")
        self.vw_option_add("rhsm_proxy_hostname", proxy_server, filename=config_file)
        self.vw_option_add("rhsm_proxy_port", proxy_port, filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step5', []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(proxy_server), exp_exist=True)
        results.setdefault('step5', []).append(s2)
        s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server), exp_exist=True)
        results.setdefault('step5', []).append(s3)

        logger.info(">>>step6: set /etc/virt-who.d/ with wrong rhsm_proxy_port")
        self.vw_option_update_value("rhsm_proxy_port", "9999", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        results.setdefault('step6', []).append(s1)

        logger.info(">>>step7: set /etc/virt-who.d/ with wrong rhsm_proxy_port and set no_proxy in /etc/rhsm/rhsm.conf")
        self.vw_option_update_value("no_proxy", register_server, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step7', []).append(s1)
        self.vw_option_update_value("no_proxy", "", filename=rhsm_conf)

        logger.info(">>>step8: set /etc/virt-who.d/ with wrong proxy_port and set NO_PROXY in /etc/sysconfig/virt-who")
        self.vw_option_add("NO_PROXY", register_server, filename="/etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step8', []).append(s1)
        self.vw_option_del("NO_PROXY", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("proxy_hostname", "", filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", "", filename=rhsm_conf)

        # case result
        self.vw_case_result(results)
