# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136781")
        hypervisor_type = self.get_config('hypervisor_type')
        if "rhevm" not in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        virt_config = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", virt_config)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', virt_config)
        self.vw_etc_d_mode_create(config_name, config_file)
        config = self.get_hypervisor_config()
        hypervisor_server = config['server']

        # case steps
        logger.info(">>>step1: run virt-who for rhevm with ovirt-engine")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who for rhevm with ovirt-engine/")
        self.vw_option_update_value("server", hypervisor_server+'/', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: run virt-who for rhevm without /ovirt-engine")
        self.vw_option_update_value("server", hypervisor_server.rstrip('/ovirt-engine'), config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res)

        # case result
        self.vw_case_result(results)