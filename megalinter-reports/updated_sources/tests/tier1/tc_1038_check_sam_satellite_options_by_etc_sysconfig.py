# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133701")
        if self.pkg_check(self.ssh_host(), "virt-who")[9:15] >= "0.23.3":
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=config_file)
        steps = {"step1": "VIRTWHO_SAM", "step2": "VIRTWHO_SATELLITE6"}

        # case steps
        for step, option in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(">>>{0}: run virt-who to check {1}".format(step, option))
            self.vw_option_enable(option, filename=config_file)
            self.vw_option_update_value(option, "1", filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            self.vw_option_disable(option, filename=config_file)

        # case result
        notes = list()
        notes.append(
            "This case will be deprecated as bug https://bugzilla.redhat.com/show_bug.cgi?id=1368341"
        )
        self.vw_case_result(results, notes)
