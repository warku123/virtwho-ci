# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133738")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        self.ssh_no_passwd_access(self.ssh_guest(), self.ssh_host())
        host = host_ip
        port = 22
        if ":" in host_ip:
            var = host_ip.split(':')
            host = var[0]
            port = int(var[1])

        # Case Steps
        logger.info(">>>step1: ssh restart virt-who and check status")
        cmd = "ssh %s -p %s 'service virt-who restart'" % (host, port)
        ret, output = self.runcmd(cmd, self.ssh_guest(), desc="ssh run virt-who restart")
        if self.vw_service_status() == "running":
            logger.info("Succeeded to restart virt-who by ssh")
            results.setdefault('step1', []).append(True)
        else:
            logger.error("Failed to restart virt-who by ssh")
            results.setdefault('step1', []).append(False)

        logger.info(">>>step2: ssh stop virt-who and check status")
        cmd = "ssh %s -p %s 'service virt-who stop'" % (host, port)
        ret, output = self.runcmd(cmd, self.ssh_guest(), desc="ssh run virt-who stop")
        if self.vw_service_status() != "running":
            logger.info("Succeeded to stop virt-who by ssh")
            results.setdefault('step2', []).append(True)
        else:
            logger.error("Failed to stop virt-who by ssh")
            results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/06/07 yuefliu<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
# - 2018/06/14 Eko<hsun@redhat.com>
# - stop and start virt-who by ssh, add port option for ssh
