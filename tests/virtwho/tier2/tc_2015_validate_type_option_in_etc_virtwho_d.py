# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136586')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'libvirt-local':
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        option_tested = "type"
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        logger.info(">>>step1: type option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: type option is wrong value")
        self.vw_option_update_value(option_tested, "xxxxxx", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["virt-who can't be started"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: type option is 红帽€467aa value")
        self.vw_option_update_value(option_tested, '红帽€467aa', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["virt-who can't be started"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: type option is null value")
        self.vw_option_update_value(option_tested, '', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["virt-who can't be started"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=0, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: type option is disable")
        logger.warning("libvirt-local mode will be used to instead when type option is disabled")
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["Error in .* backend"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info(">>>step6: type option is disable but another config is ok")
        logger.warning("libvirt-local mode will be used to instead when type option is disabled")
        config_name_ok = "virtwho-config-ok"
        config_file_ok = "/etc/virt-who.d/{0}.conf".format(config_name_ok)
        self.vw_etc_d_mode_create(config_name_ok, config_file_ok)
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["Error in .* backend"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step6', []).append(res1)
        results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: type option is null but another config is ok")
        logger.warning("invalid config will be ignored, and run the valid config normally")
        self.vw_option_enable(option_tested, config_file)
        self.vw_option_update_value(option_tested, '', config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step7', []).append(res1)

        # Case Result
        self.vw_case_result(results)
