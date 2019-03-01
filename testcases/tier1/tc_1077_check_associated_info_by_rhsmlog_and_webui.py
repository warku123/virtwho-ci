# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134063")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)
        self.vw_etc_d_mode_create(mode, mode, config_file)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")

        # Case Steps
        logger.info(">>>step1: run virt-who service")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check host-to-guest association in rhsm.log")
        res = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res)

        logger.info(">>>step3: check host-to-guest association in webui")
        res = self.vw_web_associate(self.ssh_host(), host_name, host_uuid, guest_name, guest_uuid)
        results.setdefault('step3', []).append(res)

        # Case Result
        notes = list()
        notes.append("Bug(Step3):  Missing h/g association in satellite webUI")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1644969")
        self.vw_case_result(results, notes)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/02 Eko<hsun@redhat.com>
# - Case created to check the association by rhsm.log and webui
