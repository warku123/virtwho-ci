# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136588")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        option_tested = "env"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: env option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: env option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxxx", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env.*differs|env.* is different|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: env option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, '红帽€467aa', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["codec can't decode|Communication with subscription manager failed|env.*differs"]
        res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: env option is null value")
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env not in|env.* not set|virt-who can't be started|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: env option is disable")
        self.vw_option_disable(option_tested, conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env not in|env.* not set|virt-who can't be started|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info(">>>step6: env option is disable but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_disable(option_tested, conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["env not in|env.* not set|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step6', []).append(res1)
        results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: env option is null but another config is ok")
        self.vw_extra_conf_in_d(extra_mode, extra_file)
        self.vw_option_enable(option_tested, conf_file)
        self.vw_option_update_value(option_tested, '', conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["env not in|env.* not set|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step7', []).append(res1)
        results.setdefault('step7', []).append(res2)

        # Case Result
        notes = list()
        if "stage" in server_type:
            notes.append("Bug(Step2,Step3,Step4,Step7): Set env to wrong or special or null value, still can sent report normally for stage")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530426")
        else:
            notes.append("Bug(Step4,Step7): Set env to null value, still can sent report normally for sat62/sat63")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530290")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/10/22 Yuefliu<yuefliu@redhat.com>
#- Updated msg_list in step3
#- 2018/07/18 Eko<hsun@redhat.com>
#- Case created to validate env option
