# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134108")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        host_uuid = self.mode_host_uuid(mode)
        guest_uuid = self.mode_guest_uuid(mode)
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who by cli")
        cmd = "virt-who -d"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/06 Yuefen<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
# - 2018/06/14 Eko<hsun@redhat.com>
# - update step2, use vw_rhsm_associate to instead
