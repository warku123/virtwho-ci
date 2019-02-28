# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133688")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        log_dir = "/var/log/rhsm/virtwho/"
        log_file = "/var/log/rhsm/virtwho/rhsm.log"
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: Run virt-who with log-dir setting in /etc/virt-who.conf")
        self.vw_option_enable("log_dir", virtwho_conf)
        self.vw_option_update_value("log_dir", log_dir, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        ret, output = self.runcmd("ls %s" %log_file, self.ssh_host(), desc="ls virtwho/rhsm.log")
        if ret == 0:
            logger.info("Succeeded to find file: %s" %log_file)
            ret, output = self.runcmd("cat %s" %log_file, self.ssh_host(), desc="cat virtwho/rhsm.log")
            d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
            d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
            if d1 is False or d2 is False:
                results.setdefault('step1', []).append(False)
        else:
            logger.error("%s is not exist" % log_file)
            results.setdefault('step1', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/28 yanpliu<yanpliu@redhat.com>
# - add Note for Bug 1554258
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps
# - 2018/06/14 yanpliu<yanpliu@redhat.com>
# - Case created
