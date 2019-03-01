# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133747")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_enable("VIRTWHO_INTERVAL", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: Run virt-who servie when virt-who host is registered")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "start")
        time.sleep(30)
        status = self.vw_service_status()
        thread_num = self.vw_callback_thread_num()
        error_num, error_list = self.vw_callback_error_num()
        results.setdefault('step1', []).append(error_num == 0)
        results.setdefault('step1', []).append(thread_num == 1)
        results.setdefault('step1', []).append(status == "running")
        logger.info("error_num: %s, thread_num: %s, status: %s" % (error_num, thread_num, status))

        logger.info(">>>step2: Run virt-who servie when virt-who host is un_registered")
        ret, output = self.runcmd('subscription-manager unregister', self.ssh_host(), desc="unregister system")
        logger.info("Succeeded to unregister host")
        time.sleep(15)
        status = self.vw_service_status()
        thread_num = self.vw_callback_thread_num()
        error_num, error_list = self.vw_callback_error_num()
        results.setdefault('step2', []).append(error_num != 0)
        results.setdefault('step2', []).append(thread_num == 1)
        results.setdefault('step2', []).append(status == "running")
        logger.info("error_num: %s, thread_num: %s, status: %s" % (error_num, thread_num, status))
        ret, rhsm_output = self.runcmd('cat /var/log/rhsm/rhsm.log', self.ssh_host(), desc="cat rhsm.log")
        res = self.vw_msg_search(rhsm_output, 'system is not registered', exp_exist=True)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: Run virt-who servie when virt-who host is re_registered")
        if self.system_isregister(self.ssh_host(), server_type, server_ip, mode) is False:
            self.vw_sub_register(self.ssh_host())
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
