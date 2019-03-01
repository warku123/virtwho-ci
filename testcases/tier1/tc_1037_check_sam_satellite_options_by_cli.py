# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133748")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support --sam and --satellite6 options in command line")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        cmd1 = self.vw_cli_base(mode) + "--sam -d"
        cmd2 = self.vw_cli_base(mode) + "--satellite6 -d"
        steps = {'step1':cmd1, 'step2':cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who cli to check sam/satellite options" % step)
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)

        # Case Result
        notes = list()
        notes.append("This case will be deprecated as bug https://bugzilla.redhat.com/show_bug.cgi?id=1368341")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/11 Eko<hsun@redhat.com>
# - Case created to validate sam/satellite options
