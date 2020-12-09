# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136731')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        logger.info(">>>step1: interval is null value in /etc/virt-who.conf")
        self.vw_option_enable("interval", virtwho_conf)
        self.vw_option_update_value("interval", '', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check virt-who firstly run interval in /etc/sysconfig/virt-who")
        self.vw_option_update_value("interval", '120', virtwho_conf)
        self.vw_option_enable("VIRTWHO_INTERVAL", '/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', '/etc/sysconfig/virt-who')
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step2', []).append(res)

        # Case Result
        notes = list()
        notes.append("Bug(Step1): failed to report mappings if configure 'interval=' value to null")
        notes.append("BZ: https://bugzilla.redhat.com/show_bug.cgi?id=1523482")
        self.vw_case_result(results, notes)
