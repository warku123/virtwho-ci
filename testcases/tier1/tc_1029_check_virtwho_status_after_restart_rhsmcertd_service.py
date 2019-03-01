# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133746")
        mode, host_ip, guest_ip = self.vw_env_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: restart virt-who service, check status and thread")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "start")
        thread_num = self.vw_callback_thread_num()
        results.setdefault('step1', []).append(thread_num == 1)
        results.setdefault('step1', []).append(self.vw_service_status() == "running")
        logger.info("virt-who thread number is: %s" %thread_num)

        logger.info(">>>step2: restart rhsmcertd service , check virt-who status and thread")
        ret, output = self.run_service(self.ssh_host(), "rhsmcertd", "restart")
        thread_num = self.vw_callback_thread_num()
        results.setdefault('step2', []).append(thread_num == 1)
        results.setdefault('step2', []).append(self.vw_service_status() == "running")
        logger.info("virt-who thread number is: %s" %thread_num)

        logger.info(">>>step3: restart virt-who service again , check virt-who status and thread")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/03 Eko<hsun@redhat.com>
# - update this case due to the error case steps before
# - 2018/06/20 yanpliu<yanpliu@redhat.com> 
# - add else and update config style
# - 2018/06/11 yanpliu<yanpliu@redhat.com>
# - Case created to validate mapping info after restart virt-who and rhsmcertd.service
