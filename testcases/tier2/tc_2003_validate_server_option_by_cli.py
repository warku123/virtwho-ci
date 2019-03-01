# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136572")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        extra_file = "/etc/virt-who.d/extra.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        base_cli = self.vw_cli_base(mode) + "-d"
        if "libvirt-remote" in mode:
            mode = "libvirt"

        # Case Steps
        logger.info(">>>step1: server option is good value")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: server option is wrong value")
        cli = self.vw_cli_base_update(base_cli, "--%s-server=.*" % mode, "--%s-server=xxxxx" % mode)
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: server option is 红帽€467aa value")
        cli = self.vw_cli_base_update(base_cli, "--%s-server=.*" % mode, "--%s-server=红帽€467aa" % mode)
        data, tty_output, rhsm_output = self.vw_start(cli)
        msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend|Unable to connect|codec can't encode"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: server option is null value")
        cli = self.vw_cli_base_update(base_cli, "--%s-server=.*" % mode, "--%s-server= " % mode)
        data, tty_output, rhsm_output = self.vw_start(cli)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-local mode will be used to instead when server option is null for libvirt-remote")
            msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
            res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        else:
            msg_list = ["server.* not set|virt-who can't be started|No host supplied"]
            res1 = self.op_normal_value(data, exp_error="0|1|2", exp_thread=0, exp_send=0)
            res2 = self.msg_validation(tty_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: server option is disable")
        cli = self.vw_cli_base_update(base_cli, "--%s-server=.*" % mode, " ")
        data, tty_output, rhsm_output = self.vw_start(cli)
        if "libvirt-remote" in mode or "libvirt" in mode:
            logger.warning("libvirt-local mode will be used to instead when server option is disabled for libvirt-remote")
            msg_list = ["Name or service not known|Connection timed out|Failed to connect|Error in .* backend"]
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
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/10/22 Yuefliu<yuefliu@redhat.com>
# - Updated msg_list when server is  红帽€467aa
# - 2018/07/18 Eko<hsun@redhat.com>
# - Case created to validate server option
# - for libvirt-remote, when server is disable or null value, local libvirt mode will be used to instead (bug 1530562)
