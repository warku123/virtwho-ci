# coding:utf-8
from library import *
from library.config import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133735")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.vw_pkg_check()[9:15] >= '0.23.3':
            logger.warning("Don't support to configer hypervisor in /etc/sysconfig/virt-who")
            self.vw_case_skip("skipped - this case is not avaialbe for virt-who version")
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: enable mode in /etc/sysconfig/virt-who and config same mode in /etc/virt-who.d/")
        self.vw_etc_sys_mode_enable(mode)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        '''two same vdsm modes, will send twice'''
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: check mapping info duplicated or not")
        num = rhsm_output.count('"guestId": "%s"' % guest_uuid)
        logger.info("Actual mapping info num: %s" % num)
        if "satellite62" in server_type:
            logger.info("Expected mapping info num: 1 for sat62")
            results.setdefault('step2', []).append(num == 1)
        else:
            logger.info("Expected mapping info num: 2 for sat63 and stage")
            results.setdefault('step2', []).append(num == 2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/03 Eko<hsun@redhat.com>
# - update this case for the wrong check point, and vdsm mode should not be skipped.
