# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136568')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # case config
        results = dict()
        if hypervisor_type == 'libvirt-remote':
            hypervisor_type = 'libvirt'
        base_cli = self.vw_cli_base() + '-d'
        msg_list = ["owner not in|"
                      "owner.* not set|"
                      "virt-who can't be started"]

        # Case Steps
        logger.info(">>>step1: owner option is good value")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
 
        logger.info(">>>step2: owner option is wrong value")
        cli = self.vw_cli_base_update(base_cli,
                                      '--{0}-owner=.*'.format(hypervisor_type),
                                      '--{0}-owner=xxxxx'.format(hypervisor_type))
        msg_list_2 = ["owner.* is different|"
                      "Communication with subscription manager failed"]
        data, tty_output, rhsm_output = self.vw_start(cli)
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list_2, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: skip this step because owner cannot be set to no-ascci")
        # cli = self.vw_cli_base_update(base_cli,
        #                               '--{0}-owner=.*'.format(hypervisor_type),
        #                               '--{0}-owner=红帽€467aa'.format(hypervisor_type))
        # data, tty_output, rhsm_output = self.vw_start(cli)
        # msg_list = ["codec can't decode|"
        #             "codec can't encode|"
        #             "Communication with subscription manager failed|"
        #             "owner.* is different"]
        # res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        # res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        # results.setdefault('step3', []).append(res1)
        # results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: owner option is null value")
        cli = self.vw_cli_base_update(base_cli,
                                      '--{0}-owner=.*'.format(hypervisor_type),
                                      '--{0}-owner= '.format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: owner option is disable")
        cli = self.vw_cli_base_update(base_cli,
                                      '--{0}-owner=.*'.format(hypervisor_type),
                                      ' ')
        data, tty_output, rhsm_output = self.vw_start(cli)
        res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
        res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        notes = list()
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
