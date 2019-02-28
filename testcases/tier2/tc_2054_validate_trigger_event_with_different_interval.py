# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136726")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_option_enable("VIRTWHO_INTERVAL", filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        try:
            logger.info(">>>step1: run virt-who with event(guest_suspend) for interval 60")
            self.vw_option_update_value("VIRTWHO_INTERVAL", '60', filename="/etc/sysconfig/virt-who")
            data, tty_output, rhsm_output = self.vw_start(exp_send=2, event="guest_suspend")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=2, exp_interval=60)
            results.setdefault('step1', []).append(res1)
        except:
            results.setdefault('step1', []).append(False)
            pass
        finally:
            logger.info(">>>step2: run virt-who with event(guest_resume) for interval 120")
            self.vw_option_update_value("VIRTWHO_INTERVAL", '120', filename="/etc/sysconfig/virt-who")
            data, tty_output, rhsm_output = self.vw_start(exp_send=2, event="guest_resume")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=2, exp_interval=120)
            results.setdefault('step2', []).append(res1)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/08/01 Eko<hsun@redhat.com>
#- Case created
