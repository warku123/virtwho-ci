# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133700')
        hypervisor_type = self.get_config('hypervisor_type')
        if "esx" not in hypervisor_type:
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

        # case steps
        logger.info(">>>step1: run virt-who with exlude_host_parents=* to get domain_id")
        self.vw_option_add("exclude_host_parents", "*", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step1', []).append(s2)
        domain_id = re.findall(r"Skipping host '{0}' because its parent '(.*?)'".format(host_hwuuid), rhsm_output)[-1]
        logger.info("Succeeded to find: {0}:{1}:{2}".format(host_hwuuid, domain_id, host_uuid))
        self.vw_option_del("filter_host_parents", filename=config_file)

        logger.info(">>>step2: run virt-who with exclude_host_parents=[domain_id]")
        self.vw_option_add("exclude_host_parents", domain_id, filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step2', []).append(s2)

        logger.info(">>>step3: run virt-who with exclude_host_parents=")
        self.vw_option_update_value("exclude_host_parents", "", filename=config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step4', []).append(s2)

        # case result
        self.vw_case_result(results)
