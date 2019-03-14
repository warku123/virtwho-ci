# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: fetach and send report for /etc/virt-who.d/xxx.conf
        :Polarion_Id: RHEL-134107 
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()

        # Case Steps
        logger.info(">>>step1: run virt-who for {0}".format(config_file))
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        # Case Result
        self.vw_case_result(results)
