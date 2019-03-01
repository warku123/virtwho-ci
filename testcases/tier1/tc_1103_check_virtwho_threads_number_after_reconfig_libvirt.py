# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134081")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        libvirt_conf = "/etc/libvirt/libvirtd.conf"
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")

        # Case Steps
        '''This case only for libvirt-local mode'''
        logger.info(">>>step1: run virt-who service to check the thread number")
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        thread_before = self.vw_callback_thread_num()
        logger.info("Succeeded to start virt-who service and the thread_num is %s" % thread_before)

        logger.info(">>>step2: update libvirt config, and restart libvirtd service")
        self.vw_option_enable("listen_tls", filename=libvirt_conf)
        self.vw_option_enable("listen_tcp", filename=libvirt_conf)
        self.vw_option_enable("auth_tcp", filename=libvirt_conf)
        self.vw_option_enable("tcp_port", filename=libvirt_conf)
        ret, output = self.run_service(self.ssh_host(), "libvirtd", "restart")
        ret, output = self.run_service(self.ssh_host(), "libvirtd", "status")
        if "is running" in output or "Active: active (running)" in output:
            logger.info("Succeeded to restart libvirt service")
            results.setdefault('step2', []).append(True)
        else:
            logger.error("Failed to restart libvirt service")
            results.setdefault('step2', []).append(False)

        logger.info(">>>step3: check virt-who thread_num is changed or not")
        thread_after = self.vw_callback_thread_num()
        if thread_before == thread_after:
            logger.info("Succeeded to check, thread_num(%s) is not changed" % thread_after)
            results.setdefault('step3', []).append(True)
        else:
            logger.error("Failed to check, thread_num(%s) is changed to %s" % (thread_before, thread_after))
            results.setdefault('step3', []).append(False)

        logger.info(">>>step4: recovery libvirt config")
        self.vw_option_disable("listen_tls", filename=libvirt_conf)
        self.vw_option_disable("listen_tcp", filename=libvirt_conf)
        self.vw_option_disable("auth_tcp", filename=libvirt_conf)
        self.vw_option_disable("tcp_port", filename=libvirt_conf)
        ret, output = self.run_service(self.ssh_host(), "libvirtd", "restart")
        ret, output = self.run_service(self.ssh_host(), "libvirtd", "status")
        if "is running" in output or "Active: active (running)" in output:
            logger.info("Succeeded to restart libvirt service")
            results.setdefault('step4', []).append(True)
        else:
            logger.error("Failed to restart libvirt service")
            results.setdefault('step4', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/06/26 Eko<hsun@redhat.com>
# - Case created to check virt-who thread number is changed or not after reconfig libvirt
