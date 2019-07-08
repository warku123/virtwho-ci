# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136592')
        config = self.get_hypervisor_config()
        hypervisor_type = config['type']
        hypervisor_password = config['password']
        if hypervisor_type in ('libvirt-local', 'vdsm', 'kubevirt'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        msg_list = '"encrypted_password" cannot be decrypted|'
        encrypted_pwd_null = ''
        encrypted_pwd_wrong = 'xxxxxx'
        steps = {'step2': encrypted_pwd_null, 'step3': encrypted_pwd_wrong}

        # Case Steps
        logger.info(">>>step1: encrypted_password is good value")
        encrypted_pwd = self.vw_encrypted(hypervisor_password, "-p")
        self.vw_option_disable("password", filename=config_file)
        self.vw_option_add("encrypted_password", encrypted_pwd, filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        
        for step, value in sorted(steps.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who with encrypted_password='%s'" % (step, value))
            self.vw_option_update_value("encrypted_password", '%s' % value, config_file)
            if 'libvirt-remote' in hypervisor_type:
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res2 = 'True'
            else:
                data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
                res1 = self.op_normal_value(data, exp_error='1|2', exp_thread=0, exp_send=0)
                res2 = self.vw_msg_search(rhsm_output, msg_list, exp_exist=True)
            logger.info(">>>add another valid extra config")
            config_name_ok = "virtwho-config-ok"
            config_file_ok = "/etc/virt-who.d/{0}.conf".format(config_name_ok)
            self.vw_etc_d_mode_create(config_name_ok, config_file_ok)
            if 'libvirt-remote' in hypervisor_type:
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                res4 = 'True'
            else:
                data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_error=True)
                res3 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=1)
                res4 = self.vw_msg_search(rhsm_output, msg_list, exp_exist=True)
            results.setdefault('{0}'.format(step), []).append(res1)
            results.setdefault('{0}'.format(step), []).append(res2)
            results.setdefault('{0}'.format(step), []).append(res3)
            results.setdefault('{0}'.format(step), []).append(res4)
            self.fd_delete(self.ssh_host(), config_file_ok)

        # Case Result
        self.vw_case_result(results)
