# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-170860')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
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
        register_config = self.get_register_config()
        register_server = register_config['server']
        register_type = register_config['type']
        if "satellite" in register_type:
            ssh_sat = register_config['ssh_sat']
            register_server = self.get_hostname(ssh_sat)
        proxy_server = "bootp-73-3-248.eng.pek2.redhat.com"
        proxy_port = "3128"
        bad_proxy_server = "xxx.eng.pek2.redhat.com"
        bad_proxy_port = "0000"
        rhsm_conf = "/etc/rhsm/rhsm.conf"
        error_msg = "ProxyException: Unable to connect to: .*{0}".format(bad_proxy_server)

        # Case Steps
        try:
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

            logger.info(">>>step2: set /etc/rhsm/rhsm.conf with wrong proxy_hostname and proxy_port")
            self.vw_option_update_value("proxy_hostname", bad_proxy_server, filename=rhsm_conf)
            self.vw_option_update_value("proxy_port", bad_proxy_port, filename=rhsm_conf)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            results.setdefault('step2', []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, error_msg, exp_exist=True)
            results.setdefault('step2', []).append(s2)

            logger.info(">>>step3: set rhsm_no_proxy option to register_server in /etc/virt-who.conf")
            self.vw_option_enable("[defaults]", virtwho_conf)
            self.vw_option_enable("rhsm_no_proxy", virtwho_conf)
            self.vw_option_update_value("rhsm_no_proxy", register_server, virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(proxy_server), exp_exist=False)
            results.setdefault('step3', []).append(s2)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server), exp_exist=False)
            results.setdefault('step3', []).append(s3)

            logger.info(">>>step4: set rhsm_no_proxy=* in /etc/virt-who.conf")
            self.vw_option_update_value("rhsm_no_proxy", "*", virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step4', []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(proxy_server), exp_exist=False)
            results.setdefault('step4', []).append(s2)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server), exp_exist=False)
            results.setdefault('step4', []).append(s3)

            logger.info(">>>step5: set rhsm_no_proxy to wrong in /etc/virt-who.conf")
            self.vw_option_update_value("rhsm_no_proxy", "xxx", virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            results.setdefault('step5', []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, error_msg, exp_exist=True)
            results.setdefault('step5', []).append(s2)
        except:
            results.setdefault('step except', []).append(False)
            pass

        finally:
            self.vw_option_update_value("proxy_hostname", "", filename=rhsm_conf)
            self.vw_option_update_value("proxy_port", "", filename=rhsm_conf)

        # case result
        self.vw_case_result(results)