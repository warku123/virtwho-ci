# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136590")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        option_tested = "username"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: username option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: username option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxxx", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: username option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, '红帽€467aa', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: username option is null value")
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step4', []).append(res1)
        else:
            msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: username option is disable")
        self.vw_option_disable(option_tested, conf_file)
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
        self.vw_option_disable(option_tested, conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step6', []).append(res1)
        else:
            msg_list = ["USERNAME.* not set"]
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=1)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step6', []).append(res1)
            results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: username option is null but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_enable(option_tested, conf_file)
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-remote can use sshkey to connect, username is not necessary")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step7', []).append(res1)
        else:
            msg_list = ["Unable to login|incorrect user.*|Authentication failure|Incorrect.*username|Unauthorized|Error.* backend|Permission denied"]
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=1)
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('step7', []).append(res1)
            results.setdefault('step7', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/18 Eko<hsun@redhat.com>
#- Case created to validate username option
#- username null value is acceptable for /etc/virt-who.d/, error msg is: Unable to login
#- username null value is not acceptable for /etc/sysconfig/virt-who, error msg is: USERNAME.* not set,
