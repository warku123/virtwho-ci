# coding:utf-8
from library import *
from library.config import * 
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134070")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        vdc_physical_sku = args_sku['vdc_sku_id']
        vdc_virtual_sku = args_sku['vdc_bonus_sku_id'] 
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        conf_name = "%s_config" % mode.lower()
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who and check the mapping info is sent or not")
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        physical_pool_id = sku_attrs['pool_id']
        self.vw_web_attach(self.ssh_host(), host_name, host_uuid, physical_pool_id)

        logger.info(">>>step3: attach virtual sku by pool_id in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        virtual_pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=virtual_pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step4: unregister host/hypervisor and check virtual pool revoked or not")
        self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
        output = self.system_sku_consumed(self.ssh_guest(), exp_exist=False)
        res = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=False)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/20 Eko<hsun@redhat.com>
#- Case created to check virtual pool can be revoked by auto when host/hypervisor unregister
