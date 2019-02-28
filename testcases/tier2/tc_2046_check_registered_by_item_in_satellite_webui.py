# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137102")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        baseurl = "https://%s" % server_ip
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        host_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)
        guest_id = self.satellite_host_id(self.ssh_host(), server_ip, guest_name, guest_uuid)
        if 'libvirt-local' in mode or 'vdsm' in mode:
            exp_list = {'hypervisor':'admin', 'guest':'admin'}
        else:
            vw_hostname = self.get_hostname(self.ssh_host())
            vw_hostid = self.satellite_host_id(self.ssh_host(), server_ip, vw_hostname, 'xxx')
            cmd = "curl -X GET -s -k -u %s:%s %s/api/v2/hosts/%s" \
                % (sat_user, sat_passwd, baseurl, vw_hostid)
            ret, out = self.runcmd(cmd, self.ssh_host(), showlogger=False)
            out = self.is_json(out.strip())
            vw_host_uuid = out['subscription_facet_attributes']['uuid']
            exp_list = {'hypervisor':vw_host_uuid, 'guest':'admin'}

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check registered_by info for hypervisor and guest")
        for type, exp in sorted(exp_list.items(), key=lambda item:item[0]):
            logger.info(">>>check %s" % type)
            if type == "hypervisor":
                cmd = "curl -X GET -s -k -u %s:%s %s/api/v2/hosts/%s" \
                    % (sat_user, sat_passwd, baseurl, host_id)
            else:
                cmd = "curl -X GET -s -k -u %s:%s %s/api/v2/hosts/%s" \
                    % (sat_user, sat_passwd, baseurl, guest_id)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="get hypervisor info")
            output = self.is_json(output.strip())
            if ret == 0 and output is not False and output is not None:
                user = output["subscription_facet_attributes"]["user"]
                if user is not False and user is not None and user.has_key('login'):
                    registered_by = user['login']
                    if registered_by == exp:
                        logger.info("succeded to check registered_by is '%s'" % exp)
                        results.setdefault('step2', []).append(True)
                    else:
                        logger.error("failed to check registered_by is %s, actually it's '%s'" \
                                % (exp, registered_by))
                        results.setdefault('step2', []).append(False)
                else:
                    logger.error("failed to check registered_by")
                    results.setdefault('step2', []).append(False)
            else:
                logger.error("failed to get satellite %s info" % type)
                results.setdefault('step2', []).append(False)

        # Case Result
        notes = list()
        if "libvirt-local" not in mode and "vdsm" not in mode:
            notes.append("Bug(step2): should show virt-who UUID under 'registered by' for hypervisor")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1455041")
        self.vw_case_result(results, notes)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/13 Yuefen<yuefliu@redhat.com>
