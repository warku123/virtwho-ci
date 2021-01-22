# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133657')
        trigger_type = self.get_config('trigger_type')
        if "trigger-rhev" in trigger_type:
            self.vw_case_skip(trigger_type)

        results = dict()
        logger.info(">>>step1: virt-who have correct man page")
        ret, output = self.runcmd("man virt-who", self.ssh_host(), desc="run man virt-who")
        results.setdefault('step1', []).append("Agent for reporting virtual guest IDs to Subscription" in output)

        logger.info(">>>step2: virt-who-config have correct man page")
        ret, output = self.runcmd("man virt-who-config", self.ssh_host())
        results.setdefault('step2', []).append("configuration for virt-who" in output)
        msg = "backend names: libvirt, esx, rhevm, hyperv, fake, xen, or kube.*\n.*virt"
        results.setdefault('step2', []).append(self.vw_msg_search(output, msg))

        logger.info(">>>step3: virt-who have correct help page")
        ret, output = self.runcmd("virt-who --help", self.ssh_host())
        results.setdefault('step3', []).append("optional arguments:" in output)

        # case result
        self.vw_case_result(results)
