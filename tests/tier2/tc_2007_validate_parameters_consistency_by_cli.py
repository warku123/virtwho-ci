# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136710')
        hypervisor_type = self.get_config('hypervisor_type')
        compose_id = self.get_config('rhel_compose')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # Case Config
        results = dict()
        if hypervisor_type == 'libvirt-remote':
            hypervisor_type = 'libvirt'
            wrong_mode = 'xen'
        else:
            wrong_mode = 'libvirt'
        base_cli = self.vw_cli_base() + '-d'

        # Case Steps
        logger.info(">>>step1: run virt-who by cli with all valid parameters")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who by cli with unconsistent parameters")
        cli = re.sub("--{0}-owner=".format(hypervisor_type),
                     "--{0}-owner=".format(wrong_mode),
                     base_cli)
        data, tty_output, rhsm_output = self.vw_start(cli, exp_send=1)
        msg = "does not match virtualization backend"
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(tty_output, msg, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # Case Result
        self.vw_case_result(results)