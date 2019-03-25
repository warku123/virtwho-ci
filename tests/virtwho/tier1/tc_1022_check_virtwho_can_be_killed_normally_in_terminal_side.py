# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133732')
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        self.vw_thread_clean()

        # case steps
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
            ret, output = self.runcmd(cmd, self.ssh_host())
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

        # case result
        self.vw_case_result(results)
