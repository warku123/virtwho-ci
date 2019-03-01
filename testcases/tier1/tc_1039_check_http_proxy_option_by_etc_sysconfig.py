# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133704")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)
        squid_server = "10.73.3.248:3128"
        steps = {'step1':'http_proxy', 'step2':'https_proxy'}
        self.vw_etc_d_mode_create(mode, "%s_config" % mode, filename="/etc/virt-who.d/%s.conf" % mode)

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s" % (step, option))
            if option == "http_proxy":
                value = "http://%s" % squid_server
            if option == "https_proxy":
                value = "https://%s" % squid_server
            self.vw_option_add(option, value, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, "Connection built.*%s" %squid_server, exp_exist=True)
            results.setdefault(step, []).append(s2)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*%s" %squid_server, exp_exist=True)
            results.setdefault(step, []).append(s3)
            self.vw_option_del(option, filename=config_file)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2019/01/21 Yuefen<yuefliu@redhat.com>
#- Delete bug 1638250 info 
#- 2018/06/11 Eko<hsun@redhat.com>
#- Case created to validate http_proxy option
