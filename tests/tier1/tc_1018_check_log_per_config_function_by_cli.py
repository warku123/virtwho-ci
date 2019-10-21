# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133696')
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # Case Config
        results = dict()
        guest_uuid = self.get_hypervisor_guestuuid()
        cmd1 = self.vw_cli_base() + "-d -m"
        cmd2 = self.vw_cli_base() + "-d --log-per-config"
        steps = {'step1': cmd1, 'step2': cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(">>>{0}: run virt-who cli to check log-per-config".format(step))
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            ret, output = self.runcmd('ls /var/log/rhsm/virtwho*', self.ssh_host())
            if ret != 0 or output is None:
                logger.error("Failed to find /var/log/rhsm/virtwho* files")
                results.setdefault(step, []).append(False)
            files = output.split('\n') 
            ''' check files exist or not'''
            if any("destination" in fd for fd in files):
                logger.info("Succeeded to find virtwho.destination file")
            else: 
                logger.error("Failed to find virtwho.destination file")
                results.setdefault(step, []).append(False)
            if any("main" in fd for fd in files):
                logger.info("Succeeded to find virtwho.main file")
            else: 
                logger.error("Failed to find virtwho.main file")
                results.setdefault(step, []).append(False)
            if any("rhsm_log" in fd for fd in files):
                logger.info("Succeeded to find virtwho.rhsm_log file")
            else:
                logger.error("Failed to find virtwho.rhsm_log file")
                results.setdefault(step, []).append(False)
            ''' check message is expected or not'''
            for fd in files:
                fd = fd.strip()
                ret, output = self.runcmd("cat {0}".format(fd), self.ssh_host())
                if "destination" in fd:
                    d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                    d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if d1 is False or d2 is False:
                        logger.error("Failed to validate virtwho.destination file")
                        results.setdefault(step, []).append(False)
                if "main" in fd:
                    m1 = self.vw_msg_search(output, "Report for config", exp_exist=True)
                    m2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if m1 is False or m2 is False:
                        logger.error("Failed to validate virtwho.main file")
                        results.setdefault(step, []).append(False)
                if "rhsm_log" in fd:
                    r1 = self.vw_msg_search(output, "Using reporter_id=", exp_exist=True)
                    r2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                    if r1 is False or r2 is False:
                        logger.error("Failed to validate virtwho.rhsm_log file")
                        results.setdefault(step, []).append(False)
        # case result
        notes = list()
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
