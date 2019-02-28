# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137101")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        vdc_physical_sku = args_sku['vdc_sku_id']
        vdc_virtual_sku = args_sku['vdc_bonus_sku_id']
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        active_key = args_global['activation_key']
        self.vw_option_enable("VIRTWHO_DEBUG", filename='/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename='/etc/sysconfig/virt-who')

        # Case Steps
        logger.info(">>>step1: register host and guest using activation key")
        ssh_args = [self.ssh_host(), self.ssh_guest()]
        cmd = 'subscription-manager register  --org="%s" --activationkey="%s"' \
                % (owner, active_key)
        msg = 'System has been registered with ID.*'
        for args in ssh_args:
            system = 'host' if args == self.ssh_host() else 'guest'
            logger.info('register %s' % system)
            self.system_unregister(args)
            ret, output = self.runcmd(cmd, args)
            if self.vw_msg_search(output, msg) is True:
                logger.info('succeded registering %s using activation_key' % system)
                results.setdefault('step1', []).append(True)
            else:
                logger.error('failed registering %s using activation_key' % system)
                results.setdefault('step1', []).append(False)

        logger.info(">>>step2: run virt-who")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_attach(self.ssh_host(), host_name, host_uuid, pool_id)

        logger.info(">>>step4: attach virtual sku for guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/16 Yuefen<yuefliu@redhat.com>
