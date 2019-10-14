# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134122')
        compose_id = self.get_config('rhel_compose')
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # case config
        results = dict()
        log_dir = "/var/log/rhsm/virtwho"
        log_file = "/var/log/rhsm/virtwho/virtwho.log"
        guest_uuid = self.get_hypervisor_guestuuid()
        cmd1 = self.vw_cli_base() + "-d -l {0} -f {1}".format(log_dir,log_file)
        cmd2 = self.vw_cli_base() + "-d --log-dir {0} --log-file {1}".format(log_dir,log_file)
        steps = {'step1':cmd1, 'step2':cmd2}

        # case steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who cli to check log-file".format(step))
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            ret, output = self.runcmd("ls {0}".format(log_file), self.ssh_host())
            if ret == 0:
                ret, output = self.runcmd("cat {0}".format(log_file), self.ssh_host())
                d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if d1 is False or d2 is False:
                    results.setdefault(step, []).append(False)
            else:
                logger.error("{0} is not exist".format(log_file))
                results.setdefault(step, []).append(False)

        # case result
        self.vw_case_result(results)
