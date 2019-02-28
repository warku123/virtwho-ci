# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133732")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        self.vw_thread_clean()

        # Case Steps
        logger.info(">>>step1: start virt-who thread to keep it running")
        cmd = "virt-who -d"
        t1 = threading.Thread(target=self.runcmd, args=(cmd, self.ssh_host()))
        t1.start()
        time.sleep(15)
        if self.vw_callback_thread_num() == 1:
            logger.info("Succeeded to start virt-who by cli")
            results.setdefault('step1', []).append(True)
        else:
            logger.error("Failed to start virt-who by cli")
            results.setdefault('step1', []).append(False)

        logger.info(">>>step2: kill virt-who by 'kill -2'")
        for i in range(5):
            cmd = "ps -ef | grep virt-who -i | grep -v grep | awk '{print $2}' | xargs -I {} kill -2 {}"
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="kill -2 virt-who")
            time.sleep(15)
            if self.vw_callback_thread_num() == 0:
                is_killed = "Yes"
                break
            else:
                is_killed = "No"
                logger.warning("Failed to kill virt-who, try again ...")
        if is_killed == "Yes":
            logger.info("Succeeded to kill virt-who")
            results.setdefault('step2', []).append(True)
        else:
            logger.info("Failed to kill virt-who")
            results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/08/20 Eko<hsun@redhat.com>
# - try again when failed to kill virt-who
# - 2018/06/08 yuefliu<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
