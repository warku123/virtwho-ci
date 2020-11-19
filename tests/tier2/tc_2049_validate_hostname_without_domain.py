# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136708')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type not in ("esx", "libvirt-remote"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        config = self.get_hypervisor_config()
        ssh_hypervisor = config['ssh_hypervisor']
        register_config = self.get_register_config()
        register_type = register_config['type']
        guest_name = config['guest_name']
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        hostname_non_domain = host_name.split('.')[0]
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_option_add('hypervisor_id', 'hostname', config_file)
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')

        # case steps
        try:
            logger.info(">>>step1: run virt-who for hostname without domain name")
            if hypervisor_type == "esx":
                cert = self.vcenter_cert(config['server'], config['username'], config['password'])
                esx_host = self.vcenter_host_get(cert, ssh_hypervisor, guest_name)
                self.vcenter_fqdn_set(cert, ssh_hypervisor, esx_host, hostname_non_domain)
            if hypervisor_type == "libvirt-remote":
                self.set_hostname(hostname_non_domain, ssh_hypervisor)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(str(data), hostname_non_domain, exp_exist=True)
            res3 = self.vw_msg_search(str(data), host_name, exp_exist=False)
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            results.setdefault('step1', []).append(res3)
        except:
            results.setdefault('step1', []).append(False)
            pass
        finally:
            logger.info(">>>step2: start to recovery hostname")
            if "satellite" in register_type:
                self.vw_web_host_delete(hostname_non_domain, host_uuid)
            if "stage" in register_type:
                self.stage_consumer_clean(self.ssh_host(), register_config)
            if hypervisor_type == "esx":
                cert = self.vcenter_cert(config['server'], config['username'], config['password'])
                esx_host = self.vcenter_host_get(cert, ssh_hypervisor, guest_name)
                self.vcenter_fqdn_set(cert, ssh_hypervisor, esx_host, host_name)
            if hypervisor_type == "libvirt-remote":
                self.set_hostname(host_name, ssh_hypervisor)
            if self.get_hypervisor_hostname() == host_name:
                logger.info('Succeeded to change back hostname')
                results.setdefault('step2', []).append(True)
            else:
                logger.error('Failed to change back hostname')
                results.setdefault('step2', []).append(False)

        # Case Result
        notes = list()
        notes.append("Only for libvirt-remote bug: https://bugzilla.redhat.com/show_bug.cgi?id=1874371")
        self.vw_case_result(results, notes)
