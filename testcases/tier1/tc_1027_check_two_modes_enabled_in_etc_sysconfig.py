# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133743")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        option_tested = "VIRTWHO_INTERVAL"
        config_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)
        extra_mode='libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_extra_conf_in_sys(extra_mode)
        self.vw_etc_sys_mode_enable(mode)

        # Case Steps
        logger.info(">>>step1: check reporter sent and no error msg")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

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
#- 2018/06/08 Eko<hsun@redhat.com>
#- Case created to validate two modes in /etc/sysconfig/virt-who
