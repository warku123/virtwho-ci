# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137110")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename='/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename='/etc/sysconfig/virt-who')
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, conf_file)
        default_org = args_satellite['default_owner']
        extra_org = args_satellite['extra_owner']
        org_list = {'step1':default_org, 'step2':extra_org}

        try:
            for step, org in sorted(org_list.items(), key=lambda item:item[0]):
                logger.info(">>>%s: run with owner=%s" % (step, org))
                if 'libvirt-local' not in mode and 'vdsm' not in mode:
                    self.vw_option_update_value('owner', '%s' % org, conf_file)
                host_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
                if host_id is not None and host_id != "":
                    self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
                self.system_unregister(self.ssh_host())
                self.vw_sub_register(self.ssh_host(), org)
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

        except:
            results.setdefault('step', []).append(False)
            pass

        finally:
            logger.info(">>>step finally: delete host and hypervisor from extra_org")
            host_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
            if host_id is not None and host_id != "":
                self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            self.system_unregister(self.ssh_host())

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/17 Yuefen<yuefliu@redhat.com>
