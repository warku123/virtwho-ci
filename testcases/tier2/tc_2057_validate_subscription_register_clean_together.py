# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136773")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        server, username, password = self.vw_hypervisor_info(mode)

        # Case Steps
        logger.info(">>>step1: start virt-who by run_service")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
        results.setdefault('step1', []).append(error_num==0)
        results.setdefault('step1', []).append(thread_num==1)

        logger.info(">>>step2: unregister, and the clean")
        cmd1 = "subscription-manager unregister"
        cmd2 = "subscription-manager clean"
        ret, output = self.runcmd(cmd1, self.ssh_host(), desc="unregister")
        time.sleep(15)
        ret, output = self.runcmd(cmd2, self.ssh_host(), desc="clean")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
        results.setdefault('step2', []).append(thread_num==1)

        logger.info(">>>step3: register, start virt-who")
        self.vw_sub_register(self.ssh_host())
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
        results.setdefault('step3', []).append(error_num==0)
        results.setdefault('step3', []).append(thread_num==1)

        logger.info(">>>step4: unregister and clean together")
        cmd1 = "subscription-manager unregister; subscription-manager clean"
        ret, output = self.runcmd(cmd1, self.ssh_host(), desc="unregister and clean")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
        results.setdefault('step4', []).append(thread_num==1)

        # Case Result
        notes = list()
        notes.append("Bug(Step4): unregister and clean together, virt-who will be killed")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1506167")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/08/01 Eko<hsun@redhat.com>
#- Case created
