# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136725")
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ("libvirt-local", "vdsm", "xen"):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        # self.vw_option_enable('debug', '/etc/virt-who.conf')
        # self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_option_enable('interval', '/etc/virt-who.conf')
        self.vw_option_update_value('interval', '60', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: virt-who host can access hyperivosr by default")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(60)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        send_num = self.vw_callback_send_num()
        logger.info("error_num: {0}, thread_num: {1}, send_num: {2}".format(error_num, thread_num, send_num))
        results.setdefault('step1', []).append(error_num == 0)
        results.setdefault('step1', []).append(thread_num == 1)
        results.setdefault('step1', []).append(send_num == 1)

        try:
            logger.info(">>>step2: disconnect virt-who host from hyperivosr")
            self.hypervisor_firewall_setup("off")
            start = time.time()
            while True:
                time.sleep(30)
                end = time.time()
                spend_time = int(end - start)
                error_num, error_list = self.vw_callback_error_num()
                thread_num = self.vw_callback_thread_num()
                logger.info("error_num: {0}, thread_num: {1}".format(error_num, thread_num))
                ret, rhsm_output = self.runcmd("cat /var/log/rhsm/rhsm.log", self.ssh_host(), desc="check rhsm.log")
                if thread_num == 0:
                    logger.info("virt-who is terminated by no thread")
                    results.setdefault('step2', []).append(False)
                    break
                if error_num != 0 or "timed out" in rhsm_output or "timeout" in rhsm_output:
                    logger.info("virt-who is disconnected from hyperivosr by timeout")
                    results.setdefault('step2', []).append(True)
                    break
                if spend_time >= 900:
                    logger.info("virt-who is timeout(900s)")
                    results.setdefault('step2', []).append(False)
                    break
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: connect virt-who host from hyperivosr again")
            self.hypervisor_firewall_setup("on")
            time.sleep(60)
            ret, output = self.runcmd("rm -rf /var/log/rhsm/*", self.ssh_host(), desc="rhsm.log clean")
            time.sleep(60)
            ret, rhsm_output = self.runcmd("cat /var/log/rhsm/rhsm.log", self.ssh_host(), desc="check rhsm.log")
            error_num, error_list = self.vw_callback_error_num()
            thread_num = self.vw_callback_thread_num()
            logger.info("error_num: {0}, thread_num: {1}".format(error_num, thread_num))
            if thread_num == 1 and error_num == 0 and "timed out" not in rhsm_output and "timeout" not in rhsm_output:
                logger.info("virt-who is connected to hyperivosr normally")
                results.setdefault('step3', []).append(True)
            else:
                results.setdefault('step3', []).append(False)

        # case result
        notes = list()
        notes.append("(step2) No any response after xen hypervisor lost its connection with virt-who host")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=2065097")
        self.vw_case_result(results, notes)

