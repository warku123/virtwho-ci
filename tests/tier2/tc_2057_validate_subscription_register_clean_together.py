# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-136773")
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        register_type = register_config['type']

        # case steps
        logger.info(">>>step1: start virt-who by run_service")
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: {0}, thread_num: {1}" .format(error_num, thread_num))
        results.setdefault('step1', []).append(error_num == 0)
        results.setdefault('step1', []).append(thread_num == 1)

        logger.info(">>>step2: unregister, and the clean")
        cmd1 = "subscription-manager unregister"
        cmd2 = "subscription-manager clean"
        ret, output = self.runcmd(cmd1, self.ssh_host(), desc="unregister")
        time.sleep(15)
        ret, output = self.runcmd(cmd2, self.ssh_host(), desc="clean")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: {0}, thread_num: {1}" .format(error_num, thread_num))
        results.setdefault('step2', []).append(thread_num == 1)

        logger.info(">>>step3: register, start virt-who")
        self.system_register(self.ssh_host(), register_type, register_config)
        self.vw_thread_clean()
        ret, output = self.run_service(self.ssh_host(), "virt-who", "restart")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: {0}, thread_num: {1}" .format(error_num, thread_num))
        results.setdefault('step3', []).append(error_num == 0)
        results.setdefault('step3', []).append(thread_num == 1)

        logger.info(">>>step4: unregister and clean together")
        cmd1 = "subscription-manager unregister; subscription-manager clean"
        ret, output = self.runcmd(cmd1, self.ssh_host(), desc="unregister and clean")
        time.sleep(30)
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        logger.info("error_num: {0}, thread_num: {1}" .format(error_num, thread_num))
        results.setdefault('step4', []).append(thread_num == 1)

        # case result
        self.vw_case_result(results)
