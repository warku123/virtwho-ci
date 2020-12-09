# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133649')
        self.vw_case_init()

        # case config
        results = dict()
        compose_id = self.get_config('rhel_compose')
        if "RHEL-7" in compose_id:
            cmd = self.vw_cli_base()
            cmd_oneshot = self.vw_cli_base() + "-o"
        else:
            config_name = "virtwho-config"
            config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
            self.vw_etc_d_mode_create(config_name, config_file)
            cmd = "virt-who"
            cmd_oneshot = "virt-who -o"

        # case step
        logger.info(">>>step1: Run virt-who by cli with -o option")
        data, tty_output, rhsm_output = self.vw_start(cmd_oneshot, exp_send=1,
                                                      oneshot=True)
        res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: Run virt-who by cli without -o option")
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1, oneshot=False)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)

        # case result
        notes = list()
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
