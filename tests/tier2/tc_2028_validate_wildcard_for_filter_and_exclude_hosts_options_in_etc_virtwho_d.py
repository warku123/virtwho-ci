# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136635')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        register_type = register_config['type']
        host_uuid = self.get_hypervisor_hostuuid()
        host_hwuuid = self.get_hypervisor_hwuuid()
        host_name = self.get_hypervisor_hostname()
        if "esx" in hypervisor_type or "rhevm" in hypervisor_type:
            steps = {'step1':'uuid', 'step2':'hostname', 'step3':'hwuuid'}
        else:
            steps = {'step1':'uuid', 'step2':'hostname'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to with hypervisor_id={1} and set filter_hosts".format(step, option))
            self.vw_option_add("hypervisor_id", option, config_file)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
            else:
                hypervisorId = host_uuid
            wildcard = hypervisorId[:3] + '*' + hypervisorId[4:]
            sub_steps = {'step1':hypervisorId, 'step2': "*", 'step3': wildcard, 'step4': wildcard}
            for key, value in sorted(sub_steps.items(),key=lambda item:item[0]):
                if key == "step4":
                    logger.info("++++ Set filter_hosts=* and exclude_hosts=%s ++++" % value)
                    self.vw_option_add("filter_hosts", "*", config_file)
                    self.vw_option_add("exclude_hosts", value, config_file)
                else:
                    logger.info("++++ Set filter_hosts={0} ++++".format(value))
                    self.vw_option_add("filter_hosts", value, config_file)
                data, tty_output, rhsm_output = self.vw_start()
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                if key == "step4":
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=False)
                    self.vw_option_del("exclude_hosts", config_file)
                else:
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=True)
                results.setdefault(step, []).append(res1)
                results.setdefault(step, []).append(res2)
                self.vw_option_del("filter_hosts", config_file)
            self.vw_option_del("hypervisor_id", config_file)
            self.vw_web_host_delete(host_name, hypervisorId)
        if "stage" in register_type:
            self.stage_consumer_clean(self.ssh_host(), register_config)

        # Case Result
        self.vw_case_result(results)
