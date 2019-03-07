# coding:utf-8
from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: fetch and sent report by cli
        :Polarion_Id: RHEL-134108 
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        self.vw_case_init()

        # Case Config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()
 
        # Case Steps
        logger.info(">>>step1: run virt-who by cli")
        cmd = "virt-who -d"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        # Case Result
        self.vw_case_result(results)
