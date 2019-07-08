# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133659')
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        steps = {
                'step1':'restart',
                'step2':'stop',
                'step3':'start',
                'step4':'try-restart',
                'step5':'force-reload'
                }
        if self.rhel_version(self.ssh_host()) == 6:
            steps['step6'] = "condrestart"

        # case steps
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

        # case result
        logger.info('Warning: Skip to test "reload" due to Bug 1638182 WONTFIX')
        self.vw_case_result(results)
