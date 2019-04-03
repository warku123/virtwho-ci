# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-134081')
        hypervisor_type = self.get_config('hypervisor_type')
        if "libvirt-local" not in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        libvirt_conf = "/etc/libvirt/libvirtd.conf"

        # case steps
        logger.info(">>>step1: run virt-who service to check the thread number")
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        thread_before = self.vw_callback_thread_num()
        logger.info("Succeeded to start virt-who service and the thread_num is {0}".format(thread_before))

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
            logger.info("Succeeded to check, thread_num({0}) is not changed".format(thread_after))
            results.setdefault('step3', []).append(True)
        else:
            logger.error("Failed to check, thread_num({0}) is changed to {1}".format(thread_before, thread_after))
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

        # case result
        self.vw_case_result(results)
