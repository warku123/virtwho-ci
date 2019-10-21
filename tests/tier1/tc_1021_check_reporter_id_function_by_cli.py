# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134123')
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # case config
        results = dict()
        reporter_id = "virtwho_reporter_id_tc1021"
        cmd1 = self.vw_cli_base() + "-d -r {0}".format(reporter_id)
        cmd2 = self.vw_cli_base() + "-d --reporter-id {0}".format(reporter_id)
        steps = {'step1': cmd1, 'step2': cmd2}

        # case steps
        for step, cmd in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(">>>{0}: run virt-who cli to check reporter_id".format(step))
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            if data['reporter_id'] == reporter_id:
                logger.info("Succeeded to find the expected reporter_id: {0}"
                            .format(reporter_id))
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to find the expected reporter_id: {0}"
                             .format(reporter_id))
                results.setdefault(step, []).append(False)

        # case result
        notes = list()
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
