# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-188359')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        register_config = self.get_register_config()
        server = register_config['server']
        ssh_user = register_config['ssh_user']
        ssh_passwd = register_config['ssh_passwd']
        ssh_register = {"host": server, "username": ssh_user, "password": ssh_passwd}
        admin_user = register_config['username']
        admin_passwd = register_config['password']
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_option_add("hypervisor_id", "hostname", config_file)
        json_file = "/tmp/fake.json"
        conf_file = "/etc/virt-who.d/fake.conf"
        host_name = self.get_hypervisor_hostname()

        # Case Steps
        logger.info(">>>step1: create fake json file")
        cli = "virt-who"
        self.vw_fake_json_create(cli, json_file)
        self.vw_etc_d_delete_all()
        self.vw_fake_conf_create(conf_file, json_file, True)

        logger.info(">>>step2: run virt-who with fake conf")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res1)

        logger.info(">>>step3: use hammer command to check hypervisor's fqdn")
        cmd = "hammer -u {0} -p {1} host list --search 'name ~ virt-who*'".format(admin_user, admin_passwd)
        _, result = self.runcmd(cmd, ssh_register)
        self.vw_msg_search(result, "virt-who-"+host_name)

        logger.info(">>>step4: run virt-who with the new hypervisor's fqdn")
        new_name = "newserver.rhts.eng.pek2.redhat.com"
        self.vw_fake_json_update(host_name, new_name, json_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res2 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: use hammer command to check the new hypervisor's fqdn")
        cmd = "hammer -u {0} -p {1} host list --search 'name ~ virt-who*'".format(admin_user, admin_passwd)
        _, result = self.runcmd(cmd, ssh_register)
        self.vw_msg_search(result, "virt-who-"+new_name)
        self.vw_msg_search(result, "virt-who-"+host_name, False)

        # Case Result
        self.vw_case_result(results)
