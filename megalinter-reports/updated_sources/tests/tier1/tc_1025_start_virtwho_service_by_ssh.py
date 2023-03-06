# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133738")
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.ssh_no_passwd_access(self.ssh_guest(), self.ssh_host())
        host = self.ssh_host()["host"]
        port = 22
        if ":" in host:
            var = host.split(":")
            host = var[0]
            port = int(var[1])

        # case steps
        logger.info(">>>step1: ssh restart virt-who and check status")
        cmd = "ssh {0} -p {1} 'service virt-who restart'".format(host, port)
        ret, output = self.runcmd(cmd, self.ssh_guest())
        if self.vw_service_status() == "running":
            logger.info("Succeeded to restart virt-who by ssh")
            results.setdefault("step1", []).append(True)
        else:
            logger.error("Failed to restart virt-who by ssh")
            results.setdefault("step1", []).append(False)

        logger.info(">>>step2: ssh stop virt-who and check status")
        cmd = "ssh {0} -p {1} 'service virt-who stop'".format(host, port)
        ret, output = self.runcmd(cmd, self.ssh_guest())
        if self.vw_service_status() != "running":
            logger.info("Succeeded to stop virt-who by ssh")
            results.setdefault("step2", []).append(True)
        else:
            logger.error("Failed to stop virt-who by ssh")
            results.setdefault("step2", []).append(False)

        # case result
        self.vw_case_result(results)
