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
        if "libvirt-local" in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        config_file = "/root/hypervisor1.conf"
        extra_config_file = "/etc/virt-who.d/hypervisor2.conf"
        extra_mode = 'libvirt-remote' if 'xen' in mode else 'xen'
        guest_uuid = self.mode_guest_uuid(mode)
        ext_host_name, ext_host_uuid, ext_guest_uuid = self.vw_extra_mode_info(extra_mode)
        self.vw_etc_d_mode_create(mode, mode, config_file)
        self.vw_extra_conf_in_d(extra_mode, extra_config_file)
        self.vw_option_enable("[global]", filename="/etc/virt-who.conf")
        self.vw_option_enable("interval", filename="/etc/virt-who.conf")
        self.vw_option_update_value("interval", '120', filename="/etc/virt-who.conf")
        self.vw_option_enable("debug", filename="/etc/virt-who.conf")
        self.vw_option_update_value("debug", 'True', filename="/etc/virt-who.conf")
        self.vw_option_enable("[defaults]", filename="/etc/virt-who.conf")
        self.vw_option_enable("owner", filename="/etc/virt-who.conf")
        self.vw_option_update_value("owner", 'xxx', filename="/etc/virt-who.conf")
        self.vw_option_enable("env", filename="/etc/virt-who.conf")
        self.vw_option_update_value("env", 'xxx', filename="/etc/virt-who.conf")

        # Case Steps
        logger.info(">>>step1: run virt-who with -c option to check will not run /etc/virt-who.d/x.conf")
        cmd = "virt-who -c %s -i 60" % config_file
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=60)
        res2 = self.vw_msg_search(output=tty_output, msg="\[.*DEBUG\]", exp_exist=True)
        res3 = self.vw_msg_search(str(data), guest_uuid, exp_exist=True)
        res4 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=False)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)
        results.setdefault('step1', []).append(res3)
        results.setdefault('step1', []).append(res4)


        logger.info(">>>step2: run virt-who with -c option multiple times")
        cmd = "mv %s /root/" % extra_config_file
        self.runcmd(cmd, self.ssh_host(), desc="move extra file to /root/")
        extra_config_file = "/root/hypervisor2.conf"
        cmd = "virt-who -c %s -c %s" % (config_file, extra_config_file)
        data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120)
        res2 = self.vw_msg_search(str(data), guest_uuid, exp_exist=True)
        res3 = self.vw_msg_search(str(data), ext_guest_uuid, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)
        results.setdefault('step2', []).append(res3)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/18 Yuefen<yuefliu@redhat.com>
# - Case created to validate config extra option
# - BZ:https://bugzilla.redhat.com/show_bug.cgi?id=1542652 
