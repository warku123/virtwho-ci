# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-134107")
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info(">>>step1: run virt-who for {0}".format(config_file))
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault("step2", []).append(res)

        # case result
        self.vw_case_result(results)
