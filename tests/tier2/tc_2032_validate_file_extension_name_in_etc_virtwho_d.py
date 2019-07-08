# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136711')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
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
        invalid_file = "/etc/virt-who.d/{0}.conf.txt".format(config_name)

        # Case Steps
        logger.info(">>>step1: run virt-who with the expected config file name")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who with the unexpected config file name")
        logger.warning("libvirt-local mode will be used to instead when no valid config")
        cmd = "mv {0} {1}".format(config_file, invalid_file)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="rename file")
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, ["Error in .* backend"], exp_exist=True)
        res3 = self.vw_msg_search(rhsm_output, "not have any .*conf.* files but is not empty", exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        # Case Result
        self.vw_case_result(results)
