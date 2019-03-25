# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133743')
        hypervisor1_type = self.get_exported_param("HYPERVISOR_01_TYPE")
        hypervisor2_type = self.get_exported_param("HYPERVISOR_02_TYPE")
        if not hypervisor1_type or not hypervisor2_type:
            raise FailException("need two hypervisor env")
        if "libvirt-local" in hypervisor1_type or "vdsm" in hypervisor1_type or \
                "libvirt-local" in hypervisor2_type or "vdsm" in hypervisor2_type:
            self.vw_case_skip("libvirt-local or vdsm")
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.23.3':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable("VIRTWHO_DEBUG", filename=config_file)
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename=config_file)
        self.vw_etc_sys_mode_enable(uid='01')
        self.vw_etc_sys_mode_enable(uid='02')

        # case steps
        logger.info(">>>step1: check reporter sent and no error msg")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check how many modes in rhsm.log")
        modes = re.findall(r'Using configuration.*\("(.*?)" mode\)', rhsm_output)
        if len(modes) == 1:
            logger.info("Succeeded to check, only one mode in rhsm.log: {0}".format(modes)
            results.setdefault('step2', []).append(True)
        else:
            logger.error("Failed to check, the modes number is not matched: {0}".format(modes))
            results.setdefault('step2', []).append(False)

        # case result
        self.vw_case_result(results)
