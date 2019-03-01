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
        sat_user, sat_passwd = self.satellite_account_get(server_ip)

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: attach physical vdc for hypervisor, then check subscriptions")
        physical_sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        physical_pool_id = physical_sku_attrs['pool_id']
        self.vw_web_attach(self.ssh_host(), host_name, host_uuid, physical_pool_id)
        virtual_sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        virtual_pool_id = virtual_sku_attrs['pool_id']
        katello_id = self.satellite_katello_id(self.ssh_host(), server_ip, virtual_pool_id)
        name_list = []
        if 'libvirt-local' in mode or 'vdsm' in mode:
            name_list = ['%s' % host_name]
        else:
            name_list = ['virt-who-%s-1' % host_name, 'virt-who-%s-1' % host_uuid]
        baseurl = "https://%s" % server_ip
        cmd = "curl -X GET -s -k -u %s:%s %s/katello/api/organizations/1/subscriptions/%s" \
                % (sat_user, sat_passwd, baseurl, katello_id)
        ret, output = self.runcmd(cmd, self.ssh_host())
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None:
            if output["type"] == "STACK_DERIVED" and output["virt_only"] is True and \
                output["hypervisor"]["name"] in name_list:
                logger.info("succeeded to check bonus pool coming from %s" % name_list)
                results.setdefault('step2', []).append(True)
            else:
                logger.error("failed to check bonus pool coming from %s" % name_list)
                results.setdefault('step2', []).append(False)
            if output["available"] == -1 and output["quantity"] == -1 and output["consumed"] == 0:
                logger.info("succeeded to check consumed status is '0 out of Unlimitted'")
                results.setdefault('step2', []).append(True)
            else:
                logger.error("failed to check consumed status is '0 out of Unlimitted'")
                results.setdefault('step2', []).append(False)
        else:
            logger.error("failed to get subscritons info")
            results.setdefault('step2', []).append(False)

        logger.info(">>>step3: attach bonus vdc for guest, then check subscriptions")
        self.system_sku_attach(self.ssh_guest(), pool_id=virtual_pool_id)
        time.sleep(60)
        for i in range(3):
            ret, output = self.runcmd(cmd, self.ssh_host())
            output = self.is_json(output.strip())
            if ret == 0 and output is not False and output is not None:
                if output["available"] == -2 or output["available"] == -1 and output["quantity"] == -1 and output["consumed"] == 1:
                    logger.info("succeeded to check consumed status is '1 out of Unlimitted'")
                    results.setdefault('step3', []).append(True)
                    break
                logger.warning("webui has not been refreshed, try again after 60s...")
                time.sleep(60)
        if 'step3' not in results.keys():
            logger.error("failed to check consumed status")
            results.setdefault('step3', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/15 Yuefen<yuefliu@redhat.com>