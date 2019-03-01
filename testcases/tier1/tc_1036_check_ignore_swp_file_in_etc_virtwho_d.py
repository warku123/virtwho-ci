# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133739")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        swap_file = "/etc/virt-who.d/.test.conf.swp"
        sysconfig_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", filename=sysconfig_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=sysconfig_file)
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
        self.vw_etc_d_mode_create(mode, conf_name, filename=swap_file)

        # Case Steps
        logger.info(">>>step1: check the swp file is ignored or not ")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "test.conf.swp", exp_exist=False)
        results.setdefault('step1', []).append(s2)

        logger.info(">>>step2: check how many modes in rhsm.log")
        modes = re.findall(r'Using configuration.*\("(.*?)" mode\)', rhsm_output)
        if len(modes) == 1:
            logger.info("Succeeded to check, only one mode in rhsm.log: %s" % modes)
            results.setdefault('step2', []).append(True)
        else:
            logger.error("Failed to check, the modes number is not matched: %s" % modes)
            results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/11 Eko<hsun@redhat.com>
#- Case created to validate swp file is ignored or not
