# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136591")
        hypervisor_type = self.get_config("hypervisor_type")
        if hypervisor_type in ("libvirt-local", "vdsm", "kubevirt"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        option_tested = "password"
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        msg_list = [
            "Unable to login|"
            "incorrect user.*|"
            "Authentication failure|"
            "Authentication failed|"
            "Incorrect.*username|"
            "Unauthorized|"
            "Error.* backend|"
            "Permission denied|"
            "HTTP Auth Failed"
        ]

        # Case Steps
        logger.info(">>>step1: password option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: password option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxxx", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, password value is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step2", []).append(res1)
        else:
            res1 = self.op_normal_value(
                data, exp_error="1|2|3", exp_thread=1, exp_send=0
            )
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault("step2", []).append(res1)
            results.setdefault("step2", []).append(res2)

        logger.info(">>>step3: password option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, "红帽€467aa", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        compose_id = self.get_config("rhel_compose")
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, "
                "password value is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step3", []).append(res1)
        else:
            if "RHEL-7" in compose_id:
                msg = "'password': is not in latin1 encoding"
                res1 = self.op_normal_value(
                    data, exp_error="1|2|3", exp_thread=0, exp_send=0
                )
                res2 = self.vw_msg_search(rhsm_output, msg, exp_exist=True)
            else:
                res1 = self.op_normal_value(
                    data, exp_error="1|2|3", exp_thread=1, exp_send=0
                )
                res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault("step3", []).append(res1)
            results.setdefault("step3", []).append(res2)

        logger.info(">>>step4: password option is null value")
        self.vw_option_update_value(option_tested, "", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, username is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step4", []).append(res1)
        else:
            res1 = self.op_normal_value(
                data, exp_error="0|1|2", exp_thread=1, exp_send=0
            )
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault("step4", []).append(res1)
            results.setdefault("step4", []).append(res2)

        logger.info(">>>step5: password option is disable")
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, username is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step5", []).append(res1)
        else:
            msg_list_s5 = ["PASSWORD.* not set|virt-who can't be started"]
            res1 = self.op_normal_value(
                data, exp_error="0|1|2", exp_thread=0, exp_send=0
            )
            res2 = self.msg_validation(rhsm_output, msg_list_s5, exp_exist=True)
            results.setdefault("step5", []).append(res1)
            results.setdefault("step5", []).append(res2)

        logger.info(">>>step6: password option is disable but another config is ok")
        config_name_ok = "virtwho-config-ok"
        config_file_ok = "/etc/virt-who.d/{0}.conf".format(config_name_ok)
        self.vw_etc_d_mode_create(config_name_ok, config_file_ok)
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, username is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step6", []).append(res1)
        else:
            msg_list_s6 = ["PASSWORD.* not set"]
            res1 = self.op_normal_value(
                data, exp_error="1|2|3", exp_thread=1, exp_send=1
            )
            res2 = self.msg_validation(rhsm_output, msg_list_s6, exp_exist=True)
            results.setdefault("step6", []).append(res1)
            results.setdefault("step6", []).append(res2)

        logger.info(">>>step7: password option is null but another config is ok")
        self.vw_option_enable(option_tested, config_file)
        self.vw_option_update_value(option_tested, "", config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        if "libvirt-remote" in hypervisor_type:
            logger.warning(
                "libvirt-remote can use sshkey to connect, username is not necessary"
            )
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault("step7", []).append(res1)
        else:
            res1 = self.op_normal_value(
                data, exp_error="1|2|3", exp_thread=1, exp_send=1
            )
            res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
            results.setdefault("step7", []).append(res1)
            results.setdefault("step7", []).append(res2)

        # Case Result
        self.vw_case_result(results)
