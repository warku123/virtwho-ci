# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133742')
        hypervisor1_type = self.get_exported_param("HYPERVISOR_01_TYPE")
        hypervisor2_type = self.get_exported_param("HYPERVISOR_02_TYPE")
        if not hypervisor1_type or not hypervisor2_type:
            raise FailException("This case needs two hypervisors for testing")
        if any(key in ('libvirt-local', 'vdsm') for key in (hypervisor1_type, hypervisor2_type)):
            self.vw_case_skip("libvirt-local or vdsm")
        self.vw_case_init(uid='01')

        # case config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_01_name = "virtwho-config-{0}".format(hypervisor1_type)
        config_01_file = "/etc/virt-who.d/{0}.conf".format(config_01_name)
        config_02_name = "virtwho-config-{0}".format(hypervisor2_type)
        config_02_file = "/etc/virt-who.d/{0}.conf".format(config_02_name)
        host_01_uuid = self.get_hypervisor_hostuuid(uid='01')
        host_02_uuid = self.get_hypervisor_hostuuid(uid='02')
        guest_01_uuid = self.get_hypervisor_guestuuid(uid='01')
        guest_02_uuid = self.get_hypervisor_guestuuid(uid='02')
        json_file = "/tmp/fake.json"
        fake_conf_file = "/etc/virt-who.d/fake.conf"

        # case steps
        logger.info(">>>step1: create json file and fake config file")
        self.vw_etc_d_mode_create(config_01_name, config_01_file, uid='01')
        self.vw_etc_d_mode_create(config_02_name, config_02_file, uid='02')
        self.vw_fake_json_create("virt-who", json_file)
        self.vw_etc_d_delete_all()
        self.vw_fake_conf_create(fake_conf_file, json_file, is_hypervisor=True)

        logger.info(">>>step2: run virt-who with fake conf")
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_rhsm_associate(data, host_01_uuid, guest_01_uuid, uid='01')
        res3 = self.vw_rhsm_associate(data, host_02_uuid, guest_02_uuid, uid='02')
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        # case result
        self.vw_case_result(results)
