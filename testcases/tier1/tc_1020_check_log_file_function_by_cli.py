# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134122")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        log_dir = "/var/log/rhsm/virtwho"
        log_file = "/var/log/rhsm/virtwho/virtwho.log"
        guest_uuid = self.mode_guest_uuid(mode)
        cmd1 = self.vw_cli_base(mode) + "-d -l %s -f %s" % (log_dir,log_file)
        cmd2 = self.vw_cli_base(mode) + "-d --log-dir %s --log-file %s" % (log_dir,log_file)
        steps = {'step1':cmd1, 'step2':cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who cli to check log-file" % step)
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            ret, output = self.runcmd("ls %s" %log_file, self.ssh_host(), desc="ls virtwho/virtwho.log")
            if ret == 0:
                logger.info("Succeeded to find file: %s" %log_file)
                ret, output = self.runcmd("cat %s" %log_file, self.ssh_host(), desc="cat virtwho/virtwho.log")
                d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if d1 is False or d2 is False:
                    results.setdefault(step, []).append(False)
            else:
                logger.error("%s is not exist" % log_file)
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
