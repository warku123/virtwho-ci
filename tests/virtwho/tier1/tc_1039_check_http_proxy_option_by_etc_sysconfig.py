# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133704')
        self.vw_case_init()

        # case config
        results = dict()
        config_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create('virtwho-config', '/etc/virt-who.d/virtwho-config.conf')
        squid_server = "10.73.3.248:3128"
        steps = {'step1':'http_proxy', 'step2':'https_proxy'}

        # case steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to check {1}".format(step, option))
            if option == "http_proxy":
                value = "http://{0}".format(squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(squid_server)
            self.vw_option_add(option, value, filename=config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(squid_server), exp_exist=True)
            results.setdefault(step, []).append(s2)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(squid_server), exp_exist=True)
            results.setdefault(step, []).append(s3)
            self.vw_option_del(option, filename=config_file)

        # case result
        self.vw_case_result(results)
