# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133736')
        self.vw_case_init()

        # case config
        results = dict()

        # case steps
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] < '1.31.0':
            logger.info(">>>step1: stop virt-who to check virt-who file permission")
            config_file = "/etc/sysconfig/virt-who"
            self.run_service(self.ssh_host(), "virt-who", "stop")
            cmd = "ls -l {0}".format(config_file)
            ret, output = self.runcmd(cmd, self.ssh_host())
            logger.info(output)
            if ret == 0 and output is not None and output != "":
                res = self.vw_msg_search(output, "-rw-------")
                results.setdefault('step1', []).append(res)
            else:
                logger.error("Failed to get virt-who file properties")
                results.setdefault('step1', []).append(False)

        logger.info(">>>step2: start virt-who to check virt-who.pid file permission")
        pid_file = "/var/run/virt-who.pid"
        self.run_service(self.ssh_host(), "virt-who", "start")
        cmd = "ls -l {0}".format(pid_file)
        ret, output = self.runcmd(cmd, self.ssh_host())
        logger.info(output)
        if ret == 0 and output is not None and output != "":
            res = self.vw_msg_search(output, "-rw-------")
            results.setdefault('step2', []).append(res)
        else:
            logger.error("Failed to get virt-who.pid properties")
            results.setdefault('step2', []).append(False)

        # case result
        self.vw_case_result(results)
