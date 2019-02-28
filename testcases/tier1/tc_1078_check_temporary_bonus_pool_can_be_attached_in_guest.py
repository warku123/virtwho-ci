# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134083")
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
        logger.info(">>>step1: stop virt-who, re-register guest again to create temporary bonus")
        self.vw_thread_clean()
        self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
        self.system_unregister(self.ssh_guest())
        self.vw_sub_register(self.ssh_guest())

        logger.info(">>>step2: check temporary bonus pool exist in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        sub_type = sku_attrs['sub_type']
        if "Temporary" in sub_type:
            logger.info("%s, Temporary pool is exist in guest" % sub_type)
            results.setdefault('step2', []).append(True)
        else:
            logger.error("%s, Temporary pool is not exist in guest" % sub_type)
            results.setdefault('step2', []).append(False)

        logger.info(">>>step3: attach temporary bonus pool in guest")
        pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res1 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        res2 = self.vw_msg_search(output, "using a temporary unmapped guest subscription", exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/02 Eko<hsun@redhat.com>
#- Case created to check temporary bonus pool can be attached or not in guest
