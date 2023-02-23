# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134075')
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
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        register_config = self.get_register_config()
        instance_sku = register_config['instance']

        # case steps
        logger.info(">>>step1: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), instance_sku, "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_attach(host_name, host_uuid, pool_id, quantity=2)

        logger.info(">>>step3: check no virtual sku is created or not in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "virtual", exp_exist=False)
        if sku_attrs:
            logger.error("failed to check, virtual instance sku is exist")
            results.setdefault('step3', []).append(False)
        else:
            logger.info("succeeded to check, virtual instance sku is not exist")
            results.setdefault('step3', []).append(True)

        # case result
        self.vw_case_result(results)
