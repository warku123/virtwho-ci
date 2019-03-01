# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133687")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        default_reporter_id = self.get_hostname(self.ssh_host())
        expected_reporter_id = "virtwho_reporter_id_tc1057"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info('>>>step1: Run virt-who with "debug=True"')
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info('>>>step2: Run virt-who with "debug=False"')
        self.vw_option_update_value("debug", 'False', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info('>>>step3: Run virt-who with debug option disabled')
        self.vw_option_disable("debug", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/06 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps
# - 2018/06/13 yanpliu<yanpliu@redhat.com>
# - Case created
