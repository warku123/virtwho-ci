# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137100")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        host_uuid = self.mode_host_uuid(mode)
        host_name = self.mode_host_name(mode)
        guest_uuid = self.mode_guest_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        self.vw_option_enable("VIRTWHO_DEBUG", filename='/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename='/etc/sysconfig/virt-who')
        vdc_physical_sku = args_sku['vdc_sku_id']
        vdc_physical_sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        vdc_physical_sku_pool_id = vdc_physical_sku_attrs['pool_id']
        vdc_virtual_sku = args_sku['vdc_bonus_sku_id']
        limit_sku = args_sku['limit_sku_id']
        limit_physical_sku_attrs = self.system_sku_attr(self.ssh_host(), limit_sku, "physical")
        limit_physical_sku_pool_id = limit_physical_sku_attrs['pool_id']

        ak_list = {
        'libvirt-local':  'libvirt-local_ak',
        'libvirt-remote': 'libvirt-remote_ak',
        'esx':            'esx_ak',
        'hyperv':         'hyperv_ak',
        'xen':            'xen_ak',
        'vdsm':           'vdsm_ak',
        'rhevm':          'rhevm_ak'
        }
        ak_name = ak_list[mode]

        # Case Steps
        try:
            logger.info(">>>step1: Create activation key %s and get the key id" % ak_name)
            self.satellite_active_key_create(self.ssh_host(), server_ip, ak_name)
            output = self.satellite_active_key_list(self.ssh_host(), server_ip)
            ak_id = self.satellite_ak_id_get(self.ssh_host(), output, ak_name)
        except:
            results.setdefault('step1', []).append(False)
            pass

        try:
            logger.info(">>>step2: enable auto-attach with no subscription specified")
            # register virt-who host with activation key, and then run virt-who service
            self.system_register_with_ak(self.ssh_host(), ak_name)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res)
            # attach limit and vdc subscription for hypervisor
            self.system_sku_unattach(self.ssh_host())
            self.vw_web_attach(self.ssh_host(), host_name, host_uuid, limit_physical_sku_pool_id)
            self.vw_web_attach(self.ssh_host(), host_name, host_uuid, vdc_physical_sku_pool_id)
            limit_virtual_sku_attrs = self.system_sku_attr(self.ssh_guest(), limit_sku, "virtual")
            limit_virtual_sku_pool_id = limit_virtual_sku_attrs['pool_id']
            logger.info('limit_virtual_sku_pool_id: %s' % limit_virtual_sku_pool_id)
            vdc_virtual_sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
            vdc_virtual_sku_pool_id = vdc_virtual_sku_attrs['pool_id']
            logger.info('vdc_virtual_sku_pool_id: %s' % vdc_virtual_sku_pool_id)
            # register guest with activation key, and it will auto attach one match virtual sku
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
            # add vdc virtual sku to the activation key
            vdc_katello_id = self.satellite_katello_id(self.ssh_host(), server_ip, vdc_virtual_sku_pool_id)
            self.satellite_ak_add_subscription(self.ssh_host(), server_ip, ak_id, vdc_katello_id)
            self.system_register_with_ak(self.ssh_guest(), ak_name)
            output = self.system_sku_consumed(self.ssh_guest())
            res1 = self.vw_msg_search(output, limit_virtual_sku_pool_id, exp_exist=False)
            res2 = self.vw_msg_search(output, vdc_virtual_sku_pool_id, exp_exist=True)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            # then add limit virtual sku to the activation key
            limit_katello_id = self.satellite_katello_id(self.ssh_host(), server_ip, limit_virtual_sku_pool_id)
            self.satellite_ak_add_subscription(self.ssh_host(), server_ip, ak_id, limit_katello_id)
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
            self.satellite_ak_edit_auto_attach(self.ssh_host(), server_ip, ak_id, auto_attach='false')
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
            self.satellite_ak_rm_subscription(self.ssh_host(), server_ip, ak_id, limit_katello_id)
            self.satellite_ak_rm_subscription(self.ssh_host(), server_ip, ak_id, vdc_katello_id)
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
            self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            self.vw_web_host_delete(self.ssh_guest(), guest_name, guest_uuid)
            self.satellite_ak_delete(self.ssh_host(), server_ip, ak_id)

        # Case Result
        notes = list()
        if "satellite" in server_type:
            notes.append("Bug(Step2,3,4,5): Unable to use auto-attach")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1659014")
        self.vw_case_result(results, notes)

    def satellite_ak_delete(self, ssh_args, server_ip, active_key_id, org_id=1):
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        server_hostname = self.satellite_hostname(server_ip)
        baseurl = "https://%s" % server_hostname
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        cmd = "curl %s -X DELETE -s -k -u %s:%s %s/katello/api/activation_keys/%s" \
                % (curl_header, sat_user, sat_passwd, baseurl, active_key_id)
        ret, output = self.runcmd(cmd, ssh_args, desc="satellite delete activation key id:%s" % active_key_id)
        if ret == 0:
            for i in range(5):
                output = self.satellite_active_key_list(ssh_args, server_ip, org_id)
                if output['total'] != 0:
                    for item in output['results']:
                        id_list = []
                        id_list.append(item['id'])
                        if active_key_id not in id_list:
                            logger.info("succeeded to delete activation_key id: %s" % active_key_id)
                            return
                        logger.warning("activation key still exists, try again after 30s...")
                        time.sleep(30)
                else:
                    logger.info("succeeded to delete activation_key id: %s" % active_key_id)
                    return
        raise FailException("Failed to delete activation_key")

    def satellite_ak_id_get(self, ssh_args, output, active_key_name):
        if output is not False and output is not None and output != "":
            for item in output['results']:
                if item['name'] == active_key_name:
                    active_key_id = item['id']
                    logger.info("Succeded to get activation key id: %s" % active_key_id)
                    return active_key_id
        raise FailException("Failed to get activation key id of %s" % active_key_name)

    def system_register_with_ak(self, ssh_args, active_key, sat_org=None):
        server_type, server_ip, owner, env = self.vw_server_info()
        self.system_unregister(ssh_args)
        if sat_org == None:
            sat_org = owner
        cmd = 'subscription-manager register  --org="%s" --activationkey="%s"' % (owner, active_key)
        msg = 'System has been registered with ID.*'
        ret, output = self.runcmd(cmd, ssh_args, desc='register system with activationkey')
        if self.vw_msg_search(output, msg) is True:
            logger.info('succeded to register system using activation_key: %s' % active_key)
        else:
            raise FailException('failed to register system using activation_key')

    def satellite_ak_add_subscription(self, ssh_args, server_ip, active_key_id, katello_id, quantity=None):
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        server_hostname = self.satellite_hostname(server_ip)
        if quantity == None:
            quantity = 1
        baseurl = "https://%s" % server_hostname
        curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":%s, "quantity":%s}' \
                 % (active_key_id, katello_id, quantity))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/v2/activation_keys/%s/add_subscriptions" \
                % (curl_header, sat_user, sat_passwd, data_json, baseurl, active_key_id)
        ret, output = self.runcmd(cmd, ssh_args, desc="add pool %s to activation key" % katello_id)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to add subscription %s for activation key" % katello_id)
        else:
            raise FailException("Failed to add subscription for activation key")

    def satellite_ak_rm_subscription(self, ssh_args, server_ip, active_key_id, katello_id):
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        server_hostname = self.satellite_hostname(server_ip)
        baseurl = "https://%s" % server_hostname
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":"%s"}' \
                 % (active_key_id, katello_id))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/v2/activation_keys/%s/remove_subscriptions" \
                % (curl_header, sat_user, sat_passwd, data_json, baseurl, active_key_id)
        ret, output = self.runcmd(cmd, ssh_args, desc="remove subscription %s from activation key" % katello_id)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to remove subscription from activation key")
        else:
            raise FailException("Failed to remove subscription from activation key")

    def satellite_ak_edit_auto_attach(self, ssh_args, server_ip, active_key_id, org_id=1, auto_attach='true'):
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        server_hostname = self.satellite_hostname(server_ip)
        baseurl = "https://%s" % server_hostname
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"organization_id":"%s", "auto_attach":"%s"}' % (org_id, auto_attach))
        cmd = "curl %s -X PUT -s -k -u %s:%s -d %s %s/katello/api/activation_keys/%s" \
                % (curl_header, sat_user, sat_passwd, data_json, baseurl, active_key_id)
        ret, output = self.runcmd(cmd, ssh_args, desc="edit auto_attach=%s" % auto_attach)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to edit auto_attach to %s" % auto_attach)
        else:
            raise FailException("Failed to edit auto_attach")

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2019/01/21 Yuefen<yuefliu@redhat.com>
# - Add Bug 1659014 info, unable to use auto-attach for satellite
# - 2018/10/16 Yuefen<yuefliu@redhat.com>
# - Case created
