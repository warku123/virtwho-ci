# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136577")
        hypervisor_type = self.get_config("hypervisor_type")
        if hypervisor_type in ("libvirt-local", "vdsm"):
            self.vw_case_skip(hypervisor_type)
        if self.pkg_check(self.ssh_host(), "virt-who")[9:15] >= "0.23.3":
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        if hypervisor_type == "libvirt-remote":
            hypervisor_type = "libvirt"
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        sysconfig_file = "/etc/sysconfig/virt-who"
        guest_uuid = self.get_hypervisor_guestuuid()
        option_tested = "VIRTWHO_{0}_OWNER".format(hypervisor_type.upper())
        self.vw_etc_sys_mode_enable()

        # Case Steps
        logger.info(">>>step1: owner option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: owner option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxx", sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = [
            "owner.* is different|Communication with subscription manager failed"
        ]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step2", []).append(res1)
        results.setdefault("step2", []).append(res2)

        logger.info(">>>step3: owner option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, "红帽€467aa", sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = [
            "codec can't decode|codec can't encode|Communication with subscription manager failed|owner.* is different"
        ]
        res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step3", []).append(res1)
        results.setdefault("step3", []).append(res2)

        logger.info(">>>step4: owner option is null value")
        self.vw_option_update_value(option_tested, "", sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = [
            "owner not in|owner.* not set|virt-who can't be started|Communication with subscription manager failed"
        ]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step4", []).append(res1)
        results.setdefault("step4", []).append(res2)

        logger.info(">>>step5: owner option is disable")
        self.vw_option_disable(option_tested, sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = [
            "owner not in|owner.* not set|virt-who can't be started|Communication with subscription manager failed"
        ]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step5", []).append(res1)
        results.setdefault("step5", []).append(res2)

        logger.info(">>>step6: owner option is disable but another config is ok")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_option_disable(option_tested, sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = [
            "owner not in|owner.* not set|Communication with subscription manager failed"
        ]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step6", []).append(res1)
        results.setdefault("step6", []).append(res2)

        logger.info(">>>step7: owner option is null but another config is ok")
        self.vw_option_enable(option_tested, sysconfig_file)
        self.vw_option_update_value(option_tested, "", sysconfig_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = [
            "owner not in|owner.* not set|Communication with subscription manager failed"
        ]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault("step7", []).append(res1)
        results.setdefault("step7", []).append(res2)

        # Case Result
        notes = list()
        if "libvirt" not in hypervisor_type:
            notes.append(
                "Bug(Step4,Step5,Step6,Step7): other unexpected ERROR msg found in rhsm.log"
            )
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530254")
        self.vw_case_result(results, notes)
