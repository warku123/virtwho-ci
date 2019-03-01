# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133653")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        json_file = "/tmp/file.json"
        host_uuid = self.mode_host_uuid(mode)
        guest_uuid = self.mode_guest_uuid(mode)
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        cmd1 = "virt-who -p > %s" % json_file
        cmd2 = "virt-who -p -d > %s" % json_file
        steps = {'step1':cmd1, 'step2':cmd2}

        # Case Steps
        for step, cmd in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who cli to check print option" % step)
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=0, web_check=False)
            res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
            results.setdefault(step, []).append(res)
            ret, output = self.runcmd("cat %s" %json_file, self.ssh_host(), desc="cat file")
            res = self.vw_msg_search(output, guest_uuid, exp_exist=True)
            results.setdefault(step, []).append(res)
            if "libvirt-local" not in mode and "vdsm" not in mode:
                res = self.vw_msg_search(output, host_uuid, exp_exist=True)
                results.setdefault(step, []).append(res)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/12/05 Yuefen<yuefliu@redhat.com>
#- Update to use vw_etc_d_mode_create due to Bug1655626 fix
#- 2018/06/07 Eko<hsun@redhat.com>
#- Case created to validate print option
