# coding:utf-8
from library import *
from library.config import * 
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134054")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        limit_physical_sku = args_sku['limit_sku_id']
        limit_virtual_sku = args_sku['limit_sku_id']
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
        self.vw_web_unattach(self.ssh_host(), host_name, host_uuid)
        sku_attrs = self.system_sku_attr(self.ssh_host(), limit_physical_sku, "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_attach(self.ssh_host(), host_name, host_uuid, pool_id)

        logger.info(">>>step3: check virtual sku attrs in guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), limit_virtual_sku, "virtual")
        available = sku_attrs['available']
        if available == "1":
            logger.info("Succeeded to check, vitual sku(%s) Available(%s)" % (limit_virtual_sku, available))
            results.setdefault('step3', []).append(True)
        else:
            logger.error("Failed to check, vitual sku(%s) Available(%s)" % (limit_virtual_sku, available))
            results.setdefault('step3', []).append(False)

        try:
            logger.info(">>>step4: attach virtual sku by auto in guest")
            pool_id = sku_attrs['pool_id']
            self.system_sku_attach(self.ssh_guest())
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku, exp_exist=True)
            res2 = self.vw_msg_search(output, 'Quantity Used:.*1', exp_exist=True)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)
        except:
            results.setdefault('step4', []).append(False)
            pass

        # Case Result
        notes = list()
        if "satellite" in server_type:
            notes.append("Bug(Step4): Unable to use auto-attach")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1659014")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2019/01/21 Yuefen<yuefliu@redhat.com>
# - Add Bug 1659014 info, unable to use auto-attach for satellite
#- 2018/06/26 Eko<hsun@redhat.com>
#- Case created to check virtual pool attached by auto in guest for Limited SKU
