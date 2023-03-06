# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133734")
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: restart virt-who service to keep it running")
        self.run_service(self.ssh_host(), "virt-who", "restart")
        if self.vw_service_status() == "running":
            results.setdefault("step1", []).append(True)
        else:
            logger.error("Failed to start virt-who")
            results.setdefault("step1", []).append(False)

        logger.info(">>>step2: run virt-who by cli, will failed as 'already running'")
        cmd = "virt-who"
        ret, output = self.runcmd(cmd, self.ssh_host())
        if "already running" in output:
            logger.info("Succeeded to check, return 'already running' as expected")
            results.setdefault("step2", []).append(True)
        else:
            logger.error("Failed to check, not return 'already running'")
            results.setdefault("step2", []).append(False)

        # case result
        self.vw_case_result(results)
