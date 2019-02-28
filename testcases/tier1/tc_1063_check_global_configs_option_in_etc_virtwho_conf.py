# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133690")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_file = "/tmp/vw.conf"
        conf_name = "%s_config" % mode.lower()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        if "libvirt-local" in mode:
            logger.info("Use extra mode(xen) to instead local mode")
            self.vw_extra_conf_in_d("xen", conf_file)
            host_name, host_uuid, guest_uuid = self.vw_extra_mode_info("xen")
        else:
            self.vw_etc_d_mode_create(mode, conf_name, conf_file)
            guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: Run virt-who configs setting in /etc/virt-who.conf")
        self.vw_option_enable("configs", virtwho_conf)
        self.vw_option_update_value("configs", conf_file, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
