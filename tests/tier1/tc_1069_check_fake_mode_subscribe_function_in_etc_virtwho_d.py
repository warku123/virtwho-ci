# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133680')
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        hypervisor_type = self.get_config('hypervisor_type')
        host_name = self.get_hypervisor_hostname()
        host_uuid = self.get_hypervisor_hostuuid()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()
        json_file = "/tmp/fake.json"
        conf_file = "/etc/virt-who.d/fake.conf"

        # case steps
        logger.info(">>>step1: create json file")
        cli = "virt-who -d"
        self.vw_fake_json_create(cli, json_file)
        self.vw_etc_d_delete_all()
        if "libvirt-local" in hypervisor_type or "vdsm" in hypervisor_type:
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=False)
        else:
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=True)

        logger.info(">>>step2: run virt-who with fake conf")
        data, tty_output, rhsm_output = self.vw_start(cli="virt-who -d")
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: attach physical sku for host/hypervisor")
        sku_attrs = self.system_sku_attr(self.ssh_host(), "RH00002", "physical")
        pool_id = sku_attrs['pool_id']
        self.vw_web_attach(host_name, host_uuid, pool_id)

        logger.info(">>>step4: attach bonus sku for guest")
        sku_attrs = self.system_sku_attr(self.ssh_guest(), "RH00050", "virtual")
        pool_id = sku_attrs['pool_id']
        self.system_sku_attach(self.ssh_guest(), pool_id=pool_id)
        output = self.system_sku_consumed(self.ssh_guest())
        res = self.vw_msg_search(output, 'RH00050', exp_exist=True)
        results.setdefault('step4', []).append(res)

        # case result
        self.vw_case_result(results)
