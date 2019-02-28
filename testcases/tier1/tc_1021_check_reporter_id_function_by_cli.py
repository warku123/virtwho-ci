# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134123")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        guest_uuid = self.mode_guest_uuid(mode)
        reporter_id = "virtwho_reporter_id_tc1021"
        cmd1 = self.vw_cli_base(mode) + "-d -r %s" % reporter_id
        cmd2 = self.vw_cli_base(mode) + "-d --reporter-id %s" % reporter_id
        steps = {'step1':cmd1, 'step2':cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who cli to check reporter_id" % step)
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            if data['reporter_id'] == reporter_id:
                logger.info("Succeeded to find the expected reporter_id: %s" % reporter_id)
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to find the expected reporter_id: %s" % reporter_id)
                results.setdefault(step, []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/08 Eko<hsun@redhat.com>
# - Case created to validate log_dir option
