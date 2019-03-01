# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134059")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        steps = {'step1':'service_debug', 'step2':'service_no_debug', 'step3':'cli_debug', 'step4':'cli_no_debug'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: Run virt-who by %s to check 'rhsm.connection' info" % (step, option))
            self.vw_env_init(mode)
            self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
            if step == "step1":
                self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
                self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            if step == "step2":
                self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
                self.vw_option_update_value("VIRTWHO_DEBUG", '0', filename="/etc/sysconfig/virt-who")
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            if step == "step3":
                cli = "virt-who -d"
                data, tty_output, rhsm_output = self.vw_start(cli, exp_send=1)
            if step == "step4":
                cli = "virt-who"
                data, tty_output, rhsm_output = self.vw_start(cli, exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(rhsm_output, '[rhsm.connection INFO]', exp_exist=True)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
