# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: virt-who package can be installed/unstalled
        :Polarion_Id: RHEL-133654
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        trigger_type = config.virtwho.trigger_type
        if "trigger-rhev" in trigger_type:
            self.vw_case_skip("skipped - this case is not avaialbe for {0}".format(trigger_type))

        # Case Config
        results = dict()
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')

        # Case Steps
        # If the virt-who package is installed
        if pkg:
            logger.info(">>>step1: uninstall virt-who package and verify it was removed")
            res = self.pkg_uninstall(self.ssh_host(), 'virt-who')
            results.setdefault('step1', []).append(res)

            logger.info(">>>step2: install virt-who package and verify it was installed")
            res = self.pkg_install(self.ssh_host(), 'virt-who')
            results.setdefault('step2', []).append(res)
        # The virt-who package is not installed
        else:
            logger.info(">>>step1: install virt-who package and verify it was installed")
            res = self.pkg_install(self.ssh_host(), 'virt-who')
            results.setdefault('step1', []).append(res)
            logger.info(">>>step2: uninstall virt-who package and verify it was removed")
            res = self.pkg_uninstall(self.ssh_host(), 'virt-who')
            results.setdefault('step2', []).append(res)

        logger.info(">>>step3: at last, make sure virt-who package is installed")
        if self.pkg_check(self.ssh_host(), 'virt-who') is False:
            res = self.pkg_install(self.ssh_host(), 'virt-who')
            results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
