# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # case and env init
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-150339")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        compose_id = self.get_exported_param("COMPOSE_ID")
        self.perf_env_init(mode)
        self.perf_vms_check(mode)

        # enable debug and oneshot mode
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_option_disable("interval", virtwho_conf)
        self.vw_option_enable("oneshot", virtwho_conf)
        self.vw_option_update_value("oneshot", 'True', virtwho_conf)
        self.runcmd("rm -rf /var/log/rhsm/*", self.ssh_host(), desc="clean log files")

        # create 100 virt-who config files
        for index in range(1, 51):
            conf_name = "%s_config_%s" % (mode, index)
            conf_file = "/etc/virt-who.d/%s_%s.conf" % (mode, index)
            self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file, perf=True)

        for index in range(1, 100):
            self.vw_stop()
            logger.info("Restart virt-who service with debug(on) and oneshot(on)")
            ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
            error_num, error_list = self.vw_callback_error_num()
            thread_num = self.vw_callback_thread_num()
            start=time.clock()
            while True:
                time.sleep(10)
                end=time.clock()
                spend_time = int((end-start)*10)
                error_num, error_list = self.vw_callback_error_num()
                thread_num = self.vw_callback_thread_num()
                if thread_num == 0:
                    logger.info("virt-who is terminated by pid exit")
                    break
                if spend_time >= 100:
                    logger.info("virt-who is terminated by timeout(10m)")
                    break
                logger.info("error_num: %s, thread_num: %s" %(error_num, thread_num))
            ret, output = self.runcmd("ls /var/log/rhsm/* -lha", self.ssh_host(), desc="list log files")
            logger.info(output)
