# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136771")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" not in mode and "vdsm" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        new_user ="tester"
        new_passwd = "redhat" 

        # Case Steps
        logger.info(">>>step1: create tester account")
        cmd = "useradd %s" % new_user
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="useradd account")
        cmd = r'echo -e "%s:%s" | chpasswd' % (new_user, new_passwd)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="change password")
        host_ip = self.get_exported_param("VIRTWHO_HOST_IP")
        new_ssh = {"host": host_ip, "username": new_user, "password": new_passwd}
        ret, output = self.runcmd("rpm -qa kernel", new_ssh, desc="ssh connect check")
        if ret == 0 and "kernel" in output:
            logger.info("Succeeded to create tester account")
            results.setdefault('step1', []).append(True)
        else:
            logger.error("Failed to create tester account")
            results.setdefault('step1', []).append(False)

        logger.info(">>>step2: run virt-who service by tester account")
        self.vw_thread_clean()
        attrs = ["Password:|redhat"]
        ret, output = self.run_expect(new_ssh, "/sbin/service virt-who restart", attrs)
        time.sleep(60)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        send_num = self.vw_callback_send_num()
        logger.info("error_num: %s, thread_num: %s, send_num: %s" %(error_num, thread_num, send_num))
        results.setdefault('step2', []).append(error_num==0)
        results.setdefault('step2', []).append(thread_num==1)
        results.setdefault('step2', []).append(send_num==1)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/08/02 Eko<hsun@redhat.com>
#- Case created
