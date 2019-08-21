# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136585')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        option_tested = "[.*]"
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        vw_pkg = self.pkg_check(self.ssh_host(), 'virt-who')
        msg_list = ["no section headers|"
                    "Error in .* backend|"
                    "do not have any valid section headers"]

        # Case Steps
        logger.info(">>>step1: header option is good value")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: header option is space value")
        self.vw_option_update_name(option_tested, "[ ]", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if vw_pkg[9:15] >= '0.25.7':
            res1 = self.op_normal_value(data, exp_error=2, exp_thread=0, exp_send=0)
            res2 = self.msg_validation(rhsm_output, msg_list)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
        else:
            logger.warning("Sapce value[ ] is acceptable for header option")
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res1)

        logger.info(">>>step3: header option is 红帽€467aa value")
        logger.info("Special value is acceptable for header option")
        self.vw_option_update_name(option_tested, '[红帽€467aa]', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res1)

        logger.info(">>>step4: header option is null value")
        self.vw_option_update_name(option_tested, '[]', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if vw_pkg[9:15] >= '0.25.7':
            res1 = self.op_normal_value(data, exp_error=3, exp_thread=0, exp_send=0)
        else:
            logger.warning(
                "libvirt-local mode will be used to instead when header option is null")
            res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: header option is disable")
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        if vw_pkg[9:15] >= '0.25.7':
            res1 = self.op_normal_value(data, exp_error=3, exp_thread=0, exp_send=0)
        else:
            logger.warning(
                "libvirt-local mode will be used when run without header option")
            res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        logger.info(">>>step6: owner option is disable but another config is ok")
        config_name_ok = "virtwho-config-ok"
        config_file_ok = "/etc/virt-who.d/{0}.conf".format(config_name_ok)
        self.vw_etc_d_mode_create(config_name_ok, config_file_ok)
        self.vw_option_disable(option_tested, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["no section headers"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list)
        results.setdefault('step6', []).append(res1)
        results.setdefault('step6', []).append(res2)

        logger.info(">>>step7: owner option is null but another config is ok")
        self.vw_option_enable(option_tested, config_file)
        self.vw_option_update_name(option_tested, '[]', config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_error=True)
        msg_list = ["no section headers"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=1)
        res2 = self.msg_validation(rhsm_output, msg_list)
        results.setdefault('step7', []).append(res1)
        results.setdefault('step7', []).append(res2)

        # Case Result
        self.vw_case_result(results)
