# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-196077')
        self.vw_case_init()

        # case config
        results = dict()
        config_file = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', config_file)
        self.vw_option_enable('debug', config_file)
        self.vw_option_update_value('debug', 'True', config_file)
        self.vw_etc_d_mode_create('virtwho-config', '/etc/virt-who.d/virtwho-config.conf')
        squid_server = "squid.corp.redhat.com:3128"
        bad_squid_server = "squid.corp.redhat.com:9999"
        steps = {'step2':'http_proxy', 'step3':'https_proxy'}
        error_msg = ["Connection refused|Cannot connect to proxy|Connection timed out"]

        # case steps
        logger.info(">>>step1: enable [system_environment] in /etc/virt-who.conf")
        self.vw_option_enable("[system_environment]", config_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res1)

        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to check {1}".format(step, option))
            if option == "http_proxy":
                value = "http://{0}".format(squid_server)
                bad_value = "http://{0}".format(bad_squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(squid_server)
                bad_value = "https://{0}".format(bad_squid_server)
            logger.info("> run virt-who with good {0}".format(option))
            self.vw_option_enable(option, config_file)
            self.vw_option_update_value(option, value, config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            s2 = self.vw_msg_search(rhsm_output, "Connection built.*{0}".format(squid_server), exp_exist=True)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(squid_server), exp_exist=True)
            results.setdefault(step, []).append(s1)
            results.setdefault(step, []).append(s2)
            results.setdefault(step, []).append(s3)

            logger.info("> run virt-who with bad {0}".format(option))
            self.vw_option_update_value(option, bad_value, config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0)
            s4 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            s5 = self.msg_validation(rhsm_output, error_msg, exp_exist=True)
            results.setdefault(step, []).append(s4)
            results.setdefault(step, []).append(s5)

            logger.info(">>> run virt-who with bad proxy, but no_proxy=*")
            self.vw_option_enable('no_proxy', config_file)
            self.vw_option_update_value('no_proxy', '*', config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            s6 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s6)
            self.vw_option_disable(option, config_file)
            self.vw_option_disable("no_proxy", config_file)

        # case result
        self.vw_case_result(results)
