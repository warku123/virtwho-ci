# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-137103")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, mode, config_file)
        sat_user, sat_passwd = self.satellite_account_get(server_ip)
        self.vw_option_enable("VIRTWHO_DEBUG", filename='/etc/sysconfig/virt-who')
        self.vw_option_update_value("VIRTWHO_DEBUG", "1", filename='/etc/sysconfig/virt-who')

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: delete virt-who host from webui")
        try:
            vw_host_name = self.get_hostname(self.ssh_host())
            vw_host_uuid='xxx'
            if "libvirt-local" in mode or "vdsm" in mode:
                error_msg = "consumer no longer exists"
            else:
                error_msg = ".*has been deleted"
            res1 = self.vw_web_host_delete(self.ssh_host(), vw_host_name, vw_host_uuid)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            res2 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            res3 = self.vw_msg_search(rhsm_output, error_msg, exp_exist=True)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
            results.setdefault('step2', []).append(res3)
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: re-register host and run virt-who")
            self.system_unregister(self.ssh_host())
            self.vw_sub_register(self.ssh_host())
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res)

        if "libvirt-local" not in mode and "vdsm" not in mode:
            logger.info(">>>step4: delete hypervisor from webui")
            host_name = self.mode_host_name(mode)
            host_uuid = self.mode_host_uuid(mode)
            self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/08/13 Yuefen<yuefliu@redhat.com>