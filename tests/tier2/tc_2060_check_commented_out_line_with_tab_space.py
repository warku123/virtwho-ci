# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-175032')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] < '0.25.7':
            self.vw_case_skip("virt-who version")
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        compose_id = self.get_config('rhel_compose')

        # Case Steps
        logger.info(">>>step1: run virt-who with all good configurations")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res1)

        logger.info(">>>step2: add useless line with tab spaces after type=")
        cmd = "sed -i '/^type=/a \\\txxx=xxx' {0}".format(config_file)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="add new line with tab")
        data, tty_output, rhsm_output = self.vw_start(exp_send=0)
        msg = "virt-who can't be started"
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, msg)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: comment out the useless line")
        cmd = 'sed -i "s/xxx/#xxx/" {0}'.format(config_file)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if "RHEL-7" in compose_id:
            war_msg = "A line continuation (line starts with space) that is commented " \
                      "out was detected in file"
            data, tty_output, rhsm_output = self.vw_start(exp_send=0)
            res1 = self.op_normal_value(data, exp_error=1, exp_thread=0, exp_send=0)
        else:
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step3', []).append(res1)

        # Case Result
        self.vw_case_result(results)
