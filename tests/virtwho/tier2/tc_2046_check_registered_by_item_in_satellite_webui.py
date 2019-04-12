# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137102')
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
        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()
        register_config = self.get_register_config()
        admin_user = register_config['username']
        admin_passwd = register_config['password']
        server = register_config['server']

        # Case Steps
        logger.info(">>>step1: get guest_id and vw_host_uuid")
        baseurl = "https://{0}".format(server)
        host_id = self.satellite_host_id(self.ssh_host(), register_config, host_name, host_uuid)
        guest_host_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()
        guest_id = self.satellite_host_id(self.ssh_host(), register_config, guest_host_name, guest_uuid)
        if 'libvirt-local' in hypervisor_type or 'vdsm' in hypervisor_type:
            exp_list = {'hypervisor':'admin', 'guest':'admin'}
        else:
            vw_host_name = self.get_hostname(self.ssh_host())
            vw_hostid = self.satellite_host_id(self.ssh_host(), register_config, vw_host_name, 'xxx')
            cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}" \
                .format(admin_user, admin_passwd, baseurl, vw_hostid)
            ret, out = self.runcmd(cmd, self.ssh_host())
            out = self.is_json(out.strip())
            vw_host_uuid = out['subscription_facet_attributes']['uuid']
            exp_list = {'hypervisor':vw_host_uuid, 'guest':'admin'}

        logger.info(">>>step2: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: check registered_by info for hypervisor and guest")
        for type, exp in sorted(exp_list.items(), key=lambda item:item[0]):
            logger.info(">>>check {0}".format(type))
            if type == "hypervisor":
                cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}" \
                    .format(admin_user, admin_passwd, baseurl, host_id)
            else:
                cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}" \
                    .format(admin_user, admin_passwd, baseurl, guest_id)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="get hypervisor/guest info")
            output = self.is_json(output.strip())
            if ret == 0 and output is not False and output is not None:
                user = output["subscription_facet_attributes"]["user"]
                if user is not False and user is not None and user.has_key('login'):
                    registered_by = user['login']
                    if registered_by == exp:
                        logger.info("succeded to check registered_by is '%s'" % exp)
                        results.setdefault('step3', []).append(True)
                    else:
                        logger.error("failed to check registered_by is %s, actually it's '%s'" \
                                % (exp, registered_by))
                        results.setdefault('step3', []).append(False)
                else:
                    logger.error("failed to check registered_by")
                    results.setdefault('step3', []).append(False)
            else:
                logger.error("failed to get satellite %s info" % type)
                results.setdefault('step3', []).append(False)

        # Case Result
        notes = list()
        if "libvirt-local" not in hypervisor_type and "vdsm" not in hypervisor_type:
            notes.append("Bug(step3): should show virt-who UUID under 'registered by' for hypervisor")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1455041")
        self.vw_case_result(results, notes)
