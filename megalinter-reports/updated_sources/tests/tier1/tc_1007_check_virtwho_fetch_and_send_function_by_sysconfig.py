# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133789")
        if self.pkg_check(self.ssh_host(), "virt-who")[9:15] >= "0.23.3":
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename=config_file)

        # case steps
        logger.info(">>>step1: run virt-who by /etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault("step2", []).append(res)

        # case result
        self.vw_case_result(results)
