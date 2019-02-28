# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137014")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/root/%s.conf" % mode.lower()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        ext_host_name, ext_host_uuid, ext_guest_uuid = self.vw_extra_mode_info(extra_mode)
        guest_uuid = self.mode_guest_uuid(mode)
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)

        # Case Steps
        logger.info(">>>step1: 'configs' is valid file")
        self.vw_option_enable('configs', virtwho_conf)
        self.vw_option_update_value('configs', conf_file, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(str(data), guest_uuid, exp_exist=True)
        res3 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=False)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)
        results.setdefault('step1', []).append(res3)

        logger.info(">>>step2: 'configs' is null value")
        self.vw_option_update_value('configs', '', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(str(data), guest_uuid, exp_exist=False)
        res3 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        logger.info(">>>step3: 'configs' is wrong value")
        self.vw_option_update_value('configs', 'xxxxxx', virtwho_conf)
        error_msg = 'Unable to read configuration file xxxxxx'
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_error=True)
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(str(data), guest_uuid, exp_exist=False)
        res3 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=True)
        res4 = self.vw_msg_search(str(data), error_msg, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)
        results.setdefault('step3', []).append(res3)
        results.setdefault('step3', []).append(res4)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
# - Case created
