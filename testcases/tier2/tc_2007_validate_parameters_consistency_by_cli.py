# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136710")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        base_cli = self.vw_cli_base(mode) + "-d"
        msg = 'does not match virtualization backend'
        server, username, password = self.vw_hypervisor_info(mode)
        if mode == 'libvirt-remote':
            mode = 'libvirt'
            wrong_mode = 'xen'
        else:
            wrong_mode = 'libvirt'

        # Case Steps
        logger.info(">>>step1: run virt-who by cli with all valid parameters")
        data, tty_output, rhsm_output = self.vw_start(base_cli, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who by cli with unconsistent parameters")
        cli = re.sub("--%s-owner=" % mode, "--%s-owner=" % wrong_mode, base_cli)
        data, tty_output, rhsm_output = self.vw_start(cli, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(tty_output, msg, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
