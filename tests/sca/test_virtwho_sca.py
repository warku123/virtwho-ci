# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class VirtWhoSCATestCase(Testing):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoSCATestCase, cls).setUpClass()
        register_config = cls.get_register_config(cls())
        if 'satellite' in register_config['type']:
            cls.satellite_sca_set(cls(), cls.ssh_host(cls()), register_config, enable=True)
        else:
            cls.stage_sca_set(cls(), cls.ssh_host(cls()), register_config, enable=True)
        cls.register_owner = register_config['owner']
        cls.vw_case_init(cls())
        cls.vw_etc_conf_disable_all(cls())
        cls.vw_etc_sys_disable_all(cls())
        cls.vw_etc_d_delete_all(cls())
        cls.vw_etc_d_mode_create(cls(), 'virtwho-config', '/etc/virt-who.d/virtwo_sca.conf')
        cls.vw_option_enable(cls(), '[global]', '/etc/virt-who.conf')
        cls.vw_option_enable(cls(), 'debug', '/etc/virt-who.conf')
        cls.vw_option_update_value(cls(), 'debug', 'True', '/etc/virt-who.conf')
        cls.host_uuid = cls.get_hypervisor_hostuuid(cls())
        cls.host_name = cls.get_hypervisor_hostname(cls())
        cls.guest_name = cls.get_guest_name(cls())
        cls.guest_uuid = cls.get_hypervisor_guestuuid(cls())

    @classmethod
    def tearDownClass(cls):
        register_config = cls.get_register_config(cls())
        if 'satellite' in register_config['type']:
            cls.satellite_sca_set(cls(), cls.ssh_host(cls()), register_config, enable=False)
        else:
            cls.stage_sca_set(cls(), cls.ssh_host(cls()), register_config, enable=False)

    def get_guest_name(self):
        return self.get_hostname(self.ssh_guest())

    def test_vw_report_mapping_with_sca_enabled(self):
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        logger.info(f"---data is: {data}---")
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert (self.register_owner in data.keys())
        assert (self.host_uuid in data[self.register_owner].keys())
        assert (self.guest_uuid in data[self.register_owner].keys())

        # test hypervisor facts
        facts_items = ['socket', 'type', 'dmi', 'version']
        if self.get_config('hypervisor_type') in ('esx', 'rhevm', 'ahv'):
            facts_items.append('cluster')
        facts_dic = data[self.register_owner][self.host_uuid]
        for item in facts_items:
            assert (item in facts_dic.keys())
            assert (facts_dic[item] is not None)

    def test_vw_host_to_guest_association(self):
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert (self.vw_rhsm_associate(data, self.host_uuid, self.guest_uuid))
        assert (self.vw_web_associate(self.host_name, self.host_uuid, self.guest_name, self.guest_uuid))

    def test_guest_entilement_with_sca_enabled(self):
        ret, output = self.runcmd(cmd='subscription-manager status', ssh=self.ssh_guest())
        assert ('Content Access Mode is set to Simple Content Access' in output)

    def test_hypervisor_in_web(self):
        pass
