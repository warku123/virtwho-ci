# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133691")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
        proxy_server = "10.73.3.248"
        proxy_port = "3128"
        rhsm_conf = "/etc/rhsm/rhsm.conf"
        if "stage" in server_type:
            rhsm_prefix = "/subscription"
            user, passwd, owner, env = self.stage_account_get(mode)
            server_name = server_ip
        else:
            rhsm_prefix = "/rhsm"
            user, passwd = self.satellite_account_get(server_ip)
            server_name = self.satellite_hostname(server_ip)

        # Case Steps
        logger.info(">>>step1: set /etc/rhsm/rhsm.conf with good proxy_hostname and proxy_port")
        self.vw_option_update_value("proxy_hostname", proxy_server, filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", proxy_port, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "Connection built.*%s" %proxy_server, exp_exist=True)
        results.setdefault('step1', []).append(s2)
        s3 = self.vw_msg_search(rhsm_output, "Using proxy.*%s" %proxy_server, exp_exist=True)
        results.setdefault('step1', []).append(s3)

        logger.info(">>>step2: set /etc/rhsm/rhsm.conf with wrong proxy_port")
        self.vw_option_update_value("proxy_port", "9999", filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        results.setdefault('step2', []).append(s1)

        logger.info(">>>step3: set /etc/rhsm/rhsm.conf with wrong proxy_port and no_proxy")
        self.vw_option_update_value("no_proxy", server_name, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(s1)
        self.vw_option_update_value("no_proxy", "", filename=rhsm_conf)

        logger.info(">>>step4: set /etc/rhsm/rhsm.conf with wrong proxy_port and set NO_PROXY in /etc/sysconfig/virt-who")
        self.vw_option_add("NO_PROXY", server_name, filename="/etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(s1)
        self.vw_option_del("NO_PROXY", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("proxy_hostname", "", filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", "", filename=rhsm_conf)

        logger.info(">>>step5: set /etc/virt-who.d/ with good rhsm_proxy_hostname and rhsm_proxy_port")
        self.vw_option_add("rhsm_proxy_hostname", proxy_server, filename=conf_file)
        self.vw_option_add("rhsm_proxy_port", proxy_port, filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step5', []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "Connection built.*%s" %proxy_server, exp_exist=True)
        results.setdefault('step5', []).append(s2)
        s3 = self.vw_msg_search(rhsm_output, "Using proxy.*%s" %proxy_server, exp_exist=True)
        results.setdefault('step5', []).append(s3)

        logger.info(">>>step6: set /etc/virt-who.d/ with wrong rhsm_proxy_port")
        self.vw_option_update_value("rhsm_proxy_port", "9999", filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        results.setdefault('step6', []).append(s1)

        logger.info(">>>step7: set /etc/virt-who.d/ with wrong rhsm_proxy_port and set no_proxy in /etc/rhsm/rhsm.conf")
        self.vw_option_update_value("no_proxy", server_name, filename=rhsm_conf)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step7', []).append(s1)
        self.vw_option_update_value("no_proxy", "", filename=rhsm_conf)

        logger.info(">>>step8: set /etc/virt-who.d/ with wrong proxy_port and set NO_PROXY in /etc/sysconfig/virt-who")
        self.vw_option_add("NO_PROXY", server_name, filename="/etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step8', []).append(s1)
        self.vw_option_del("NO_PROXY", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("proxy_hostname", "", filename=rhsm_conf)
        self.vw_option_update_value("proxy_port", "", filename=rhsm_conf)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/13 Eko<hsun@redhat.com>
#- Case created to validate rhsm_proxy options
