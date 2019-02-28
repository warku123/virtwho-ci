# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133657")
        trigger_name = self.get_exported_param("TRIGGER_NAME")
        if "trigger-rhev" in trigger_name:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % trigger_name)

        results = dict()
        logger.info(">>>step1: virt-who have correct man page")
        ret, output = self.runcmd("man virt-who", self.ssh_host(), desc="run man virt-who")
        results.setdefault('step1', []).append("Agent for reporting virtual guest IDs to Subscription" in output)

        logger.info(">>>step2: virt-who-config have correct man page")
        ret, output = self.runcmd("man virt-who-config", self.ssh_host(), desc="run man virt-who-config")
        results.setdefault('step2', []).append("configuration for virt-who" in output)

        logger.info(">>>step3: virt-who have correct help page")
        ret, output = self.runcmd("virt-who --help", self.ssh_host(), desc="run virt-who --help")
        results.setdefault('step3', []).append("optional arguments:" in output)

        # Case Result
        self.vw_case_result(results)

# ===changelog===
# - 2018/07/16 <hsun@redhat.com>
# - skip this case, it's not available for rhev as bug: https://bugzilla.redhat.com/show_bug.cgi?id=1601305
# - 2018/06/14 <hsun@redhat.com>
# - remove function from case
# - 2018/06/01 <shyan@redhat.com>
# - Case created and support to run against rhel6/7/8
