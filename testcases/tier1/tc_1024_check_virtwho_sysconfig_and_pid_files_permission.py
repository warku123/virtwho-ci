# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133736")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        pid_file = "/var/run/virt-who.pid"

        # Case Steps
        logger.info(">>>step1: stop virt-who to check virt-who file permission")
        self.run_service(self.ssh_host(), "virt-who", "stop")
        cmd = "ls -l %s" % config_file
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="get virt-who file properties")
        logger.info(output)
        if ret == 0 and output is not None and output != "":
            res = self.vw_msg_search(output, "-rw-------")
            results.setdefault('step1', []).append(res)
        else:
            logger.error("Failed to get virt-who file properties")
            results.setdefault('step1', []).append(False)

        logger.info(">>>step2: start virt-who to check virt-who.pid file permission")
        self.run_service(self.ssh_host(), "virt-who", "start")
        cmd = "ls -l %s" % pid_file
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="get virt-who.pid properties")
        logger.info(output)
        if ret == 0 and output is not None and output != "":
            res = self.vw_msg_search(output, "-rw-------")
            results.setdefault('step2', []).append(res)
        else:
            logger.error("Failed to get virt-who.pid properties")
            results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/06/07 yuefliu<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
