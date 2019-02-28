# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136580")
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
        config_file = "/etc/sysconfig/virt-who"
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', config_file)
        self.vw_etc_sys_mode_enable(mode)
        if "libvirt-remote" in mode:
            mode = "libvirt"
        option_tested = "VIRTWHO_%s_USERNAME" % mode.upper()

        # Case Steps
        logger.info(">>>step1: username option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: username option is wrong value")
        self.vw_option_update_value(option_tested, 'xxxxx', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: username option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, '红帽€467aa', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: username option is null value")
        self.vw_option_update_value(option_tested, '', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step4', []).append(res1)
        else:
            msg_list = ["USERNAME.* not set|virt-who can't be started"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: username option is disable")
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step5', []).append(res1)
        else:
            msg_list = ["USERNAME.* not set|virt-who can't be started"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)

        logger.info(">>>step6: username option is disable but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step6', []).append(res1)
        else:
            msg_list = ["USERNAME.* not set"]
            res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step6', []).append(res1)
            results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: username option is null but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_enable(option_tested, config_file)
        self.vw_option_update_value(option_tested, '', config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step7', []).append(res1)
        else:
            msg_list = ["USERNAME.* not set"]
            res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step7', []).append(res1)
            results.setdefault('step7', []).append(res2)

        # Case Result
        notes = list()
        if "libvirt" not in mode:
            notes.append("Bug(Step4,Step5,Step6,Step7): other unexpected ERROR msg found in rhsm.log")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530841")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/18 Eko<hsun@redhat.com>
#- Case created to validate username option
