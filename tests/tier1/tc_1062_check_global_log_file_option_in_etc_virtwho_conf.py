# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-133693")
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", "True", virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()
        log_dir = "/var/log/rhsm/virtwho/"
        log_file = "/var/log/rhsm/virtwho/rhsm.log"

        # case steps
        logger.info(">>>step1: Run virt-who log_file setting in /etc/virt-who.conf")
        self.vw_option_enable("log_dir", virtwho_conf)
        self.vw_option_enable("log_file", virtwho_conf)
        self.vw_option_update_value("log_dir", log_dir, virtwho_conf)
        self.vw_option_update_value("log_file", log_file, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault("step1", []).append(res)
        ret, output = self.runcmd("ls {0}".format(log_file), self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to find file: {0}".format(log_file))
            ret, output = self.runcmd("cat {0}".format(log_file), self.ssh_host())
            d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
            d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
            if d1 is False or d2 is False:
                results.setdefault("step1", []).append(False)
        else:
            logger.error("{0} is not exist".format(log_file))
            results.setdefault("step1", []).append(False)

        # case result
        self.vw_case_result(results)
