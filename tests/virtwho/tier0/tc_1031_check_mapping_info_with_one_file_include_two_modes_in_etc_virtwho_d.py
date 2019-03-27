# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133733')
        hypervisor1_type = self.get_exported_param("HYPERVISOR_01_TYPE")
        hypervisor2_type = self.get_exported_param("HYPERVISOR_02_TYPE")
        if not hypervisor1_type or not hypervisor2_type:
            raise FailException("need two hypervisor env")
        if "libvirt-local" in hypervisor1_type or "vdsm" in hypervisor1_type or \
                "libvirt-local" in hypervisor2_type or "vdsm" in hypervisor2_type:
            self.vw_case_skip("libvirt-local or vdsm")
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
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
        guest_01_uuid = self.get_hypervisor_guestuuid(uid='01')
        guest_02_uuid = self.get_hypervisor_guestuuid(uid='02')
        
        # case steps
        logger.info(">>>step1: create config file include two different hypervisors")
        self.vw_etc_d_mode_create(config_01_name, config_01_file, uid='01')
        self.vw_etc_d_mode_create(config_02_name, config_02_file, uid='02')
        cmd = 'cat {0} >> {1} && rm -rf {0}'.format(config_02_file, config_01_file)
        ret, output = self.runcmd(cmd, self.ssh_host())
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check mapping info included two hypervisors")
        res1 = self.vw_msg_search(str(data), guest_01_uuid, exp_exist=True)
        res2 = self.vw_msg_search(str(data), guest_02_uuid, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # case result
        self.vw_case_result(results)
