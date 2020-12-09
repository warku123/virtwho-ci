# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134082')
        hypervisor_type = self.get_config('hypervisor_type')
        trigger_type = self.get_config('trigger_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if "trigger-rhel" not in trigger_type:
            self.vw_case_skip(trigger_type)
        self.vw_case_init()

        # case config
        results = dict()
        conf_etc = "/etc/virt-who.conf"
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)

        # case steps
        logger.info(">>>step1: create virt-who config")
        self.vw_option_enable('[global]', conf_etc)
        self.vw_option_enable('debug', conf_etc)
        self.vw_option_update_value('debug', 'True', conf_etc)
        self.vw_option_enable("interval", filename=conf_etc)
        self.vw_option_update_value("interval", '60', filename=conf_etc)

        logger.info("setting options in /etc/virt-who.d/")
        self.vw_etc_d_mode_create(config_name, config_file)
        
        logger.info(">>>step2: start virt-who service to check")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_looptime=60)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: start to reboot virt-who host")
        self.system_reboot(self.ssh_host())

        logger.info(">>>step4: start virt-who service to check again")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_looptime=60)
        res2 = self.vw_msg_search(output=rhsm_output, msg="\[.*DEBUG\]", exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        # case result
        self.vw_case_result(results)

