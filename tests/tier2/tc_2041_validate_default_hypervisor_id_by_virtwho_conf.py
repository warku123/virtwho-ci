# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136731')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_enable("[defaults]", virtwho_conf)
        self.vw_option_enable("hypervisor_id", virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        register_type = register_config['type']
        register_owner = register_config['owner']

        # Case Steps
        logger.info(">>>step: hypervisor_id in /etc/virt-who.d/x.conf has high priority")
        self.vw_option_update_value('hypervisor_id', 'uuid', virtwho_conf)
        self.vw_option_add('hypervisor_id', 'hostname', config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step', []).append(res)
        if host_name in data[register_owner].keys():
            logger.info("Succeeded to search hypervisorId:{0}".format(host_name))
            results.setdefault('step', []).append(True)
        else:
            logger.error("Failed to search hypervisorId:{0}".format(host_name))
            results.setdefault('step', []).append(False)
        if "satellite" in register_type:
            self.vw_web_host_delete(host_name, host_uuid)
        if "stage" in register_type:
            self.stage_consumer_clean(self.ssh_host(), register_config)

        # Case Result
        self.vw_case_result(results)