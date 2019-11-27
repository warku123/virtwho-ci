# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134056')
        hypervisor_type = self.get_config('hypervisor_type')
        register_config = self.get_register_config()
        register_type = register_config['type']
        register_owner = register_config['owner']
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if "satellite62" in register_type:
            self.vw_case_skip(register_type)
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
        host_uuid = self.get_hypervisor_hostuuid()

        # case steps
        logger.info(">>>step1: Run virt-who servie to check hypervisor's facts")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        facts = data[register_owner][host_uuid]
        results.setdefault('step1', []).append(res)
        results.setdefault('step1', []).append(data['is_async'] == "hypervisors_async")
        results.setdefault('step1', []).append('type' in facts.keys())
        results.setdefault('step1', []).append('version' in facts.keys())
        results.setdefault('step1', []).append('socket' in facts.keys())
        logger.info("hypervisor.type: {0} ".format(facts['type']))
        logger.info("cpu.cpu_socket(s): {0}".format(facts['socket']))
        logger.info("hypervisor.version: {0}".format(facts['version']))

        # case result
        self.vw_case_result(results)
