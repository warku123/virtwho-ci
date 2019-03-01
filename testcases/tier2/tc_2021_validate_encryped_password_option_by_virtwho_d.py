# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136592")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        msg_list = '"encrypted_password" cannot be decrypted|'
        server, username, password = self.vw_hypervisor_info(mode)
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
        encrypted_pwd_null = ''
        encrypted_pwd_wrong = 'xxxxxx'
        steps = {'step2': encrypted_pwd_null, 'step3': encrypted_pwd_wrong}

        # Case Steps
        logger.info(">>>step1: encrypted_password is good value")
        encrypted_pwd = self.vw_encrypted(password, "-p")
        self.vw_option_disable("password", filename=conf_file)
        self.vw_option_add("encrypted_password", encrypted_pwd, filename=conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        
        for step, value in sorted(steps.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who with encrypted_password='%s'" % (step, value))
            self.vw_option_update_value("encrypted_password", '%s' % value, conf_file)
            if mode == 'libvirt-remote':
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res2 = 'True'
            else:
                data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
                res1 = self.op_normal_value(data, exp_error='1|2', exp_thread=0, exp_send=0)
                res2 = self.vw_msg_search(rhsm_output, msg_list, exp_exist=True)
            logger.info(">>>add another valid extra config")
            self.vw_extra_conf_in_d(extra_mode, extra_file)
            if mode == 'libvirt-remote':
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res4 = 'True'
            else:
                data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_error=True)
                res3 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=1)
                res4 = self.vw_msg_search(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('%s' % step, []).append(res1)
            results.setdefault('%s' % step, []).append(res2)
            results.setdefault('%s' % step, []).append(res3)
            results.setdefault('%s' % step, []).append(res4)
            self.fd_delete(self.ssh_host(), extra_file)

        # Case Result
        notes = list()
        if "libvirt" not in mode:
            notes.append("Bug(step3): Failed to run valid hypervisors if configure one hypervisor with wrong encrypted_password")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1641953")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/18 Yuefen<yuefliu@redhat.com>