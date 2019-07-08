# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137110')
        hypervisor_type = self.get_config('hypervisor_type')
        register_type = self.get_config('register_type')
        if 'stage' in register_type:
            self.vw_case_skip(register_type)
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
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        ssh_sat = register_config['ssh_sat']
        default_org = 'Default_Organization'
        extra_org = 'Virtwho_Org'
        org_list = {'step1':default_org, 'step2':extra_org}

        for step, org in sorted(org_list.items(), key=lambda item:item[0]):
            logger.info(">>>{0}: run with owner={1}".format(step, org))
            host_id = self.satellite_host_id(self.ssh_host(), register_config, host_name, host_uuid)
            if 'libvirt-local' not in hypervisor_type and 'vdsm' not in hypervisor_type:
                self.vw_option_update_value('owner', org, config_file)
            if host_id is not None and host_id != "":
                self.vw_web_host_delete(host_name, host_uuid)
            if org == extra_org:
                register_config['owner'] = extra_org
            self.system_unregister(self.ssh_host())
            self.system_register(self.ssh_host(), register_type, register_config)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            if org == default_org:
                res2 = self.satellite_hosts_search(ssh_sat, register_config, default_org, host_name, host_uuid, exp_exist=True)
                res3 = self.satellite_hosts_search(ssh_sat, register_config, extra_org, host_name, host_uuid, exp_exist=False)
            else:
                res2 = self.satellite_hosts_search(ssh_sat, register_config, default_org, host_name, host_uuid, exp_exist=False)
                res3 = self.satellite_hosts_search(ssh_sat, register_config, extra_org, host_name, host_uuid, exp_exist=True)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)
            results.setdefault(step, []).append(res3)

        logger.info(">>>step finally: delete host and hypervisor from extra_org")
        host_id = self.satellite_host_id(self.ssh_host(), register_config, host_name, host_uuid)
        if host_id is not None and host_id != "":
            self.vw_web_host_delete(host_name, host_uuid)
        self.system_unregister(self.ssh_host())

        # Case Result
        self.vw_case_result(results)
