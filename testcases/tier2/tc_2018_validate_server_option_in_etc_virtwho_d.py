# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136589")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        option_tested = "server"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: server option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: server option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxxx", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: server option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, '红帽€467aa', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend|Unable to connect|Unable to login"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: server option is null value")
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-local mode will be used to instead when server option is null for libvirt-remote")
            msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        else:
            msg_list = ["SERVER.* not set|virt-who can't be started|No host supplied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: server option is disable")
        self.vw_option_disable(option_tested, conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-local mode will be used to instead when server option is disabled for libvirt-remote")
            msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        else:
            msg_list = ["SERVER.* not set|virt-who can't be started|No host supplied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info(">>>step6: server option is disable but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_disable(option_tested, conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["SERVER.* not set|Error in .* backend|No host supplied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step6', []).append(res1)
        results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: server option is null but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_enable(option_tested, conf_file)
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["SERVER.* not set|Error in .* backend|No host supplied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step7', []).append(res1)
        results.setdefault('step7', []).append(res2)

        # Case Result
        notes = list()
        if "libvirt" not in mode:
            notes.append("Bug(Step4): Set server to null value, virt-who still can be started")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1516209")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/18 Eko<hsun@redhat.com>
#- Case created to validate server option
