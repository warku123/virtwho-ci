# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133731")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        ext_host_name, ext_host_uuid, ext_guest_uuid = self.vw_extra_mode_info(extra_mode)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: create two config files for two different hypervisors")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
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
# - 2018/07/03 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/22 yanpliu<yanpliu@redhat.com>
# - update vw_extra_conf_in_d interface invoke
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps
# - 2018/06/12 yanpliu<yanpliu@redhat.com>
# - Case created to validate create two config files with two different hypervisors by virt-who.d
