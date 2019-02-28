# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133659")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        rhel_ver = self.rhel_version(self.ssh_host())
        steps = {
                'step1':'restart',
                'step2':'stop',
                'step3':'start',
                'step4':'try-restart',
                'step5':'reload', 
                'step6':'force-reload'
                }
        if rhel_ver == 6:
            steps['step7'] = "condrestart"

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: %s virt-who service" % (step, option))
            ret, output = self.run_service(self.ssh_host(), "virt-who", option)
            if ret == 0:
                if option == "stop":
                    results.setdefault(step, []).append("running" != self.vw_service_status())
                else:
                    results.setdefault(step, []).append("running" == self.vw_service_status())
            else:
                logger.error("failed to run '%s' option" % option)
                results.setdefault(step, []).append(False)

        # Case Result
        notes = list()
        notes.append("Bug(Step5): Failed to reload virt-who.service")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1638182")
        self.vw_case_result(results, notes)
if __name__ == '__main__':
    unittest.main()

# ===changelog===
# - 2019/01/15 Yuefen Liu<yuefliu@redhat.com>
# - Change self.vw_etc_sys_mode_enable() to self.vw_etc_d_mode_create()
# - 2018/10/11 Yuefen Liu<yuefliu@redhat.com>
# - Add checking "if ret == 0" after self.run_service()
# - 2018/06/01 <shyan@redhat.com>
# - Case created and support to run against rhel6/7/8
# RHEL-6: Usage: /etc/init.d/virt-who {start|stop|status|restart|condrestart|try-restart|reload|force-reload}
# RHEL-7: The service command supports only basic LSB actions (start, stop, restart, try-restart, reload, force-reload, status).
# - 2018/06/14 <hsun@redhat.com>
# - update steps
