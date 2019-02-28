# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136725")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        server, username, password = self.vw_hypervisor_info(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_option_enable("VIRTWHO_INTERVAL", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_INTERVAL", '60', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: virt-who host can access hyperivosr by default")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(60)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        send_num = self.vw_callback_send_num()
        logger.info("error_num: %s, thread_num: %s, send_num: %s" %(error_num, thread_num, send_num))
        results.setdefault('step1', []).append(error_num==0)
        results.setdefault('step1', []).append(thread_num==1)
        results.setdefault('step1', []).append(send_num==1)

        try:
            logger.info(">>>step2: disconnect virt-who host from hyperivosr")
            self.hypervisors_access(mode, connected="no")
            start=time.clock()
            while True:
                time.sleep(30)
                end=time.clock()
                spend_time = int((end-start)*10)
                error_num, error_list = self.vw_callback_error_num()
                thread_num = self.vw_callback_thread_num()
                logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
                ret, rhsm_output = self.runcmd("cat /var/log/rhsm/rhsm.log", self.ssh_host(), desc="check rhsm.log", showlogger=False)
                if thread_num == 0:
                    logger.info("virt-who is terminated by no thread")
                    results.setdefault('step2', []).append(False)
                    break
                if error_num != 0 or "timed out" in rhsm_output or "timeout" in rhsm_output:
                    logger.info("virt-who is disconnected from hyperivosr by timeout")
                    results.setdefault('step2', []).append(True)
                    break
                if spend_time >= 6:
                    logger.info("virt-who is timeout(6m)")
                    results.setdefault('step2', []).append(False)
                    break
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: connect virt-who host from hyperivosr again")
            self.hypervisors_access(mode, connected="yes")
            time.sleep(60)
            ret, output = self.runcmd("rm -rf /var/log/rhsm/*", self.ssh_host(), desc="rhsm.log clean")
            time.sleep(60)
            ret, rhsm_output = self.runcmd("cat /var/log/rhsm/rhsm.log", self.ssh_host(), desc="check rhsm.log", showlogger=False)
            error_num, error_list = self.vw_callback_error_num()
            thread_num = self.vw_callback_thread_num()
            logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
            if thread_num == 1 and error_num == 0 and "timed out" not in rhsm_output and "timeout" not in rhsm_output:
                logger.info("virt-who is connected to hyperivosr normally")
                results.setdefault('step3', []).append(True)
            else:
                results.setdefault('step3', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/31 Eko<hsun@redhat.com>
#- Case created
