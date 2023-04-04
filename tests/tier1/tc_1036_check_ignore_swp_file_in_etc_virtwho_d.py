# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133739")
        hypervisor_type = self.get_config("hypervisor_type")
        if hypervisor_type in ("libvirt-local"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable("[global]", "/etc/virt-who.conf")
        self.vw_option_enable("debug", "/etc/virt-who.conf")
        self.vw_option_update_value("debug", "True", "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        swap_file = "/etc/virt-who.d/.test.conf.swp"
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_etc_d_mode_create(config_name, swap_file)

        # case steps
        logger.info(">>>step1: check the swp file is ignored or not ")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(s1)
        s2 = self.vw_msg_search(rhsm_output, "test.conf.swp", exp_exist=False)
        results.setdefault("step1", []).append(s2)

        logger.info(">>>step2: check how many modes in rhsm.log")
        modes = re.findall(r'Using configuration.*\("(.*?)" mode\)', rhsm_output)
        if len(modes) == 1:
            logger.info(
                "Succeeded to check, only one mode in rhsm.log: {0}".format(modes)
            )
            results.setdefault("step2", []).append(True)
        else:
            logger.error(
                "Failed to check, the modes number is not matched: {0}".format(modes)
            )
            results.setdefault("step2", []).append(False)

        # case result
        self.vw_case_result(results)
