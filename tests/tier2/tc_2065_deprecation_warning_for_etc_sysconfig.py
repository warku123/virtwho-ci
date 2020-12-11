# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-195890')
        compose_id = self.get_config('rhel_compose')
        if "RHEL-9" in compose_id:
            self.vw_case_skip("RHEL-9")
        self.vw_case_init()

        # case config
        results = dict()
        sysconf_file = "/etc/sysconfig/virt-who"
        config_file = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', config_file)
        self.vw_option_enable('debug', config_file)
        self.vw_option_update_value('debug', 'True', config_file)
        self.vw_etc_d_mode_create('virtwho-config', '/etc/virt-who.d/virtwho-config.conf')

        # case steps
        logger.info(">>>step1: check the prompt in /etc/sysconfig/virt-who")
        cmd = 'cat {}'.format(sysconf_file)
        ret, output = self.runcmd(cmd,self.ssh_host())
        msg = 'The use of this file is deprecated and will be ignored in the next major'
        res1 = self.vw_msg_search(output, msg)
        results.setdefault('step1', []).append(res1)

        logger.info(">>>step2: check the prompt in /var/log/rhsm.log")
        data, tty_output, rhsm_output = self.vw_start()
        res2 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res2)
        msg2 ='The use of environment variables and the use of the sysconfig file ' \
              'to configure virt-who are deprecated. ' \
              'Their use will be ignored in the next major release'
        res3 = self.vw_msg_search(rhsm_output, msg2)
        results.setdefault('step2', []).append(res3)

        logger.info(">>>step3: check the prompt in man virt-who")
        ret, output = self.runcmd("man virt-who", self.ssh_host(), desc="run man virt-who")
        msg3 = 'Their use is deprecated'
        msg4 = 'and will be ignored in the next major release'
        res4 = self.vw_msg_search(output, msg3)
        res5 = self.vw_msg_search(output, msg4)
        results.setdefault('step3', []).append(res4)
        results.setdefault('step3', []).append(res5)

        # case result
        self.vw_case_result(results)
