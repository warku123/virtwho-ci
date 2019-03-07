# coding:utf-8
from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: -d option
        :Polarion_Id: RHEL-133661
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        self.vw_case_init()

        # Case Config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        logger.info(">>>step1: Run virt-who by cli with -d option")
        cmd = "virt-who -d"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: Run virt-who by cli without -d option")
        cmd = "virt-who"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # Case Result
        notes = list()
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1510712")
        self.vw_case_result(results, notes)
