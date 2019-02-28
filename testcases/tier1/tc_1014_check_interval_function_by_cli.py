# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133650")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who without -i option")
        cmd = "virt-who -d"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: run virt-who with -i 10 option")
        cmd = "virt-who -d -i 10"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=3600)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: run virt-who with -i 60 option")
        cmd = "virt-who -d -i 60"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60, exp_loopnum=1, exp_looptime=60)
        results.setdefault('step3', []).append(res)

        logger.info(">>>step4: run virt-who with -i 120 option")
        cmd = "virt-who -d -i 120"
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1, exp_loopnum=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120, exp_loopnum=1, exp_looptime=120)
        results.setdefault('step4', []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/12/05 Yuefen<yuefliu@redhat.com>
#- Update to use vw_etc_d_mode_create due to Bug1655626 fix
#- 2018/05/21 Eko<hsun@redhat.com>
#- Case created to validate owner option
