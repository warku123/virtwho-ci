# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133685")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: enable interval and set to 10 in /etc/virt-who.conf")
        self.vw_option_enable("interval", virtwho_conf)
        self.vw_option_update_value("interval", '10', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: enable interval and set to 60 in /etc/virt-who.conf")
        self.vw_option_update_value("interval", '60', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: enable interval and set to 120 in /etc/virt-who.conf")
        self.vw_option_update_value("interval", '120', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120, exp_loopnum=1, exp_looptime=120)
        results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/03 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps
# - 2018/06/13 yanpliu<yanpliu@redhat.com>
# - Case created
