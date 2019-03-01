# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133734")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        self.vw_etc_sys_mode_enable(mode)
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: restart virt-who service to keep it running")
        self.run_service(self.ssh_host(), "virt-who", "restart")
        if self.vw_service_status() == "running":
            results.setdefault('step1', []).append(True)
        else:
            logger.error("Failed to start virt-who")
            results.setdefault('step1', []).append(False)

        logger.info(">>>step2: run virt-who by cli, will failed as 'already running'")
        cmd = "virt-who"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="run virt-who by cli")
        if "already running" in output:
            logger.info("Succeeded to check, return 'already running' as expected")
            results.setdefault('step2', []).append(True)
        else:
            logger.error("Failed to check, not return 'already running'")
            results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/06 yuefliu<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
