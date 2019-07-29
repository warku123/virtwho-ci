# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137101')
        register_type = self.get_config('register_type')
        if 'stage' in register_type:
            self.vw_case_skip(register_type)
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
        vdc_physical_sku = register_config['vdc']
        vdc_virtual_sku = register_config['vdc_bonus']
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        register_owner = register_config['owner']
        active_key = 'Virtwho_AK'
        cmd = 'subscription-manager register  --org="{0}" --activationkey="{1}"'.format(
            register_owner, active_key)
        msg = 'System has been registered with ID.*'

        # Case Steps
        logger.info(">>>step1: register host and guest using activation key")
        for system in [self.ssh_host(), self.ssh_guest()]:
            self.system_unregister(system)
            ret, output = self.runcmd(cmd, system)
            res1 = self.vw_msg_search(output, msg, exp_exist=True)
            results.setdefault('step1', []).append(res1)

        logger.info(">>>step2: check temporary sku is attached by auto in guest")
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, 'Subscription Type: .*Temporary', exp_exist=True)
        results.setdefault('step2', []).append(res1)

        logger.info(">>>step3: start virt-who service to check temporary sku disappeared")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        output = self.system_sku_consumed(self.ssh_guest())
        res2 = self.vw_msg_search(output, 'Subscription Type: .*Temporary', exp_exist=False)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: attach physical sku for host/hypervisor  \
                    then register guest using activation key again")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_unattach(host_name, host_uuid)
        self.vw_web_attach(host_name, host_uuid, pool_id)
        self.system_unregister(self.ssh_guest())
        ret, output = self.runcmd(cmd, self.ssh_guest())
        res = self.vw_msg_search(output, msg, exp_exist=True)
        results.setdefault('step4', []).append(res)

        logger.info(">>>step5: check stable virtual sku is attached by auto in guest")
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step5', []).append(res)

        # Case Result
        self.vw_case_result(results)