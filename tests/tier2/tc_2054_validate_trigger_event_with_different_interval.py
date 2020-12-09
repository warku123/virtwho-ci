# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136726")
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '1.31.0':
            self.vw_case_skip("virt-who version")
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type != 'esx':
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        virt_config = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG",virt_config)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', virt_config)
        self.vw_option_enable("VIRTWHO_INTERVAL", virt_config)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        try:
            logger.info(">>>step1: run virt-who with event(guest_suspend) for interval 60")
            self.vw_option_update_value("VIRTWHO_INTERVAL", '60', virt_config)
            data, tty_output, rhsm_output = self.vw_start(exp_send=2, event="guest_suspend")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=2, exp_interval=60)
            results.setdefault('step1', []).append(res1)
        except:
            results.setdefault('step1', []).append(False)
            pass
        finally:
            logger.info(">>>step2: run virt-who with event(guest_resume) for interval 120")
            self.vw_option_update_value("VIRTWHO_INTERVAL", '120', filename="/etc/sysconfig/virt-who")
            data, tty_output, rhsm_output = self.vw_start(exp_send=2, event="guest_resume")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=2, exp_interval=120)
            results.setdefault('step2', []).append(res1)

        # case result
        self.vw_case_result(results)
