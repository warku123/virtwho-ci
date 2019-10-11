# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136572')
        hypervisor_type = self.get_config('hypervisor_type')
        compose_id = self.get_config('rhel_compose')
        if hypervisor_type in ('libvirt-local', 'vdsm', 'kubevirt'):
            self.vw_case_skip(hypervisor_type)
        if "RHEL-8" in compose_id:
            self.vw_case_skip("RHEL-8")
        self.vw_case_init()

        # Case Config
        results = dict()
        if hypervisor_type == 'libvirt-remote':
            hypervisor_type = 'libvirt'
        base_cli = self.vw_cli_base() + '-d'
        msg_list = ["Name or service not known|"
                    "Connection timed out|"
                    "Failed to connect|"
                    "Error in .* backend"]

        # Case Steps
        logger.info(">>>step1: server option is good value")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: server option is wrong value")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-server=.*".format(hypervisor_type),
                                      "--{0}-server=xxxxx".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: server option is 红帽€467aa value")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-server=.*".format(hypervisor_type),
                                      "--{0}-server=红帽€467aa".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list_3 = ["Name or service not known|"
                      "Connection timed out|"
                      "Failed to connect|"
                      "Error in .* backend|"
                      "Unable to connect|"
                      "codec can't encode"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list_3, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: server option is null value")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-server=.*".format(hypervisor_type),
                                      "--{0}-server= ".format(hypervisor_type))
        data, tty_output, rhsm_output = self.vw_start(cli)
        if "libvirt" in hypervisor_type:
            logger.warning("libvirt-local mode will be used to instead "
                           "when server option is null for libvirt-remote")
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        else:
            msg_list = ["server.* not set|virt-who can't be started|No host supplied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: server option is disable")
        cli = self.vw_cli_base_update(base_cli,
                                      "--{0}-server=.*".format(hypervisor_type),
                                      " ")
        data, tty_output, rhsm_output = self.vw_start(cli)
        if "libvirt" in hypervisor_type:
            logger.warning("libvirt-local mode will be used to instead "
                           "when server option is disabled for libvirt-remote")
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        else:
            msg_list = ["server.* not set|virt-who can't be started|No host supplied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        self.vw_case_result(results)
