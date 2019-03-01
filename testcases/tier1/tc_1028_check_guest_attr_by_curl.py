# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133745")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode
        config_name = "%s_config" % mode
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: config mode, check report send and no error msg ")
        self.vw_etc_d_mode_create(mode, config_name, filename=config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check guest attributes by curl")
        if "stage" in server_type:
            stage_user, stage_passwd, owner, env = self.stage_account_get(mode)
            consumer_uuid = self.stage_consumer_uuid(self.ssh_host(), mode, host_name, host_uuid)
            baseurl = "https://subscription.rhsm.stage.redhat.com/subscription"
            cmd = "curl -s -k -u %s:%s %s/consumers/%s/guestids/%s" \
                % (stage_user, stage_passwd, baseurl, consumer_uuid, guest_uuid)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="stage guest attributes")
            logger.info(output)
            if guest_uuid in output and "guestId" in output and "attributes" in output:
                logger.info("Succeeded to check the guest attributes by curl")
                results.setdefault('step2', []).append(True)
            else:
                logger.error("Failed to check the guest attributes by curl")
                results.setdefault('step2', []).append(False)
        if "satellite" in server_type:
            sat_user, sat_passwd = self.satellite_account_get(server_ip)
            guest_hostid = self.satellite_host_id(self.ssh_host(), server_ip, guest_name, guest_uuid)
            baseurl = "https://%s" % server_ip
            cmd = "curl -X GET -s -k -u %s:%s %s/api/v2/hosts/%s" % (sat_user, sat_passwd, baseurl, guest_hostid)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="satellite guest attributes")
            attr1 = '"id":%s' % guest_hostid
            if attr1 in output and guest_name in output:
                logger.info("Succeeded to check the guest attributes by curl")
                results.setdefault('step2', []).append(True)
            else:
                logger.error("Failed to check the guest attributes by curl")
                results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/08 Eko<hsun@redhat.com>
#- Case created to validate guest attributes by curl
