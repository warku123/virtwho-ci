# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136709")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)
        self.vw_option_enable("VIRTWHO_INTERVAL", filename=config_file)
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', filename=config_file)
        good_squid_server = "10.73.3.248:3128"
        wrong_squid_server = "10.73.3.24:3128"
        types = {'type1':'http_proxy', 'type2':'https_proxy'}
        self.vw_etc_d_mode_create(mode, "%s_config" % mode, filename="/etc/virt-who.d/%s.conf" % mode)

        # Case Steps
        logger.info(">>>step1: run with good proxy server")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s" % (type, option))
            if option == "http_proxy":
                value = "http://%s" % good_squid_server
            if option == "https_proxy":
                value = "https://%s" % good_squid_server
            self.vw_option_add(option, value, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(rhsm_output, "Connection built.*%s" % good_squid_server)
            res3 = self.vw_msg_search(rhsm_output, "Using proxy.*%s" % good_squid_server)
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            results.setdefault('step1', []).append(res3)
            self.vw_option_del(option, filename=config_file)

        logger.info(">>>step2: run with wrong proxy server and 'NO_PROXY'")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s with wrong proxy" % (type, option))
            if option == "http_proxy":
                value = "http://%s" % wrong_squid_server
            if option == "https_proxy":
                value = "https://%s" % wrong_squid_server
            self.vw_option_add(option, value, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            error_msg = "Connection refused|Cannot connect to proxy|Connection timed out"
            res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            res2 = self.vw_msg_search(rhsm_output, error_msg)
            self.vw_option_add("NO_PROXY", "*", filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
            results.setdefault('step2', []).append(res3)
            self.vw_option_del(option, filename=config_file)
            self.vw_option_del("NO_PROXY", filename=config_file)

        # Case Result
        notes = list()
        if "hyperv" in mode:
            notes.append("Bug(Step1): hyperv doesn't support http_proxy")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1638250")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/10 Yuefen<yuefliu@redhat.com>
# - Case created to validate http_proxy extra option
