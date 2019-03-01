# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133662")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        self.vw_etc_sys_mode_enable(mode)
        config_file = "/etc/sysconfig/virt-who"

        # Case Steps
        logger.info('>>>step1: Run virt-who with "VIRTWHO_DEBUG=1"')
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info('>>>step2: Run virt-who with "VIRTWHO_DEBUG=0"')
        self.vw_option_update_value("VIRTWHO_DEBUG", "0", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info('>>>step3: Run virt-who with "VIRTWHO_DEBUG" disabled')
        self.vw_option_disable("VIRTWHO_DEBUG", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/05/31 Yuefen<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
