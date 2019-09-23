# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-171135')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] < '0.24.6':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info('>>>step1: Run virt-who without debug"')
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res1)

        logger.info('>>>step2: Configure "print_=false" then run virt-who by cli')
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("print_", virtwho_conf)
        self.vw_option_update_value("print_", 'false', virtwho_conf)
        self.vw_stop()
        cmd = "virt-who"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=False)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info('>>>step3: Configure "print_=false" then start virt-who service')
        self.vw_stop()
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info('>>>step4: Configure "print_=true" then run virt-who by cli')
        self.vw_option_update_value("print_", 'true', virtwho_conf)
        self.vw_stop()
        cmd = "virt-who"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=0)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(tty_output, guest_uuid, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info('>>>step5: Configure "print_=true" then start virt-who service')
        self.vw_stop()
        data, tty_output, rhsm_output = self.vw_start("virt-who")
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=False)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info('>>>step6: Configure "print_=xxx" then start virt-who service')
        msg = "print_ must be a valid boolean"
        self.vw_option_update_value("print_", 'xxx', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=False)
        res3 = self.vw_msg_search(rhsm_output, msg, exp_exist=True)
        results.setdefault('step6', []).append(res1)
        results.setdefault('step6', []).append(res2)
        results.setdefault('step6', []).append(res3)

        # case result
        self.vw_case_result(results)
