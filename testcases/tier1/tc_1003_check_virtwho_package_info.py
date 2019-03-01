# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133656")

        pkg_info = self.vw_pkg_info()
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

        # Case Result
        self.vw_case_result(results)

if __name__ == '__main__':
    unittest.main()

# ===changelog===
# - 2018/06/28 <hsun@redhat.com>
# - update step3, because the url is changed to https://github.com/candlepin/virt-who in rhel7.6
# - 2018/06/14 <hsun@redhat.com>
# - improve step 6/7
# - 2018/06/01 <shyan@redhat.com>
# - Case created and support to run against rhel6/7/8
