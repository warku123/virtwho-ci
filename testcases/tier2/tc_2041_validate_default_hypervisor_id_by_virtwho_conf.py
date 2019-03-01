# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136731")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        host_uuid = self.mode_host_uuid(mode)
        host_hwuuid = self.mode_host_hwuuid(mode)
        host_name = self.mode_host_name(mode)
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        self.vw_option_enable('[default]', virtwho_conf)
        self.vw_option_enable('hypervisor_id', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        logger.info(">>>step: hypervisor_id has high priority in /etc/virt-who.d/x.conf")
        self.vw_option_update_value('hypervisor_id', 'uuid', virtwho_conf)
        self.vw_option_add('hypervisor_id', 'hostname', conf_file)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step', []).append(res)
        if data[owner].has_key(host_name):
            logger.info("Succeeded to search hypervisorId:%s" % host_name)
            results.setdefault('step', []).append(True)
        else:
            logger.error("Failed to search hypervisorId:%s" % host_name)
            results.setdefault('step', []).append(False)
        if "satellite" in server_type:
            self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
        if "stage" in server_type:
            self.stage_consumer_clean(self.ssh_host(), mode)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
# - Case created
