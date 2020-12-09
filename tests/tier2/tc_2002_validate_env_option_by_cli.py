# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136571')
        hypervisor_type = self.get_config('hypervisor_type')
        compose_id = self.get_config('rhel_compose')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if "RHEL-7" not in compose_id:
            self.vw_case_skip(compose_id)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        if hypervisor_type == 'libvirt-remote':
            hypervisor_type = 'libvirt'
        base_cli = self.vw_cli_base() + '-d'

        # Case Steps
        logger.info(">>>step1: env option is good value")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: env option is wrong value")
        cli = self.vw_cli_base_update(base_cli, "--{0}-env=.*".format(hypervisor_type),
                                      "--{0}-env=xxxxx".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["env.*differs|"
                    "env.* is different|"
                    "Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: env option is 红帽€467aa value")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-env=.*".format(hypervisor_type),
                                      "--{0}-env=红帽€467aa".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["codec can't decode|"
                    "Communication with subscription manager failed|"
                    "env.*differs"]
        res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: env option is null value")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-env=.*".format(hypervisor_type),
                                      "--{0}-env= ".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["env not in|env.* not set|"
                    "virt-who can't be started"]
        res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: env option is disable")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-env=.*".format(hypervisor_type),
                                      " ")
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["env not in|env.* not set|virt-who can't be started"]
        res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        notes = list()
        register_type = self.get_config('register_type')
        if "stage" in register_type:
            notes.append("Bug(Step2,Step3): Set env to wrong or special value,"
                         " still can sent report normally for stage")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530426")
        self.vw_case_result(results, notes)
