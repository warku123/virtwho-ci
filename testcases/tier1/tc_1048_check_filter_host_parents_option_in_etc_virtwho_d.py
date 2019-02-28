# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133702")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "esx" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        host_uuid = self.mode_host_uuid(mode)
        host_hwuuid = self.mode_host_hwuuid(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who with filter_host_parents=*")
        self.vw_option_add("filter_host_parents", "*", filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step1', []).append(s2)
        domain_id = re.findall(r"Skipping host '%s' because its parent '(.*?)'" % host_hwuuid, rhsm_output)[-1]
        logger.info("Succeeded to find: %s:%s:%s" % (host_hwuuid, domain_id, host_uuid))

        logger.info(">>>step2: run virt-who with filter_host_parents=[domain_id]")
        self.vw_option_update_value("filter_host_parents", domain_id, filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step2', []).append(s2)

        logger.info(">>>step3: run virt-who with filter_host_parents=")
        self.vw_option_update_value("filter_host_parents", "", filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step3', []).append(s2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/13 Eko<hsun@redhat.com>
#- Case created to validate filter_host_parents option
