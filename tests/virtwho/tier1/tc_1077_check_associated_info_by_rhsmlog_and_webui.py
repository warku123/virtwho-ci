# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134063')
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info(">>>step1: run virt-who service")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: check host-to-guest association in webui")
        res = self.vw_web_associate(host_name, host_uuid, guest_name, guest_uuid)
        results.setdefault('step3', []).append(res)

        # case result
        notes = list()
        notes.append("Bug(Step3):  Missing h/g association in satellite webUI")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1644969")
        self.vw_case_result(results, notes)
