# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134079')
        self.vw_case_skip("instance sku")
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
        register_config = self.get_register_config()
        instance_sku = register_config['instance']

        # case steps
        logger.info(">>>step1: set cpu.cpu_socket(s) to 1 in guest")
        res = self.system_custom_facts_create(self.ssh_guest(), 'cpu.cpu_socket(s)', '1')
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: attach physical sku for guest without quantity")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=physical_pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*1', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Subscription is current', exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        logger.info(">>>step3: attach physical sku for guest with quantity=1")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=physical_pool_id, quantity=1)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*1', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Subscription is current', exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)
        results.setdefault('step3', []).append(res3)

        logger.info(">>>step4: attach physical sku for guest with quantity=2")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=physical_pool_id, quantity=2)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*2', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Subscription is current', exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)
        results.setdefault('step4', []).append(res3)
        self.system_custom_facts_remove(self.ssh_guest())

        # case result
        self.vw_case_result(results)
