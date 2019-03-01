# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137111")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type or 'libvirt-local' in mode or 'vdsm' in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        self.system_unregister(self.ssh_host())
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename='/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename='/etc/sysconfig/virt-who')
        default_org = args_satellite['default_owner']
        extra_org = args_satellite['extra_owner']
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        conf_file_2 = "/etc/virt-who.d/%s_2.conf" % mode.lower()
        rhsm_prefix = "/rhsm"
        self.vw_etc_d_mode_create(mode, mode, conf_file)
        user, passwd = self.satellite_account_get(server_ip)
        self.vw_option_add("rhsm_hostname", server_ip, conf_file)
        self.vw_option_add("rhsm_port", "443", conf_file)
        self.vw_option_add("rhsm_prefix", rhsm_prefix, conf_file)
        self.vw_option_add("rhsm_username", user, conf_file)
        self.vw_option_add("rhsm_password", passwd, conf_file)

        try:
            org_list = {'step1':default_org, 'step2':extra_org}
            for step, org in sorted(org_list.items(), key=lambda item:item[0]):
                logger.info(">>>%s: run with owner=%s" % (step, org))
                self.vw_option_update_value('owner', '%s' % org, conf_file)
                host_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
                if host_id is not None and host_id != "":
                    self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                if org == default_org:
                    res2 = self.satellite_hosts_search(self.ssh_host(), server_ip, default_org, host_name, host_uuid, exp_exist=True)
                    res3 = self.satellite_hosts_search(self.ssh_host(), server_ip, extra_org, host_name, host_uuid, exp_exist=False)
                else:
                    res2 = self.satellite_hosts_search(self.ssh_host(), server_ip, default_org, host_name, host_uuid, exp_exist=False)
                    res3 = self.satellite_hosts_search(self.ssh_host(), server_ip, extra_org, host_name, host_uuid, exp_exist=True)
                results.setdefault(step, []).append(res1)
                results.setdefault(step, []).append(res2)
                results.setdefault(step, []).append(res3)

            logger.info(">>>step3: run with owner=%s and owner=%s" % (default_org, extra_org))
            self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            cmd = "cp %s %s" % (conf_file, conf_file_2)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc='create conf_file_2')
            self.vw_option_update_value('owner', '%s' % default_org, conf_file)
            self.vw_option_update_value('owner', '%s' % extra_org, conf_file_2)
            self.vw_option_update_value('[.*]', '[esx_2]', conf_file_2)
            data, tty_output, rhsm_output = self.vw_start(exp_send=2)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=2)
            res2 = self.satellite_hosts_search(self.ssh_host(), server_ip, default_org, host_name, host_uuid, exp_exist=True)
            res3 = self.satellite_hosts_search(self.ssh_host(), server_ip, extra_org, host_name, host_uuid, exp_exist=True)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            results.setdefault('step3', []).append(res3)

        except:
            results.setdefault('step', []).append(False)
            pass

        finally:
            logger.info(">>>step finally: delete host/hypervisor from webui")
            host_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
            if host_id is not None and host_id != "":
                self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            self.system_unregister(self.ssh_host())

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/17 Yuefen<yuefliu@redhat.com>
