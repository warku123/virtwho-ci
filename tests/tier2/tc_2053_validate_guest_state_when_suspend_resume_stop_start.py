# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136733")
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('kubevirt', 'ahv'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        register_config = self.get_register_config()
        vdc_physical_sku = register_config['vdc']
        vdc_virtual_sku = register_config['vdc_bonus']
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()
        owner = register_config['owner']

        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_option_enable('interval', '/etc/virt-who.conf')
        self.vw_option_update_value('interval', '60', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: run virt-who and attach VDC for host/guest")
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        self.vw_web_attach(host_name, host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        try:
            logger.info(">>>step2: suspend guest, and then restart virt-who")
            self.hypervisor_guest_suspend()
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            if hypervisor_type in ("libvirt-remote", "libvirt-local", "hyperv", "esx"):
                res2 = self.validate_guest_state(data, owner, guest_uuid, exp_state=3)
            else:
                res2 = self.validate_guest_state(data, owner, guest_uuid, exp_state=False)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: resume guest, and then restart virt-who")
            self.hypervisor_guest_resume()
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            output = self.system_sku_consumed(self.ssh_guest())
            res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
            res3 = self.validate_guest_state(data, owner, guest_uuid, exp_state=1)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            results.setdefault('step3', []).append(res3)

        try:
            logger.info(">>>step4: stop guest, and then restart virt-who")
            ret, output = self.runcmd("sync;sync;sync", self.ssh_guest(), desc="sync data")
            self.hypervisor_guest_stop()
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            if hypervisor_type in ("libvirt-remote", "libvirt-local",  "hyperv", "esx"):
                res2 = self.validate_guest_state(data, owner, guest_uuid, exp_state="3|4|5")
            else:
                res2 = self.validate_guest_state(data, owner, guest_uuid, exp_state=False)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)
        except:
            results.setdefault('step4', []).append(False)
            pass
        finally:
            logger.info(">>>step5: start guest, and then restart virt-who")
            self.hypervisor_guest_start()
            data, tty_output, rhsm_output = self.vw_start()
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            output = self.system_sku_consumed(self.ssh_guest())
            res2 = self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True)
            res3 = self.validate_guest_state(data, owner, guest_uuid, exp_state=1)
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)
            results.setdefault('step5', []).append(res3)

        # case result
        self.vw_case_result(results)

    def validate_guest_state(self, data, owner, guest_uuid, exp_state):
        hypervisor_type = self.get_config('hypervisor_type')
        if exp_state is False:
            if hypervisor_type in ('libvirt-local', 'vdsm'):
                state = guest_uuid in data.keys()
            else:
                state = guest_uuid in data[owner].keys()
        else:
            if hypervisor_type in ('libvirt-local', 'vdsm'):
                state = data[guest_uuid]['state']
            else:
                state = data[owner][guest_uuid]['state']
        if str(state) in str(exp_state):
            logger.info("Expected guest state({0}) is matched({1}) for {2}".format(exp_state, state, hypervisor_type))
            return True
        else:
            logger.error("Expected guest state({0}) is not matched({1}) for {2}".format(exp_state, state, hypervisor_type))
            return False
