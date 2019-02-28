# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136630")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
        if "stage" in server_type:
            rhsm_prefix = "/subscription"
            user, passwd, owner, env = self.stage_account_get(mode)
        else:
            rhsm_prefix = "/rhsm"
            user, passwd = self.satellite_account_get(server_ip)

        # Case Steps
        logger.info(">>>step1: run virt-who with rhsm_hostname, rhsm_port, rhsm_prefix good value")
        self.vw_option_add("rhsm_hostname", server_ip, conf_file)
        self.vw_option_add("rhsm_port", "443", conf_file)
        self.vw_option_add("rhsm_prefix", rhsm_prefix, conf_file)
        self.vw_option_add("rhsm_username", user, conf_file)
        self.vw_option_add("rhsm_password", passwd, conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who with rhsm_username=xxxxxx")
        self.vw_option_update_value("rhsm_username", "xxxxxx", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, "Communication with subscription manager failed", exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: run virt-who with rhsm_username=红帽©¥®ðπ∉")
        '''红帽©¥®ðπ∉ username is not supported by candlepin'''
        msg_list = ["codec can't decode|Communication with subscription manager failed"]
        self.vw_option_update_value("rhsm_username", "红帽©¥®ðπ∉", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: run virt-who with rhsm_username null value")
        self.vw_option_update_value("rhsm_username", " ", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(res1)

        logger.info(">>>step5: run virt-who with rhsm_username disable")
        self.vw_option_disable("rhsm_username", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step5', []).append(res1)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/10/23 Yuefliu<yuefliu@redhat.com>
#- Updated msg_list in step3
#- 2018/07/16 Eko<hsun@redhat.com>
#- Case created to validate rhsm_username
