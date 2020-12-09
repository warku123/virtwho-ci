# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136771")
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type not in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create(config_name, config_file)
        new_user ="tester"
        new_passwd = "redhat"

        # case steps
        logger.info(">>>step1: create tester account")
        cmd = "useradd {}" .format(new_user)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="useradd account")
        cmd = r'echo -e "{0}:{1}" | chpasswd' .format(new_user, new_passwd)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="change password")
        host_ip = self.ssh_host()['host']
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
        logger.info("error_num: {0}, thread_num: {1}, send_num: {2}" .format(error_num, thread_num, send_num))
        results.setdefault('step2', []).append(error_num==0)
        results.setdefault('step2', []).append(thread_num==1)
        results.setdefault('step2', []).append(send_num==1)

        # case result
        self.vw_case_result(results)
