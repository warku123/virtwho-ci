# coding:utf-8
from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: virt-who service options
        :Polarion_Id: RHEL-133659
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        self.vw_case_init()

        # Case Config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        steps = {
                'step1':'restart',
                'step2':'stop',
                'step3':'start',
                'step4':'try-restart',
                'step5':'reload', 
                'step6':'force-reload'
                }
        if self.rhel_version(self.ssh_host()) == 6:
            steps['step7'] = "condrestart"

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: {1} virt-who service".format(step, option))
            ret, output = self.run_service(self.ssh_host(), "virt-who", option)
            if ret == 0:
                if option == "stop":
                    results.setdefault(step, []).append("running" != self.vw_service_status())
                else:
                    results.setdefault(step, []).append("running" == self.vw_service_status())
            else:
                logger.error("failed to run '{0}' option".format(option))
                results.setdefault(step, []).append(False)

        # Case Result
        notes = list()
        notes.append("Bug(Step5): Failed to reload virt-who.service")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1638182")
        self.vw_case_result(results, notes)
