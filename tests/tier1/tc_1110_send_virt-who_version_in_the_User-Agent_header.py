# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-195888')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] < '0.30.0':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info('>>>step1: set the environment in the virt-who host and run virt-who service')
        cmd = ('export SUBMAN_DEBUG_PRINT_REQUEST=1;'
               'export SUBMAN_DEBUG_PRINT_REQUEST_HEADER=1')
        cmd = "{0}; virt-who -o -c {1}".format(cmd, config_file)
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
        results.setdefault('step1', []).append(res1)

        logger.info('>>>step2: check the message from console')
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')[9:17]
        msg = 'virt-who/{}'.format(pkg)
        res2 = self.vw_msg_search(output=tty_output, msg=msg, exp_exist=True)
        results.setdefault('step2', []).append(res2)

        # case results
        self.vw_case_result(results)
