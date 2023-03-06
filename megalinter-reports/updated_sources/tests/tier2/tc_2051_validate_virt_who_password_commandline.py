# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136708")
        self.vw_case_init()

        # Case Config
        results = dict()
        # Case Steps
        logger.info(">>>step1: run virt-who-password")
        value1 = self.vw_encrypted(r"ad\"min")
        value2 = self.vw_encrypted(r"ad\"min", "-p")
        value3 = self.vw_encrypted(r'"ad\"min"', "-p")
        value4 = self.vw_encrypted(r"ad\"min", "--password")
        value5 = self.vw_encrypted(r'"ad\"min"', "--password")
        results.setdefault("step1", []).append(
            value1 == value2 == value3 == value4 == value5
        )

        # Case Result
        self.vw_case_result(results)
