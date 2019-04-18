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

        # Case Steps
        logger.info(">>>step1: register host and guest using activation key")
        ssh_args = [self.ssh_host(), self.ssh_guest()]
        cmd = 'subscription-manager register  --org="{0}" --activationkey="{1}"' \
                .format(register_owner, active_key)
        msg = 'System has been registered with ID.*'
        for args in ssh_args:
            system = 'host' if args == self.ssh_host() else 'guest'
            logger.info('register {0}'.format(system))
            self.system_unregister(args)
            ret, output = self.runcmd(cmd, args)
            if self.vw_msg_search(output, msg) is True:
                logger.info('succeded registering {0} using activation_key'.format(system))
                results.setdefault('step1', []).append(True)
            else:
                logger.error('failed registering {0} using activation_key'.format(system))
                results.setdefault('step1', []).append(False)

        logger.info(">>>step2: run virt-who")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_attach(host_name, host_uuid, pool_id)

        logger.info(">>>step4: attach virtual sku for guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)
