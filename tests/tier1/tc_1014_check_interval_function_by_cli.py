# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133650')
        self.vw_case_init()

        # case config
        results = dict()
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            config_name = "virtwho-config"
            config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
            self.vw_etc_d_mode_create(config_name, config_file)
            cmd = "virt-who -d"
            cmd_i_10 = "virt-who -d -i 10"
            cmd_i_60 = "virt-who -d -i 60"
            cmd_i_120 = "virt-who -d -i 120"
        else:
            cmd = self.vw_cli_base() + "-d"
            cmd_i_10 = self.vw_cli_base() + "-d -i 10"
            cmd_i_60 = self.vw_cli_base() + "-d -i 60"
            cmd_i_120 = self.vw_cli_base() + "-d -i 120"

        # case steps
        logger.info(">>>step1: run virt-who without -i option")
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1,
                                   exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who with -i 10 option")
        msg = "Interval value can't be lower than 60 seconds. " \
              "Default value of 3600 seconds will be used"
        data, tty_output, rhsm_output = self.vw_start(cmd_i_10, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1,
                                    exp_send=1, exp_interval=3600)
        res2 = self.vw_msg_search(tty_output, msg, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: run virt-who with -i 60 option")
        data, tty_output, rhsm_output = self.vw_start(cmd_i_60, exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1,
                                   exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step4: run virt-who with -i 120 option")
        data, tty_output, rhsm_output = self.vw_start(cmd_i_120, exp_send=1,
                                                      exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1,
                                   exp_interval=120, exp_loopnum=1, exp_looptime=120)
        results.setdefault('step4', []).append(res)

        # case result
        notes = list()
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2,3,4) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
