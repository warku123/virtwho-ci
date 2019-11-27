# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133683')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
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
        guest_uuid = self.get_hypervisor_guestuuid()
        register_config = self.get_register_config()
        register_owner = register_config['owner']

        # case steps
        logger.info(">>>step1: Run virt-who service to check the rhsm.log")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        if register_owner in data.keys() and guest_uuid in data[register_owner].keys():
            logger.info("Succeeded to check, mapping info is specified to {0}".format(
                register_owner))
            results.setdefault('step1', []).append(True)
        else:
            logger.error("Failed to check, mapping info is not specified to {0}".format(
                register_owner))
            results.setdefault('step1', []).append(False)

        # case result
        self.vw_case_result(results)
