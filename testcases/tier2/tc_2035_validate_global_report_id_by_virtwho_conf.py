# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136716")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        reporter_id_null = ''
        reporter_id_non_ascii = '红帽©¥®ðπ∉'
        steps = {'step1':reporter_id_null, 'step2':reporter_id_non_ascii}

        # Case Steps
        for step, value in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check reporter_id(%s)" % (step, value))
            self.vw_option_enable("reporter_id", virtwho_conf)
            self.vw_option_update_value("reporter_id", value, virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            if value in data['reporter_id']:
                logger.info("Succeeded to check, the reporter_id(%s) is expected" % data['reporter_id'])
                results.setdefault(step, []).append(True)
            else:
                logger.info("Failed to check, the reporter_id(%s) is not expected" % data['reporter_id'])
                results.setdefault(step, []).append(False)

        # Case Result
        notes = list()
        notes.append("Bug(step1): virt-who still uses null value for reporter_id to report")
        notes.append("BZ: https://bugzilla.redhat.com/show_bug.cgi?id=1523067")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
# - Case created
