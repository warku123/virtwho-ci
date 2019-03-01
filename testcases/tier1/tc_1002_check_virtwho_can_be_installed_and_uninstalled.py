# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133654")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        trigger_name = self.get_exported_param("TRIGGER_NAME")
        if "trigger-rhev" in trigger_name:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % trigger_name)

        # Case Config
        results = dict()
        pkg = self.vw_pkg_check()

        # Case Steps
        # If the virt-who package is installed
        if pkg != "":
            logger.info(">>>step1: uninstall virt-who package and verify it was removed")
            res = self.vw_pkg_uninstall()
            results.setdefault('step1', []).append(res)

            logger.info(">>>step2: install virt-who package and verify it was installed")
            res = self.vw_pkg_install()
            results.setdefault('step2', []).append(res)
        # The virt-who package is not installed
        else:
            logger.info(">>>step1: install virt-who package and verify it was installed")
            res = self.vw_pkg_install()
            results.setdefault('step1', []).append(res)
            logger.info(">>>step2: uninstall virt-who package and verify it was removed")
            res = self.vw_pkg_uninstall()
            results.setdefault('step2', []).append(res)

        logger.info(">>>step3: at last, make sure virt-who package is installed")
        if self.vw_pkg_check() == "":
            res = self.vw_pkg_install()
            results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

# ===changelog===
# - 2018/06/01 <shyan@redhat.com>
# - Case created and support to run against rhel6/7/8
# - 2018/06/13 Eko<hsun@redhat.com>
# - improve case steps
