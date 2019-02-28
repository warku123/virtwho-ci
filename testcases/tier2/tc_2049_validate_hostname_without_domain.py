# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136640")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "esx" not in mode and "libvirt-remote" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        host_uuid = self.mode_host_uuid(mode)
        hostname_original = self.mode_host_name(mode)
        hostname_non_domain = hostname_original.split('.')[0]
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        self.vw_option_add('hypervisor_id', 'hostname', conf_file)
        self.vw_option_enable("VIRTWHO_DEBUG", '/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', '/etc/sysconfig/virt-who')

        # Case Steps
        try:
            logger.info(">>>step1: run virt-who for hostname without domain name")
            if mode == "esx":
                cmd = 'esxcli system hostname set --fqdn=%s' % hostname_non_domain
                ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
                ret, output = self.runcmd(cmd, ssh_esx_master, desc="update hostname")
            if mode == "libvirt-remote":
                ssh_libvirt = self.ssh_libvirt_env(mode)
                host_ip = self.get_ipaddr(ssh_libvirt)
                etc_hosts_value = "%s %s" % (host_ip, hostname_non_domain)
                self.set_hostname(hostname_non_domain, ssh_libvirt)
                self.set_etc_hosts(etc_hosts_value, ssh_libvirt)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(str(data), hostname_non_domain, exp_exist=True)
            res3 = self.vw_msg_search(str(data), hostname_original, exp_exist=False)
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            results.setdefault('step1', []).append(res3)
        except:
            results.setdefault('step1', []).append(False)
            pass
        finally:
            logger.info(">>>step2: start to recovery hostname")
            if "satellite" in server_type:
                self.vw_web_host_delete(self.ssh_host(), hostname_non_domain, host_uuid)
            if "stage" in server_type:
                self.stage_consumer_clean(self.ssh_host(), mode)
            if mode == "esx":
                cmd = 'esxcli system hostname set --fqdn=%s' % hostname_original
                ret, output = self.runcmd(cmd, ssh_esx_master)
            if mode == "libvirt-remote":
                etc_hosts_value = "%s %s" % (host_ip, hostname_original)
                self.set_hostname(hostname_original, ssh_libvirt)
                self.set_etc_hosts(etc_hosts_value, ssh_libvirt)
            if self.mode_host_name(mode) == hostname_original:
                logger.info('Succeeded to change back hostname')
                results.setdefault('step2', []).append(True)
            else:
                logger.error('Failed to change back hostname')
                results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/19 Yuefen<yuefliu@redhat.com>
