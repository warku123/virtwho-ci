# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-198374')
        compose_id = self.get_config('rhel_compose')
        if "RHEL-9" not in compose_id:
            self.vw_case_skip(compose_id)
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        hypervisor_type = self.get_config('hypervisor_type')
        json_file = "/tmp/fake.json"
        fake_config_file = "/etc/virt-who.d/fake.conf"

        # case steps
        logger.info(">>>step1: create json file")
        self.vw_fake_json_create("virt-who -d -p", json_file)
        ret, fake_json = self.runcmd("cat {0}".format(json_file), self.ssh_host())
        self.vw_etc_d_delete_all()

        logger.info(">>>step2: check the mapping in json file is same with debug output")
        if hypervisor_type in ("libvirt-local", "vdsm"):
            self.vw_fake_conf_create(fake_config_file, json_file, is_hypervisor=False)
        else:
            self.vw_fake_conf_create(fake_config_file, json_file, is_hypervisor=True)
        data, tty_output, rhsm_output = self.vw_start(cli='virt-who -do', exp_send=1)
        results.setdefault('step2', []).append(fake_json in tty_output)

        # case result
        self.vw_case_result(results)
