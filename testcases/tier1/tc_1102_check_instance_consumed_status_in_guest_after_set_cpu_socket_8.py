# coding:utf-8
from library import *
from library.config import * 
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134080")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        instance_sku = args_sku['instance_sku_id']
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        conf_name = "%s_config" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: set cpu.cpu_socket(s) to 8 in guest")
        res = self.system_custom_facts_create(self.ssh_guest(), 'cpu.cpu_socket(s)', '8')
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

        logger.info(">>>step5: attach physical sku for guest with quantity=6")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=physical_pool_id, quantity=6)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*2', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Quantity Used:.*6', exp_exist=True)
        res4 = self.vw_msg_search(output, 'Status Details:.*Subscription is current', exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)
        results.setdefault('step5', []).append(res3)
        results.setdefault('step5', []).append(res4)
        self.system_custom_facts_remove(self.ssh_guest())


        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/06/25 Yuefen<yuefliu@redhat.com>
# - Case created to check virtual pool created or not in guest for Unlimited SKU
