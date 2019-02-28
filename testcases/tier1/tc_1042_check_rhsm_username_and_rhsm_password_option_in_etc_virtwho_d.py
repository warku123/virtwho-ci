# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133710")
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
        if "stage" in server_type:
            rhsm_prefix = "/subscription"
            user, passwd, owner, env = self.stage_account_get(mode)
        else:
            rhsm_prefix = "/rhsm"
            user, passwd = self.satellite_account_get(server_ip)

        # Case Steps
        logger.info(">>>step1: run virt-who without rhsm_username and rhsm_password")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who with rhsm_username and rhsm_password good value")
        self.vw_option_add("rhsm_hostname", server_ip, filename=conf_file)
        self.vw_option_add("rhsm_port", "443", filename=conf_file)
        self.vw_option_add("rhsm_prefix", rhsm_prefix, filename=conf_file)
        self.vw_option_add("rhsm_username", user, filename=conf_file)
        self.vw_option_add("rhsm_password", passwd, filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: run virt-who with rhsm_username and rhsm_password null value")
        self.vw_option_update_value("rhsm_username", "", filename=conf_file)
        self.vw_option_update_value("rhsm_password", "", filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step4: run virt-who with rhsm_username and rhsm_password disable")
        self.vw_option_disable("rhsm_username", filename=conf_file)
        self.vw_option_disable("rhsm_password", filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/13 Eko<hsun@redhat.com>
#- Case created to validate rhsm_username and rhsm_password_option
