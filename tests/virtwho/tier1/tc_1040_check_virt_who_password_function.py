# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133706')
        self.vw_case_init()

        # case config
        results = dict()
        password = "redhat"

        # case steps
        encrypt_1 = self.vw_encrypted(password)
        encrypt_2 = self.vw_encrypted(password, option="-p")
        encrypt_3 = self.vw_encrypted(password, option="--password")
        if encrypt_1 == encrypt_2 == encrypt_3:
            results.setdefault("step ", []).append(True)
        else:
            results.setdefault("step", []).append(False)

        # case result
        self.vw_case_result(results)
