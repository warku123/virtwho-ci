# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133654')
        trigger_type = self.get_config('trigger_type')
        if trigger_type in ('trigger-rhev', 'trigger-brew', 'trigger-multiarch'):
            self.vw_case_skip(trigger_type)

        # case config
        results = dict()
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')

        # case steps
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

        # case result
        self.vw_case_result(results)
