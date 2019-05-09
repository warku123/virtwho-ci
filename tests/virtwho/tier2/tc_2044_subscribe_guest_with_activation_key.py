# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137100')
        hypervisor_type = self.get_config('hypervisor_type')
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
        limit_sku = register_config['limit']
        vdc_physical_sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        vdc_physical_sku_pool_id = vdc_physical_sku_attrs['pool_id']
        limit_physical_sku_attrs = self.system_sku_attr(self.ssh_host(), limit_sku, "physical")
        limit_physical_sku_pool_id = limit_physical_sku_attrs['pool_id']
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()

        register_config = self.get_register_config()
        sat_host = register_config['server']
        admin_user = register_config['username']
        admin_passwd = register_config['password']
        ssh_sat = {
                "host": sat_host, 
                "username": register_config['ssh_user'],
                "password": register_config['ssh_passwd'],
                }
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

        # Case Steps
        try:
            logger.info(">>>step1: Create activation key {0}".format(ak_name))
            self.satellite_active_key_create(ssh_sat, admin_user, admin_passwd, ak_name)
        except:
            results.setdefault('step1', []).append(False)
            pass

        try:
            logger.info(">>>step2: enable auto-attach with no subscription specified")
            self.system_register_with_ak(self.ssh_host(), ak_name)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res)
            # attach limit and vdc subscription for hypervisor
            self.system_sku_unattach(self.ssh_host())
            self.vw_web_attach(host_name, host_uuid, limit_physical_sku_pool_id)
            self.vw_web_attach(host_name, host_uuid, vdc_physical_sku_pool_id)
            limit_virtual_sku_attrs = self.system_sku_attr(self.ssh_guest(), limit_sku, "virtual")
            limit_virtual_sku_pool_id = limit_virtual_sku_attrs['pool_id']
            logger.info('limit_virtual_sku_pool_id: {0}'.format(limit_virtual_sku_pool_id))
            vdc_virtual_sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
            vdc_virtual_sku_pool_id = vdc_virtual_sku_attrs['pool_id']
            logger.info('vdc_virtual_sku_pool_id: {0}'.format(vdc_virtual_sku_pool_id))
            # register guest with activation key, guest will auto-attach the best match pool from all subscriptions
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku_pool_id, exp_exist=True)
            res2 = self.vw_msg_search(output, vdc_virtual_sku_pool_id, exp_exist=False)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
        except:
            results.setdefault('step2', []).append(False)
            pass

        try:
            logger.info(">>>step3: enable auto-attach with subscription specified")
            # add vdc virtual sku to activation key, guest will auto-attach the best match pool from subscriptions in the key
            vdc_katello_id = self.satellite_katello_id(ssh_sat, register_config, vdc_virtual_sku_pool_id)
            self.satellite_ak_add_subscription(ssh_sat, admin_user, admin_passwd, ak_name, vdc_katello_id)
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku_pool_id, exp_exist=False)
            res2 = self.vw_msg_search(output, vdc_virtual_sku_pool_id, exp_exist=True)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            # then add limit virtual sku to activation key, guest will auto-attach the best match pool from subscriptions in the key
            limit_katello_id = self.satellite_katello_id(self.ssh_host(), register_config, limit_virtual_sku_pool_id)
            self.satellite_ak_add_subscription(ssh_sat, admin_user, admin_passwd, ak_name, limit_katello_id)
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku_pool_id, exp_exist=True)
            res2 = self.vw_msg_search(output, vdc_virtual_sku_pool_id, exp_exist=False)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
        except:
            results.setdefault('step3', []).append(False)
            pass

        try:
            logger.info(">>>step4: disable auto-attach with subscription specified")
            # guest will auto-attach all pools in the key
            self.satellite_ak_edit_auto_attach(ssh_sat, admin_user, admin_passwd, ak_name, auto_attach='false')
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku_pool_id, exp_exist=True)
            res2 = self.vw_msg_search(output, vdc_virtual_sku_pool_id, exp_exist=True)
            results.setdefault('step4', []).append(res1)
            results.setdefault('step4', []).append(res2)
        except:
            results.setdefault('step4', []).append(False)
            pass

        try:
            logger.info(">>>step5: disable auto-attach with no subscription specified")
            # guest will not auto-attach any pool
            self.satellite_ak_rm_subscription(ssh_sat, admin_user, admin_passwd, ak_name, limit_katello_id)
            self.satellite_ak_rm_subscription(ssh_sat, admin_user, admin_passwd, ak_name, vdc_katello_id)
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            cmd = "subscription-manager list --co"
            ret, output = self.runcmd(cmd, self.ssh_guest(), desc="subscription list consumed for guest")
            if ret == 0 and "No consumed subscription pools" in output:
                results.setdefault('step5', []).append(True)
            else:
                logger.info('Failed to search no subscription is auto attached')
                results.setdefault('step5', []).append(False)
        except:
            results.setdefault('step5', []).append(False)
            pass

        finally:
            logger.info(">>>step finally: Clear environment")
            self.vw_web_host_delete(host_name, host_uuid)
            self.vw_web_host_delete(guest_name, guest_uuid)
            self.satellite_ak_delete(ssh_sat, admin_user, admin_passwd, ak_name)

        # Case Result
        self.vw_case_result(results)

    def satellite_ak_delete(self, ssh_sat, admin_user, admin_passwd, key_name):
        output = self.satellite_active_key_list(ssh_sat, admin_user, admin_passwd)
        key_id = self.satellite_ak_id_get(output, key_name)
        baseurl = "https://%s" % self.get_hostname(ssh_sat)
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        cmd = "curl %s -X DELETE -s -k -u %s:%s %s/katello/api/activation_keys/%s" \
                % (curl_header, admin_user, admin_passwd, baseurl, key_id)
        ret, output = self.runcmd(cmd, ssh_sat, desc="satellite delete activation key id:%s" % key_id)
        if ret == 0:
            for i in range(5):
                output = self.satellite_active_key_list(ssh_sat, admin_user, admin_passwd)
                if output['total'] != 0:
                    for item in output['results']:
                        id_list = []
                        id_list.append(item['id'])
                        if key_id not in id_list:
                            logger.info("succeeded to delete activation_key id: %s" % key_id)
                            return
                        logger.warning("activation key still exists, try again after 30s...")
                        time.sleep(30)
                else:
                    logger.info("succeeded to delete activation_key id: %s" % key_id)
                    return
        raise FailException("Failed to delete activation_key")

    def satellite_ak_id_get(self, output, key_name):
        if output is not False and output is not None and output != "":
            for item in output['results']:
                if item['name'] == key_name:
                    key_id = item['id']
                    logger.info("Succeded to get activation key id: %s" % key_id)
                    return key_id
        raise FailException("Failed to get activation key id of %s" % key_name)

    def system_register_with_ak(self, ssh_args, key_name, sat_org=None):
        if sat_org == None:
            register_config = self.get_register_config()
            sat_org = register_config['owner']
        self.system_unregister(ssh_args)
        cmd = 'subscription-manager register  --org="%s" --activationkey="%s"' % (sat_org, key_name)
        msg = 'System has been registered with ID.*'
        ret, output = self.runcmd(cmd, ssh_args, desc='register system with activationkey')
        if self.vw_msg_search(output, msg) is True:
            logger.info('succeded to register system using activation_key: %s' % key_name)
        else:
            raise FailException('failed to register system using activation_key')

    def satellite_ak_add_subscription(self, ssh_sat, admin_user, admin_passwd, key_name, katello_id, quantity=1):
        output = self.satellite_active_key_list(ssh_sat, admin_user, admin_passwd)
        key_id = self.satellite_ak_id_get(output, key_name)
        baseurl = "https://%s" % self.get_hostname(ssh_sat)
        curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":%s, "quantity":%s}' \
                 % (key_id, katello_id, quantity))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/v2/activation_keys/%s/add_subscriptions" \
                % (curl_header, admin_user, admin_passwd, data_json, baseurl, key_id)
        ret, output = self.runcmd(cmd, ssh_sat, desc="add pool %s to activation key" % katello_id)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to add subscription %s for activation key" % katello_id)
        else:
            raise FailException("Failed to add subscription for activation key")

    def satellite_ak_rm_subscription(self, ssh_sat, admin_user, admin_passwd, key_name, katello_id):
        output = self.satellite_active_key_list(ssh_sat, admin_user, admin_passwd)
        key_id = self.satellite_ak_id_get(output, key_name)
        baseurl = "https://%s" % self.get_hostname(ssh_sat)
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":"%s"}' \
                 % (key_id, katello_id))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/v2/activation_keys/%s/remove_subscriptions" \
                % (curl_header, admin_user, admin_passwd, data_json, baseurl, key_id)
        ret, output = self.runcmd(cmd, ssh_sat, desc="remove subscription %s from activation key" % katello_id)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to remove subscription from activation key")
        else:
            raise FailException("Failed to remove subscription from activation key")

    def satellite_ak_edit_auto_attach(self, ssh_sat, admin_user, admin_passwd, key_name, auto_attach='true'):
        output = self.satellite_active_key_list(ssh_sat, admin_user, admin_passwd)
        key_id = self.satellite_ak_id_get(output, key_name)
        baseurl = "https://%s" % self.get_hostname(ssh_sat)
        org_name = 'Default_Organization'
        org_id = self.satellite_org_id_get(ssh_sat, admin_user, admin_passwd, org_name)
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"organization_id":"%s", "auto_attach":"%s"}' % (org_id, auto_attach))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/activation_keys/%s" \
                % (curl_header, admin_user, admin_passwd, data_json, baseurl, key_id)
        ret, output = self.runcmd(cmd, ssh_sat, desc="edit auto_attach=%s" % auto_attach)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to edit auto_attach to %s" % auto_attach)
        else:
            raise FailException("Failed to edit auto_attach")
