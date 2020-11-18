# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-196078')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type != 'esx':
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        config = self.get_hypervisor_config()
        ssh_hypervisor = config['ssh_hypervisor']
        register_config = self.get_register_config()
        server = register_config['server']
        ssh_user = register_config['ssh_user']
        ssh_passwd = register_config['ssh_passwd']
        ssh_register = {"host": server, "username": ssh_user, "password": ssh_passwd}

        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        host_uuid = self.get_hypervisor_hostuuid()
        host_name = self.get_hypervisor_hostname()

        cert = self.vcenter_cert(config['server'], config['username'], config['password'])
        cluster_name = self.vcenter_cluster_get(cert, ssh_hypervisor)
        new_cluster_name = "virtwho/test"

        # Case Steps
        try:
            logger.info(">>>step1: change the vcenter cluster name to: virtwho/test")
            self.vcenter_cluster_name_set(cert, ssh_hypervisor, cluster_name, new_cluster_name)

            logger.info(">>>step2: run virt-who service with the new cluster name")
            data, tty_output, rhsm_output = self.vw_start(exp_error=0, exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res1)

            logger.info(">>>step3: check the hyperivsor fact by hammer command")
            output = self.satellite_hosts_get(self.ssh_host(), register_config,
                                              host_name, host_uuid, "get hypervisor info")
            cmd = "hammer host facts --name {}".format(output['name'])
            _, result = self.runcmd(cmd, ssh_register)

            self.vw_msg_search(result, new_cluster_name)
            self.vw_msg_search(result, cluster_name, False)

        finally:
            logger.info(">>>step finally: change back the vcenter cluster name")
            self.vcenter_cluster_name_set(cert, ssh_hypervisor, new_cluster_name, cluster_name)

        # Case Result
        self.vw_case_result(results)
