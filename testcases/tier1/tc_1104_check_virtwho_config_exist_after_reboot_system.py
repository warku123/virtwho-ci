# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134082")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        trigger_name = self.get_exported_param("TRIGGER_NAME")
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        if "trigger-rhel" not in trigger_name:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % trigger_name)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_etc_sys = "/etc/sysconfig/virt-who"
        conf_etc_d = "/etc/virt-who.d/%s.conf" % mode
        conf_etc = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()

        # Case Steps
        logger.info(">>>step1: create virt-who config")
        logger.info("setting options in /etc/sysconfig/virt-who")
        self.vw_option_enable("VIRTWHO_DEBUG", filename=conf_etc_sys)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=conf_etc_sys)

        logger.info("setting options in /etc/virt-who.conf")
        self.vw_option_enable("[global]", filename=conf_etc)
        self.vw_option_enable("interval", filename=conf_etc)
        self.vw_option_update_value("interval", '60', filename=conf_etc)

        logger.info("setting options in /etc/virt-who.d/")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_etc_d)

        logger.info(">>>step2: start virt-who service to check")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_looptime=60)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: start to reboot virt-who host")
        self.system_reboot(self.ssh_host())

        logger.info(">>>step4: start virt-who service to check again")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_looptime=60)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/06/26 Eko<hsun@redhat.com>
# - Case created to check virt-who config exist after reboot system 
