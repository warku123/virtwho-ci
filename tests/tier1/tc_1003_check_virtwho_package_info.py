# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133656')
        pkg_info = self.pkg_info(self.ssh_host(), 'virt-who')
        compose_id = self.get_config('rhel_compose')
        trigger_type = self.get_config('trigger_type')
        results = dict()

        logger.info(">>>step1: 'rpm -qi virt-who' contains valid 'Group' info")
        results.setdefault('step1', []).append(
            pkg_info.get("Group") == "System Environment/Base")

        logger.info(">>>step2: 'rpm -qi virt-who' contains valid 'License' info")
        if "RHEL-9" in compose_id:
            results.setdefault('step2', []).append(
                pkg_info.get("License") == "GPLv2+ and LGPLv3+")
        else:
            results.setdefault('step2', []).append(
                pkg_info.get("License") == "GPLv2+")

        logger.info(">>>step3: 'rpm -qi virt-who' contains valid 'URL' info")
        urls = ['https://github.com/virt-who/virt-who',
                'https://github.com/candlepin/virt-who']
        results.setdefault('step3', []).append(
            any(url in pkg_info.get("URL") for url in urls))

        logger.info(">>>step4: 'rpm -qi virt-who' contains valid 'Packager' info")
        msg = "Red Hat, Inc. <http://bugzilla.redhat.com/bugzilla>"
        results.setdefault('step4', []).append(pkg_info.get("Packager") == msg)

        logger.info(">>>step5: 'rpm -qi virt-who' contains valid 'Vendor' info")
        results.setdefault('step5', []).append(pkg_info.get("Vendor") == "Red Hat, Inc.")

        logger.info(">>>step6: 'rpm -qi virt-who' contains Signature info")
        if trigger_type in ('trigger-brew'):
            results.setdefault('step6', []).append("none" in pkg_info.get("Signature"))
        else:
            results.setdefault('step6', []).append("Key ID" in pkg_info.get("Signature"))
        logger.info(">>>step7: 'virt-who --version' to check version")
        vw_pkg = self.pkg_check(self.ssh_host(), 'virt-who')[9:15]
        logger.info("virt-who version should be {0}".format(vw_pkg))
        ret, output = self.runcmd('virt-who --version', self.ssh_host())
        logger.info("'virt-who --version' output is {0}".format(output))
        if ret == 0 and vw_pkg in output:
            results.setdefault('step7', []).append(True)
        else:
            results.setdefault('step7', []).append(False)

        # case result
        self.vw_case_result(results)
