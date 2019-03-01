# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136731")
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
        logger.info(">>>step1: interval is null value in /etc/virt-who.conf")
        self.vw_option_enable("interval", virtwho_conf)
        self.vw_option_update_value("interval", '', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check virt-who firstly run interval configured in /etc/sysconfig/virt-who")
        self.vw_option_update_value("interval", '120', virtwho_conf)
        self.vw_option_enable("VIRTWHO_INTERVAL", '/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', '/etc/sysconfig/virt-who')
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step2', []).append(res)

        # Case Result
        notes = list()
        notes.append("Bug(Step1): failed to report mappings if configure 'interval=' value to null")
        notes.append("BZ: https://bugzilla.redhat.com/show_bug.cgi?id=1523482")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
# - Case created
