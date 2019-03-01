# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133661")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

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
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/05/31 Yuefen<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
