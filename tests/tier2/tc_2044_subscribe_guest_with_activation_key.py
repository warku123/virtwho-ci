# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137100')
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

        hypervisor_type = self.get_config('hypervisor_type')
        register_config = self.get_register_config()
        ssh_sat = register_config['ssh_sat']
        default_org = register_config['owner']
        vdc_physical = register_config['vdc']
        vdc_virtual = register_config['vdc_bonus']
        limit_sku = register_config['limit']
        physical_vdc_pool_id = self.system_sku_attr(self.ssh_host(), vdc_physical, "physical")['pool_id']
        physical_limit_pool_id= self.system_sku_attr(self.ssh_host(), limit_sku, "physical")['pool_id']
        default_org_id = self.satellite_org_id_get(ssh_sat, register_config, default_org)
        ak_list = {
        'libvirt-local':    'libvirt-local_ak',
        'libvirt-remote':   'libvirt-remote_ak',
        'esx':              'esx_ak',
        'hyperv':           'hyperv_ak',
        'xen':              'xen_ak',
        'vdsm':             'vdsm_ak',
        'rhevm':            'rhevm_ak',
        'kubevirt':         'kubevirt_ak'
        }

        ak_name = ak_list[hypervisor_type]
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()

        # Case Steps
        try:
            logger.info(">>>step1: Register host with activation key, and start to run virt-who")
            self.satellite_active_key_create(ssh_sat, register_config, ak_name, default_org_id)
            self.system_register_with_ak(self.ssh_host(), register_config, ak_name)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step1', []).append(res)

            logger.info(">>>step2: Attach physical vdc and limit sku to hypervisor, and check virtual sku in guest")
            self.system_sku_unattach(self.ssh_host())
            self.vw_web_attach(host_name, host_uuid, physical_limit_pool_id)
            self.vw_web_attach(host_name, host_uuid, physical_vdc_pool_id)
            virtual_vdc_pool_id = self.system_sku_attr(self.ssh_guest(), vdc_virtual, "virtual")['pool_id']
            virtual_limit_pool_id = self.system_sku_attr(self.ssh_guest(), limit_sku, "virtual")['pool_id']
            if not virtual_vdc_pool_id and not virtual_limit_pool_id:
                results.setdefault('step2', []).append(False)

            logger.info(">>>step3: Register guest with auto-attach enabled by default, no sku in the key")
            # guest will be auto-attached the best matched pool, limit has the high priority
            self.system_register_with_ak(self.ssh_guest(), register_config, ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, virtual_limit_pool_id, exp_exist=True)
            res2 = self.vw_msg_search(output, virtual_vdc_pool_id, exp_exist=False)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)

            logger.info(">>>step4: Re-register guest with auto-attach enabled by default, but only add virtual_vdc to the key")
            # guest will be auto-attached with the only virtual vdc
            vdc_katello_id = self.satellite_katello_id(ssh_sat, register_config, virtual_vdc_pool_id)
            self.satellite_active_key_attach_sku(ssh_sat, register_config, ak_name, vdc_katello_id, default_org_id)
            self.system_register_with_ak(self.ssh_guest(), register_config, ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, virtual_limit_pool_id, exp_exist=False)
            res2 = self.vw_msg_search(output, virtual_vdc_pool_id, exp_exist=True)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)

            logger.info(">>>step5: Re-register guest with auto-attach enabled by default, both virtual_vdc and virtual_limit are added to the key")
            # guest will be auto-attached the best matched pool, vdc has the high priority
            limit_katello_id = self.satellite_katello_id(ssh_sat, register_config, virtual_limit_pool_id)
            self.satellite_active_key_attach_sku(ssh_sat, register_config, ak_name, limit_katello_id, default_org_id)
            self.system_register_with_ak(self.ssh_guest(), register_config, ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, virtual_limit_pool_id, exp_exist=False)
            res2 = self.vw_msg_search(output, virtual_vdc_pool_id, exp_exist=True)
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)

            logger.info(">>>step6: Re-register guest with auto-attach disabled, both virtual_vdc and virtual_limit are added to the key")
            # guest will be auto-attached with these two skus
            self.satellite_active_key_auto_attach_enable(ssh_sat, register_config, ak_name, default_org_id, auto_attach='false')
            self.system_register_with_ak(self.ssh_guest(), register_config, ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, virtual_limit_pool_id, exp_exist=True)
            res2 = self.vw_msg_search(output, virtual_vdc_pool_id, exp_exist=True)
            results.setdefault('step6', []).append(res1)
            results.setdefault('step6', []).append(res2)

            logger.info(">>>step7: Re-register guest with auto-attach disabled, no sku in the key")
            # guest will not be auto-attached to any sku
            self.satellite_active_key_unattach_sku(ssh_sat, register_config, ak_name, limit_katello_id, default_org_id)
            self.satellite_active_key_unattach_sku(ssh_sat, register_config, ak_name, vdc_katello_id, default_org_id)
            self.system_register_with_ak(self.ssh_guest(), register_config, ak_name)
            output = self.system_sku_consumed(self.ssh_guest(), exp_exist=False)
            res1 = self.vw_msg_search(output, 'No consumed subscription pools', exp_exist=True)
            results.setdefault('step7', []).append(res1)
        except:
            results.setdefault('step7', []).append(False)
            pass

        finally:
            logger.info(">>>Finally step: Clear environment")
            self.vw_web_host_delete(host_name, host_uuid)
            self.vw_web_host_delete(guest_name, guest_uuid)
            self.satellite_active_key_delete(ssh_sat, register_config, ak_name, default_org_id)

        # Case Result
        self.vw_case_result(results)

