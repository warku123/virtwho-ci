# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136636')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type not in ('esx'):
            self.vw_case_skip(hypervisor_type)
        # Bug 1461272 only be fixed in rhel8, so rhel7 doesn't support this function
        compose_id = self.get_config('rhel_compose')
        if "RHEL-7" in compose_id:
            self.vw_case_skip(compose_id)
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

        # Case Steps
        logger.info(">>>step1: run virt-who with filter_host_parents= to check the domain_id")
        self.vw_option_add("filter_host_parents", "", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        domain_id = re.findall(r"Skipping host '{0}' because its parent '(.*?)'".format(host_hwuuid), rhsm_output)[-1]
        logger.info("Succeeded to find: {0}:{1}:{0}".format(host_hwuuid, domain_id))
        self.vw_option_del("filter_host_parents", config_file)

        steps = {'step2':'uuid', 'step3':'hostname', 'step4':'hwuuid'}
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to with hypervisor_id={1} and set filter_host_parents".format(step, option))
            self.vw_option_add("hypervisor_id", option, config_file)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
            else:
                hypervisorId = host_uuid
            wildcard = domain_id[:3] + '*' + domain_id[4:]
            sub_steps = {'step1':domain_id, 'step2': "*", 'step3': wildcard, 'step4': wildcard}
            for key, value in sorted(sub_steps.items(),key=lambda item:item[0]):
                if key == "step4":
                    logger.info("++++ Set filter_host_parents={0} and exclude_host_parents=* ++++".format(value))
                    self.vw_option_add("exclude_host_parents", "*", config_file)
                    self.vw_option_add("filter_host_parents", value, config_file)
                else:
                    logger.info("++++ Set filter_host_parents={0} ++++".format(value))
                    self.vw_option_add("filter_host_parents", value, config_file)
                data, tty_output, rhsm_output = self.vw_start()
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                if key == "step4":
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=False)
                else:
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=True)
                results.setdefault(step, []).append(res1)
                results.setdefault(step, []).append(res2)
                self.vw_option_del("exclude_host_parents", config_file)
                self.vw_option_del("filter_host_parents", config_file)
            self.vw_option_del("hypervisor_id", config_file)
            if "satellite" in register_type:
                self.vw_web_host_delete(host_name, hypervisorId)
        if "stage" in register_type:
            self.stage_consumer_clean(self.ssh_host(), register_config)

        # Case Result
        self.vw_case_result(results)
