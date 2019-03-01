# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136708")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        # Case Steps
        logger.info(">>>step1: run virt-who-password")
        value1 = self.vw_encrypted(r'ad\"min')
        value2 = self.vw_encrypted(r'ad\"min', "-p")
        value3 = self.vw_encrypted(r'"ad\"min"', "-p")
        value4 = self.vw_encrypted(r'ad\"min', "--password")
        value5 = self.vw_encrypted(r'"ad\"min"', "--password")
        results.setdefault('step1', []).append(value1==value2==value3==value4)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/31 Eko<hsun@redhat.com>
#- Case created
