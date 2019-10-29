# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class VirtWhoGatingTestCase(Testing):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoGatingTestCase, cls).setUpClass()
        cls.config_name = "virtwho-config"
        cls.config_file = "/etc/virt-who.d/virtwo_gating.conf"
        cls.sys_file = '/etc/sysconfig/virt-who'
        cls.global_file = '/etc/virt-who.conf'
        cls.vw_case_init(cls())
        cls.host_name = cls.get_hypervisor_hostname(cls())
        cls.host_uuid = cls.get_hypervisor_hostuuid(cls())
        cls.host_hwuuid = cls.get_hypervisor_hwuuid(cls())
        cls.guest_name = cls.get_guest_name(cls())
        cls.guest_uuid = cls.get_hypervisor_guestuuid(cls())

    def setUp(self):
        self.vw_etc_conf_disable_all()
        self.vw_etc_sys_disable_all()
        self.vw_etc_d_delete_all()

    def get_guest_name(self):
        return self.get_hostname(self.ssh_guest())

    def test_virtwho_debug(self):
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        self.vw_option_enable('VIRTWHO_DEBUG', self.sys_file)
        self.vw_option_update_value('VIRTWHO_DEBUG', '1', self.sys_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert(self.vw_msg_search(rhsm_output, msg="\[.*DEBUG\]", exp_exist=True))
        self.vw_option_update_value('VIRTWHO_DEBUG', '0', self.sys_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert(self.vw_msg_search(rhsm_output, msg="\[.*DEBUG\]", exp_exist=False))
        self.vw_option_disable('VIRTWHO_DEBUG', self.sys_file)

    def test_virtwho_oneshot(self):
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        data, tty_output, rhsm_output = self.vw_start(
            'virt-who -o', exp_send=1, oneshot=True)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1))
        data, tty_output, rhsm_output = self.vw_start(
            'virt-who', exp_send=1, oneshot=False)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))

    def test_virtwho_interval(self):
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        self.vw_option_enable('VIRTWHO_DEBUG', self.sys_file)
        self.vw_option_update_value('VIRTWHO_DEBUG', '1', self.sys_file)
        self.vw_option_enable('VIRTWHO_INTERVAL', self.sys_file)
        self.vw_option_update_value('VIRTWHO_INTERVAL', '60', self.sys_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1, exp_loopnum=1)
        assert(self.op_normal_value(
            data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60,
            exp_loopnum=1, exp_looptime=60))

    def test_virtwho_hypervisor_id(self):
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        self.vw_option_enable('[global]', self.global_file)
        self.vw_option_enable('debug', self.global_file)
        self.vw_option_update_value('debug', 'True', self.global_file)
        register_config = self.get_register_config()
        register_type = register_config['type']
        register_owner = register_config['owner']
        hypervisor_type = self.get_config('hypervisor_type')
        steps = {'step1':'uuid', 'step2':'hostname'}
        if hypervisor_type in ('esx', 'rhevm'):
            steps['step3'] = 'hwuuid'
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            self.vw_option_add("hypervisor_id", option, self.config_file)
            data, tty_output, rhsm_output = self.vw_start()
            assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
            if option == "hwuuid":
                hypervisorId = self.host_hwuuid
            elif option == "hostname":
                hypervisorId = self.host_name
            else:
                hypervisorId = self.host_uuid
            assert(hypervisorId in data[register_owner].keys())
            self.vw_option_del("hypervisor_id", self.config_file)

    def test_virtwho_fake_mode(self):
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        hypervisor_type = self.get_config('hypervisor_type')
        json_file = "/tmp/fake.json"
        conf_file = "/etc/virt-who.d/fake.conf"
        self.vw_fake_json_create('virt-who -d', json_file)
        self.vw_etc_d_delete_all()
        self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=True)
        data, tty_output, rhsm_output = self.vw_start(cli="virt-who -d")
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert(self.vw_rhsm_associate(data, self.host_uuid, self.guest_uuid))
        sku_attrs = self.system_sku_attr(self.ssh_host(), "RH00001", "physical")
        self.vw_web_attach(self.host_name, self.host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), "RH00049", "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert(self.vw_msg_search(output, 'RH00049', exp_exist=True))

    def test_virtwho_rhsm_options(self):
        self.system_unregister(self.ssh_host())
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        self.vw_option_enable('[global]', self.global_file)
        self.vw_option_enable('debug', self.global_file)
        self.vw_option_update_value('debug', 'True', self.global_file)
        register_config = self.get_register_config()
        register_type = register_config['type']
        self.vw_option_add("rhsm_hostname", register_config['server'], self.config_file)
        self.vw_option_add("rhsm_port", "443", self.config_file)
        self.vw_option_add("rhsm_prefix", register_config['prefix'], self.config_file)
        self.vw_option_add("rhsm_username", register_config['username'], self.config_file)
        self.vw_option_add("rhsm_password", register_config['password'], self.config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        self.system_register(self.ssh_host(), register_type, register_config)

    def test_virtwho_vdc_subscription(self):
        self.vw_case_init()
        self.vw_option_enable('[global]', self.global_file)
        self.vw_option_enable('debug', self.global_file)
        self.vw_option_update_value('debug', 'True', self.global_file)
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        register_config = self.get_register_config()
        register_type = register_config['type']
        vdc_physical_sku = register_config['vdc']
        vdc_virtual_sku = register_config['vdc_bonus']
        data, tty_output, rhsm_output = self.vw_start()
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        self.vw_web_attach(self.host_name, self.host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert(self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True))
        ret, output = self.runcmd('subscription-manager repos --list', self.ssh_guest())
        if "stage" in register_type:
            assert(self.vw_msg_search(output, "Available Repositories" , exp_exist=True))
        else:
            assert(self.vw_msg_search(output, "no repositories available" , exp_exist=True))
        ret, output = self.runcmd('subscription-manager status', self.ssh_guest())
        assert(self.vw_msg_search(output, "Overall Status: Current" , exp_exist=True))
        assert(self.vw_msg_search(output, "Invalid" , exp_exist=False))
