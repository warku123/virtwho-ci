# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133740")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        ext_host_name, ext_host_uuid, ext_guest_uuid = self.vw_extra_mode_info(extra_mode)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: create a extra hypervisors in virt-who.d and run cli -d")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        cmd = "virt-who -d"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check mapping info included two hypervisors")
        res1 = self.vw_msg_search(str(data), guest_uuid, exp_exist=True)
        res2 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/07/03 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/22 yanpliu<yanpliu@redhat.com>
# - update vw_extra_conf_in_d interface invoke
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps, remove else
# - 2018/06/12 yanpliu<yanpliu@redhat.com>
# - Case created
