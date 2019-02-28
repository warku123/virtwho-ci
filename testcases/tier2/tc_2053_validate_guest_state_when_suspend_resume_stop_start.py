# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136733")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        vdc_physical_sku = args_sku['vdc_sku_id']
        vdc_virtual_sku = args_sku['vdc_bonus_sku_id']
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_option_enable("VIRTWHO_INTERVAL", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who and attach VDC for host/guest")
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        self.vw_web_attach(self.ssh_host(), host_name, host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        try:
            logger.info(">>>step2: suspend guest, and then restart virt-who")
            self.mode_guest_suspend(mode)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            if "libvirt" in mode or "hyperv" in mode or "esx" in mode:
                res2 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state=3)
            else:
                res2 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state=False)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: resume guest, and then restart virt-who")
            self.mode_guest_resume(mode)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            output = self.system_sku_consumed(self.ssh_guest())
            res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
            res3 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state=1)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            results.setdefault('step3', []).append(res3)

        try:
            logger.info(">>>step4: stop guest, and then restart virt-who")
            ret, output = self.runcmd("sync;sync;sync", self.ssh_guest(), desc="sync data")
            self.mode_guest_stop(mode)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            if "libvirt" in mode or "hyperv" in mode or "esx" in mode:
                res2 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state="3|4|5")
            else:
                res2 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state=False)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)
        except:
            results.setdefault('step4', []).append(False)
            pass
        finally:
            logger.info(">>>step5: start guest, and then restart virt-who")
            self.mode_guest_start(mode)
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            output = self.system_sku_consumed(self.ssh_guest())
            res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
            res3 = self.validate_guest_state(data, mode, owner, guest_uuid, exp_state=1)
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)
            results.setdefault('step5', []).append(res3)

        # Case Result
        self.vw_case_result(results)

    def validate_guest_state(self, data, mode, owner, guest_uuid, exp_state):
        if exp_state is False:
            if "vdsm" in mode or "libvirt-local" in mode:
                state = data.has_key(guest_uuid)
            else:
                state = data[owner].has_key(guest_uuid)
        else:
            if "vdsm" in mode or "libvirt-local" in mode:
                state = data[guest_uuid]['state']
            else:
                state = data[owner][guest_uuid]['state']
        if str(state) in str(exp_state):
            logger.info("Expected guest state(%s) is matched(%s) for %s" % (exp_state, state, mode))
            return True
        else:
            logger.error("Expected guest state(%s) is not matched(%s) for %s" % (exp_state, state, mode))
            return False

if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/08/01 Eko<hsun@redhat.com>
#- Case created
