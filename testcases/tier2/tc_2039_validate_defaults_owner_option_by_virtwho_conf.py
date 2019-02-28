# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136727")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_enable("[defaults]", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: disable owner option in /etc/virt-who.d/, set correct owner in /etc/virt-who.conf")
        self.vw_option_disable("owner", conf_file)
        self.vw_option_enable("owner", virtwho_conf)
        self.vw_option_update_value("owner", owner, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res1)

        logger.info(">>>step2: disable owner option in /etc/virt-who.d/, set owner=xxxxxx in /etc/virt-who.conf")
        self.vw_option_update_value("owner", "xxxxxx", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner.* is different|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: disable owner option in /etc/virt-who.d/, set owner=红帽©¥®ðπ∉ in /etc/virt-who.conf")
        self.vw_option_update_value("owner", "红帽©¥®ðπ∉", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["codec can't decode|codec can't encode|Communication with subscription manager failed|owner.* is different"]
        res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: disable owner option in /etc/virt-who.d/, set owner= in /etc/virt-who.conf")
        self.vw_option_update_value("owner", "", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner not in|owner.* not set|virt-who can't be started|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: correct owner in /etc/virt-who.conf, but wrong owner in /etc/virt-who.d/ config file")
        self.vw_option_update_value("owner", owner, virtwho_conf)
        self.vw_option_enable("owner", conf_file)
        self.vw_option_update_value("owner", "xxxxxx", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner.* is different|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        notes = list()
        if "satellite62" in server_type:
            notes.append("Bug(Step4): set owner to null, still can sent report normally")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1516173")
        self.vw_case_result(results, notes)

if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/10/23 Yuefliu<yuefliu@redhat.com>
#- Updated msg_list in step3
# - 2018/07/30 Eko<hsun@redhat.com>
# - create cases
