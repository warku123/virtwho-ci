# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134078')
        self.vw_case_skip("instance sku")
        hypervisor_type = self.get_config('hypervisor_type')
        trigger_type = self.get_config('trigger_type')
        if hypervisor_type not in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if "trigger-rhev" in trigger_type:
            self.vw_case_skip(trigger_type)
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
        register_type = register_config['type']
        instance_sku = register_config['instance']
        sku_attrs = self.system_sku_attr(self.ssh_host(), instance_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']

        # case steps
        logger.info(">>>step1: set cpu.cpu_socket(s) to 8 in host")
        res = self.system_custom_facts_create(self.ssh_host(), 'cpu.cpu_socket(s)', '8')
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: attach physical sku for host without quantity")
        self.system_sku_unattach(self.ssh_host())
        self.system_sku_attach(self.ssh_host(), pool_id=physical_pool_id)
        output = self.system_sku_consumed(self.ssh_host())
        res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, 'Quantity Used:.*8', exp_exist=True)
        res3 = self.vw_msg_search(output, 'Status Details:.*Subscription is current')
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)
        results.setdefault('step3', []).append(res3)

        logger.info(">>>step4: attach physical sku for host with quantity=1")
        self.system_sku_unattach(self.ssh_host())
        cmd = ("subscription-manager attach --pool={0} --quantity=1"
               .format(physical_pool_id))
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="subscription attach")
        error_msg = 'must be attached using a quantity evenly divisible by 2'
        res = self.vw_msg_search(output, error_msg, exp_exist=True)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step5: attach physical sku for host with quantity=2")
        # Sometimes, Status Details is not Only supports 2 of 8 sockets, try it 5 loops
        res1 = res2 = res3 = False
        for i in range(5):
            self.system_sku_unattach(self.ssh_host())
            sku_attrs = self.system_sku_attr(self.ssh_host(), instance_sku, "physical")
            physical_pool_id = sku_attrs['pool_id']
            self.system_sku_attach(self.ssh_host(), pool_id=physical_pool_id, quantity=2)
            output = self.system_sku_consumed(self.ssh_host())
            msg = 'Status Details:.*Only supports 2 of 8 sockets'
            res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
            res2 = self.vw_msg_search(output, 'Quantity Used:.*2', exp_exist=True)
            res3 = self.vw_msg_search(output, msg, exp_exist=True)
            if res1 and res2 and res3:
                break
            wait_time = 60*(i+3)
            logger.warning("attach result is not expected, try again after {0}"
                           .format(wait_time))
            time.sleep(wait_time)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)
        results.setdefault('step5', []).append(res3)

        try:
            logger.info(">>>step6: attach sku for host by auto")
            self.system_sku_attach(self.ssh_host())
            output = self.system_sku_consumed(self.ssh_host())
            res1 = self.vw_msg_search(output, instance_sku, exp_exist=True)
            res2 = self.vw_msg_search(output, 'Quantity Used:.*2', exp_exist=True)
            res2 = self.vw_msg_search(output, 'Quantity Used:.*6', exp_exist=True)
            res4 = self.vw_msg_search(output, 'Status Details:.*Subscription is current')
            results.setdefault('step6', []).append(res1)
            results.setdefault('step6', []).append(res2)
            results.setdefault('step6', []).append(res3)
            results.setdefault('step6', []).append(res4)
        except:
            results.setdefault('step6', []).append(False)
            pass
        finally:
            self.system_custom_facts_remove(self.ssh_host())

        # case result
        self.vw_case_result(results)
