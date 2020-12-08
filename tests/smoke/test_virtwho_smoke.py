# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class VirtWhoSmokeTestCase(Testing):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoSmokeTestCase, cls).setUpClass()
        cls.config_name = "virtwho-config"
        cls.config_file = "/etc/virt-who.d/virtwo_smoke.conf"
        cls.global_file = '/etc/virt-who.conf'
        cls.vw_case_init(cls())
        cls.register_config = cls.get_register_config(cls())
        cls.host_name = cls.get_hypervisor_hostname(cls())
        cls.host_uuid = cls.get_hypervisor_hostuuid(cls())
        cls.host_hwuuid = cls.get_hypervisor_hwuuid(cls())
        cls.guest_name = cls.get_guest_name(cls())
        cls.guest_uuid = cls.get_hypervisor_guestuuid(cls())

    def setUp(self):
        self.vw_etc_conf_disable_all()
        self.vw_etc_sys_disable_all()
        self.vw_etc_d_delete_all()
        self.vw_etc_d_mode_create(self.config_name, self.config_file)
        self.vw_option_enable('[global]', self.global_file)
        self.vw_option_enable('debug', self.global_file)
        self.vw_option_update_value('debug', 'True', self.global_file)

    def get_guest_name(self):
        return self.get_hostname(self.ssh_guest())

    def test_vw_host_to_guest_association(self):
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        assert (self.vw_rhsm_associate(data, self.host_uuid, self.guest_uuid))
        assert (self.vw_web_associate(self.host_name, self.host_uuid, self.guest_name, self.guest_uuid))

    def test_vw_rhsm_options(self):
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.system_unregister(self.ssh_host())
        register_type = self.register_config['type']
        self.vw_option_add("rhsm_hostname", self.register_config['server'], self.config_file)
        self.vw_option_add("rhsm_port", "443", self.config_file)
        self.vw_option_add("rhsm_prefix", self.register_config['prefix'], self.config_file)
        self.vw_option_add("rhsm_username", self.register_config['username'], self.config_file)
        self.vw_option_add("rhsm_password", self.register_config['password'], self.config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        self.system_register(self.ssh_host(), register_type, self.register_config)

    def test_vw_http_proxy(self):
        proxy_server = "{0}:{1}".format(deploy.proxy.server, deploy.proxy.port)
        steps = {'step1':'http_proxy', 'step2':'https_proxy'}
        self.vw_option_enable("[system_environment]", self.global_file)
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to check {1}".format(step, option))
            if option == "http_proxy":
                value = "http://{0}".format(proxy_server)
            if option == "https_proxy":
                value = "https://{0}".format(proxy_server)
            self.vw_option_enable(option, self.global_file)
            self.vw_option_update_value(option, value, self.global_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
            assert (self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server)))
            self.vw_option_disable(option, self.global_file)

    def test_vw_hypervisor_id(self):
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        register_owner = self.register_config['owner']
        if hypervisor_type in ('esx', 'rhevm'):
            hypervisor_ids = ['uuid', 'hostname', 'hwuuid']
        else:
            hypervisor_ids = ['uuid', 'hostname']
        for hypervisor_id in hypervisor_ids:
            if 'hwuuid' in hypervisor_ids:
                if hypervisor_id == "uuid":
                    ids = [self.host_uuid, self.host_name, self.host_hwuuid]
                elif hypervisor_id == "hostname":
                    ids = [self.host_name, self.host_uuid, self.host_hwuuid]
                else:
                    ids = [self.host_hwuuid, self.host_uuid, self.host_name]
            else:
                if hypervisor_id == "uuid":
                    ids = [self.host_uuid, self.host_name]
                else:
                    ids = [self.host_name, self.host_uuid]
            logger.info(">>> check hypervisor_id in rhsm.log")
            self.vw_option_add("hypervisor_id", hypervisor_id, self.config_file)
            data, tty_output, rhsm_output = self.vw_start()
            assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
            assert (ids[0] in data[register_owner].keys())
            logger.info(">>> check only single hypervisor name on Satellite WebUI")
            ssh_sat = self.register_config["ssh_sat"]
            admin_user = self.register_config['username']
            admin_passwd = self.register_config['password']
            cmd = "hammer -u {0} -p {1} host list --search 'name ~ virt-who*'".format(
                admin_user, admin_passwd)
            ret, result = self.runcmd(cmd, ssh_sat)
            assert (self.vw_msg_search(result, "virt-who-" + ids[0]), True)
            assert (self.vw_msg_search(result, "virt-who-" + ids[1], False))
            if 'hwuuid' in hypervisor_ids:
                assert (self.vw_msg_search(result, "virt-who-" + ids[2], False))
            self.vw_option_del("hypervisor_id", self.config_file)

    def test_vw_vdc_subscription(self):
        vdc_physical_sku = self.register_config['vdc']
        vdc_virtual_sku = self.register_config['vdc_bonus']
        data, tty_output, rhsm_output = self.vw_start()
        assert(self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        logger.info(">>> attach virtual vdc pool for guest")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_host(), vdc_physical_sku, "physical")
        self.vw_web_attach(self.host_name, self.host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), vdc_virtual_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert(self.vw_msg_search(output, vdc_virtual_sku, exp_exist=True))
        ret, output = self.runcmd('subscription-manager repos --list', self.ssh_guest())
        assert(self.vw_msg_search(output, "no repositories available" , exp_exist=True))
        ret, output = self.runcmd('subscription-manager status', self.ssh_guest())
        assert(self.vw_msg_search(output, "Overall Status: Current" , exp_exist=True))
        assert(self.vw_msg_search(output, "Invalid" , exp_exist=False))
        logger.info(">>> virtual vdc pool is revoked after unattach physical sku")
        self.vw_web_unattach(self.host_name, self.host_uuid)
        output = self.system_sku_consumed(self.ssh_guest(), exp_exist=False)
        assert (self.vw_msg_search(output, vdc_virtual_sku, exp_exist=False))

    def test_virtwho_limited_subscription(self):
        limited_sku = self.register_config['limit']
        data, tty_output, rhsm_output = self.vw_start()
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        logger.info(">>> attach virtual limited pool for guest")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_host(), limited_sku, "physical")
        self.vw_web_attach(self.host_name, self.host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), limited_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, limited_sku))
        ret, output = self.runcmd('subscription-manager repos --list', self.ssh_guest())
        assert (self.vw_msg_search(output, "no repositories available"))
        ret, output = self.runcmd('subscription-manager status', self.ssh_guest())
        assert (self.vw_msg_search(output, "Overall Status: Current"))
        assert (self.vw_msg_search(output, "Invalid", exp_exist=False))
        logger.info(">>> no virtual limit pool for guest any more")
        output = self.system_sku_attr(self.ssh_guest(), limited_sku, "virtual", exp_exist=False)
        assert (self.vw_msg_search(str(output), limited_sku, exp_exist=False))
        logger.info(">>> limit bonus pool is revoked after unattach physical sku")
        self.vw_web_unattach(self.host_name, self.host_uuid)
        output = self.system_sku_consumed(self.ssh_guest(), exp_exist=False)
        assert (self.vw_msg_search(output, limited_sku, exp_exist=False))

    def test_virtwho_unlimited_subscription(self):
        unlimited_sku = self.register_config['unlimit']
        data, tty_output, rhsm_output = self.vw_start()
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        logger.info(">>> attach virtual unlimit pool for guest")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_host(), unlimited_sku, "physical")
        self.vw_web_attach(self.host_name, self.host_uuid, sku_attrs['pool_id'])
        sku_attrs = self.system_sku_attr(self.ssh_guest(), unlimited_sku, "virtual")
        self.system_sku_attach(self.ssh_guest(), pool_id=sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, unlimited_sku))
        logger.info(">>>  virtual unlimit sku can be listed in guest ")
        output = self.system_sku_attr(self.ssh_guest(), unlimited_sku, "virtual")
        assert (self.vw_msg_search(str(output), unlimited_sku))
        logger.info(">>> virtual unlimit pool is revoked after unattach physical sku")
        self.vw_web_unattach(self.host_name, self.host_uuid)
        output = self.system_sku_consumed(self.ssh_guest(), exp_exist=False)
        assert (self.vw_msg_search(output, unlimited_sku, exp_exist=False))

    def test_virtwho_instance_subscription(self):
        instance_sku = self.register_config['instance']
        logger.info(">>> set cpu.cpu_socket(s) to 8 in guest")
        assert (self.system_custom_facts_create(self.ssh_guest(), 'cpu.cpu_socket(s)', '8'))
        logger.info(">>> attach physical instance sku for guest without quantity")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        self.system_sku_attach(self.ssh_guest(), sku_attrs['pool_id'])
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, instance_sku))
        assert (self.vw_msg_search(output, 'Quantity Used:.*1'))
        assert (self.vw_msg_search(output, 'Status Details:.*Subscription is current'))
        logger.info(">>> attach physical instance sku for guest with quantity=1")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        self.system_sku_attach(self.ssh_guest(), sku_attrs['pool_id'], quantity=1)
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, instance_sku))
        assert (self.vw_msg_search(output, 'Quantity Used:.*1'))
        assert (self.vw_msg_search(output, 'Status Details:.*Subscription is current'))
        logger.info(">>> attach physical instance sku for guest with quantity=2")
        self.system_sku_unattach(self.ssh_guest())
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        self.system_sku_attach(self.ssh_guest(), sku_attrs['pool_id'], quantity=2)
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, instance_sku))
        assert (self.vw_msg_search(output, 'Quantity Used:.*2'))
        assert (self.vw_msg_search(output, 'Status Details:.*Subscription is current'))
        logger.info(">>> attach physical instance sku for guest with quantity=6")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), instance_sku, "physical")
        self.system_sku_attach(self.ssh_guest(), sku_attrs['pool_id'], quantity=6)
        output = self.system_sku_consumed(self.ssh_guest())
        assert (self.vw_msg_search(output, instance_sku, exp_exist=True))
        assert (self.vw_msg_search(output, 'Quantity Used:.*2'))
        assert (self.vw_msg_search(output, 'Quantity Used:.*6'))
        assert (self.vw_msg_search(output, 'Status Details:.*Subscription is current'))
        self.system_custom_facts_remove(self.ssh_guest())

    def test_temporary_sku(self):
        logger.info(">>> check virtual temporary sku exist in guest")
        self.system_sku_refresh(self.ssh_guest())
        ret, output = self.runcmd("subscription-manager list --av", self.ssh_guest())
        assert (self.vw_msg_search(output, 'Subscription Type: .*Temporary', exp_exist=True))
        logger.info(">>> run virt-who service and check temporary sku disappear")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        assert (self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1))
        self.system_sku_refresh(self.ssh_guest())
        ret, output = self.runcmd("subscription-manager list --av", self.ssh_guest())
        assert (self.vw_msg_search(output, 'Subscription Type: .*Temporary', exp_exist=False))
