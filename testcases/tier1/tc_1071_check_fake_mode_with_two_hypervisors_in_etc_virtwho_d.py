# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133742")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        json_file = "/tmp/fake.json"
        fake_conf_file = "/etc/virt-who.d/fake.conf"
        mode_conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        mode_conf_name = "%s_config" % mode.lower()
        extra_conf_file = "/etc/virt-who.d/extra.conf"
        host_name = self.mode_host_name(mode)
        host_uuid = self.mode_host_uuid(mode)
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.mode_guest_uuid(mode)
        extra_mode='libvirt-remote' if 'xen' in mode else 'xen'
        ext_host_name, ext_host_uuid, ext_guest_uuid = self.vw_extra_mode_info(extra_mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")

        # Case Steps
        logger.info(">>>step1: create json file and fake config file")
        self.vw_extra_conf_in_d(extra_mode, filename=extra_conf_file)
        self.vw_etc_d_mode_create(mode, mode_conf_name, filename=mode_conf_file)
        self.vw_fake_json_create("virt-who", json_file)
        self.vw_etc_d_delete_all()
        self.vw_fake_conf_create(fake_conf_file, json_file, is_hypervisor=True)

        logger.info(">>>step2: run virt-who with fake conf")
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        res3 = self.vw_rhsm_associate(data, ext_host_uuid, ext_guest_uuid)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/15 Eko<hsun@redhat.com>
#- Case created to validate fake mode with two hypervisors
