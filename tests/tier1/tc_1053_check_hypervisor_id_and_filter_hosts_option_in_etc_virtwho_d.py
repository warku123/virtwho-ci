# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133709')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()
        host_hwuuid = self.get_hypervisor_hwuuid()
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        register_type = register_config['type']
        register_owner = register_config['owner']
        if "esx" in hypervisor_type or "rhevm" in hypervisor_type:
            steps = {'step1':'uuid', 'step2':'hostname', 'step3':'hwuuid'}
        else:
            steps = {'step1':'uuid', 'step2':'hostname'}

        # case steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to with hypervisor_id={1} and set filter_hosts".format(step, option))
            self.vw_option_add("hypervisor_id", option, filename=config_file)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
            else:
                hypervisorId = host_uuid
            self.vw_option_add("filter_hosts", hypervisorId, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            hypervisor_num = data[register_owner]['hypervisor_num']
            if hypervisorId in data[register_owner].keys() and hypervisor_num == 1:
                logger.info("Succeeded to search, {0} hypervisorId({1}) found".format(hypervisor_num, hypervisorId))
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to search, {0} hypervisorId({1}) found".format(hypervisor_num, hypervisorId))
                results.setdefault(step, []).append(False)
            self.vw_option_del("hypervisor_id", filename=config_file)
            self.vw_option_del("filter_hosts", filename=config_file)
            if "satellite" in register_type:
                self.vw_web_host_delete(host_name, hypervisorId)
        if "stage" in register_type:
            self.stage_consumer_clean(self.ssh_host(), register_config)

        # case result
        self.vw_case_result(results)
