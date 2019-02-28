# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133681")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        json_file = "/tmp/fake.json"
        conf_file = "/etc/virt-who.d/fake.conf"
        host_uuid = self.mode_host_uuid(mode)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: create json file")
        cli = "virt-who -d"
        self.vw_fake_json_create(cli, json_file)
        self.vw_etc_d_delete_all()
        if "libvirt-local" in mode or "vdsm" in mode:
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=False)
        else:
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=True)

        logger.info(">>>step2: run virt-who with fake conf")
        data, tty_output, rhsm_output = self.vw_start(cli="virt-who -d")
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_rhsm_associate(data, host_uuid, guest_uuid)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
#- 2018/06/15 Eko<hsun@redhat.com>
#- Case created to validate fake mode with one hypervisor
