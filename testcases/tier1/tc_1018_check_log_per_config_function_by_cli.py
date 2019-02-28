# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133696")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        guest_uuid = self.mode_guest_uuid(mode)
        cmd1 = self.vw_cli_base(mode) + "-d -m"
        cmd2 = self.vw_cli_base(mode) + "-d --log-per-config"
        steps = {'step1':cmd1, 'step2':cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who cli to check log-per-config" % step)
            logger.info("Start to check the per log file in /var/log/rhsm/virtwho.*")
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            cmd = "ls /var/log/rhsm/virtwho*"
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="list file")
            if ret != 0 or output is None:
                logger.error("Failed to find /var/log/rhsm/virtwho* files")
                results.setdefault(step, []).append(False)
            files = output.split('\n') 
            ''' check files exist or not'''
            if any("destination" in fd for fd in files):
                logger.info("Succeeded to find virtwho.destination file")
            else: 
                logger.error("Failed to find virtwho.destination file")
                results.setdefault(step, []).append(False)
            if any("main" in fd for fd in files):
                logger.info("Succeeded to find virtwho.main file")
            else: 
                logger.error("Failed to find virtwho.main file")
                results.setdefault(step, []).append(False)
            if any("rhsm_log" in fd for fd in files):
                logger.info("Succeeded to find virtwho.rhsm_log file")
            else:
                logger.error("Failed to find virtwho.rhsm_log file")
                results.setdefault(step, []).append(False)
            ''' check message is expected or not'''
            for fd in files:
                fd = fd.strip()
                if "destination" in fd:
                    ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                    d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                    d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if d1 is False or d2 is False:
                        logger.error("Failed to validate virtwho.destination file")
                        results.setdefault(step, []).append(False)
                if "main" in fd:
                    ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                    m1 = self.vw_msg_search(output, "Report for config", exp_exist=True)
                    m2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if m1 is False or m2 is False:
                        logger.error("Failed to validate virtwho.main file")
                        results.setdefault(step, []).append(False)
                if "rhsm_log" in fd:
                    ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                    r1 = self.vw_msg_search(output, "Using reporter_id=", exp_exist=True)
                    r2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if r1 is False or r2 is False:
                        logger.error("Failed to validate virtwho.rhsm_log file")
                        results.setdefault(step, []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/08 Eko<hsun@redhat.com>
# - Case created to validate log_per_config option
