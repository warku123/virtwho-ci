# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: fetch and sent report
        :Polarion_Id: RHEL-133789
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_etc_sys_mode_enable()
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)

        # Case Steps
        logger.info(">>>step1: run virt-who by /etc/sysconfig/virt-who")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        # Case Result
        self.vw_case_result(results)
