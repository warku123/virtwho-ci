# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133706")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        password = "redhat"

        # Case Steps
        encrypt_1 = self.vw_encrypted(password)
        encrypt_2 = self.vw_encrypted(password, option="-p")
        encrypt_3 = self.vw_encrypted(password, option="--password")
        if encrypt_1 == encrypt_2 == encrypt_3:
            results.setdefault("step ", []).append(True)
        else:
            results.setdefault("step", []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/13 Eko<hsun@redhat.com>
#- Case created to validate virt-who-password option
