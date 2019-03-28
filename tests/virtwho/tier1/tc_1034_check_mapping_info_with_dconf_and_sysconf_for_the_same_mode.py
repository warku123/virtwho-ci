# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133735')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info(">>>step1: enable mode in /etc/sysconfig/virt-who and config same mode in /etc/virt-who.d/")
        self.vw_etc_sys_mode_enable()
        self.vw_etc_d_mode_create(config_name, config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check mapping info duplicated or not")
        register_config = self.get_register_config()
        register_type = register_config['type']
        num = rhsm_output.count('"guestId": "{0}"'.format(guest_uuid))
        logger.info("Actual mapping info num: {0}".format(num))
        if "satellite62" in register_type:
            logger.info("Expected mapping info num: 1 for sat62")
            results.setdefault('step2', []).append(num == 1)
        else:
            logger.info("Expected mapping info num: 2 for sat63 above and stage")
            results.setdefault('step2', []).append(num == 2)

        # case result
        self.vw_case_result(results)
