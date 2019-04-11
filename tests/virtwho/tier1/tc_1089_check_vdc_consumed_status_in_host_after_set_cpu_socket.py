# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134052')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type not in ('libvirt-local', 'vdsm'):
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
        register_config = self.get_register_config()
        vdc_physical_sku = register_config['vdc']
        vdc_virtual_sku = register_config['vdc_bonus']

        # case steps
        logger.info(">>>step1: set cpu.cpu_socket(s) to 4 in host")
        res = self.system_custom_facts_create(self.ssh_host(), 'cpu.cpu_socket(s)', '4')
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: attach physical sku for host/hypervisor without quantity")
        self.system_sku_unattach(self.ssh_host())
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_host(), pool_id=physical_pool_id)
        output = self.system_sku_consumed(self.ssh_host())
        res1 = self.vw_msg_search(output, vdc_physical_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*2', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Subscription is current', exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)
        results.setdefault('step3', []).append(res3)

        logger.info(">>>step4: attach physical sku for host/hypervisor with quantity=1")
        self.system_sku_unattach(self.ssh_host())
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_host(), pool_id=physical_pool_id, quantity=1)
        output = self.system_sku_consumed(self.ssh_host())
        res1 = self.vw_msg_search(output, vdc_physical_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*1', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Only supports 2 of 4 sockets', exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)
        results.setdefault('step4', []).append(res3)
        self.system_custom_facts_remove(self.ssh_host())

        # case result
        self.vw_case_result(results)
