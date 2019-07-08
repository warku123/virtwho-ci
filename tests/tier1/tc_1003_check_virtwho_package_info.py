# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133656')
        pkg_info = self.pkg_info(self.ssh_host(), 'virt-who')
        results = dict()

        logger.info(">>>step1: 'rpm -qi virt-who' contains valid 'Group' info")
        results.setdefault('step1', []).append(pkg_info.get("Group") == "System Environment/Base")

        logger.info(">>>step2: 'rpm -qi virt-who' contains valid 'License' info")
        results.setdefault('step2', []).append(pkg_info.get("License") == "GPLv2+")

        logger.info(">>>step3: 'rpm -qi virt-who' contains valid 'URL' info")
        urls = ['https://github.com/virt-who/virt-who', 'https://github.com/candlepin/virt-who']
        results.setdefault('step3', []).append(any(url in pkg_info.get("URL") for url in urls))

        logger.info(">>>step4: 'rpm -qi virt-who' contains valid 'Packager' info")
        results.setdefault('step4', []).append(pkg_info.get("Packager") == "Red Hat, Inc. <http://bugzilla.redhat.com/bugzilla>")

        logger.info(">>>step5: 'rpm -qi virt-who' contains valid 'Vendor' info")
        results.setdefault('step5', []).append(pkg_info.get("Vendor") == "Red Hat, Inc.")

        logger.info(">>>step6: 'rpm -qi virt-who' contains valid 'RSA/SHA256' info")
        results.setdefault('step6', []).append("RSA/SHA256" in pkg_info.get("Signature"))

        logger.info(">>>step7: 'rpm -qi virt-who' contains valid 'Key ID' info")
        results.setdefault('step7', []).append("Key ID" in pkg_info.get("Signature"))

        # case result
        self.vw_case_result(results)
