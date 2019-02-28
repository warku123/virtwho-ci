# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133689")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        self.vw_option_update_value("debug", 'True', virtwho_conf)
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        guest_uuid = self.mode_guest_uuid(mode)

        # Case Steps
        logger.info(">>>step1: Run virt-who with log-per-config=False in /etc/virt-who.conf")
        self.vw_option_enable("log_per_config", virtwho_conf)
        self.vw_option_update_value("log_per_config", 'False', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        ret, output = self.runcmd('ls /var/log/rhsm/virtwho*', self.ssh_host(), desc="list file")
        if ret == 0:
            logger.error("Failed to search, unexpected /var/log/rhsm/virtwho* files exist")
            results.setdefault('step1', []).append(False)
        else:
            logger.info("Succeeded to search, unexpected /var/log/rhsm/virtwho* files not exist")
            results.setdefault('step1', []).append(True)

        logger.info(">>>step2: Run virt-who with log-per-config=True in /etc/virt-who.conf")
        self.vw_option_update_value("log_per_config", 'True', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(res)
        ret, output = self.runcmd('ls /var/log/rhsm/virtwho*', self.ssh_host(), desc="list file")
        if ret != 0 or output is None:
            logger.error("Failed to find /var/log/rhsm/virtwho* files")
            results.setdefault('step2', []).append(False)
        files = output.split('\n')
        ''' check files exist or not'''
        if any("destination" in fd for fd in files):
            logger.info("Succeeded to find virtwho.destination file")
        else:
            logger.error("Failed to find virtwho.destination file")
            results.setdefault('step2', []).append(False)
        if any("main" in fd for fd in files):
            logger.info("Succeeded to find virtwho.main file")
        else:
            logger.error("Failed to find virtwho.main file")
            results.setdefault('step2', []).append(False)
        if any("rhsm_log" in fd for fd in files):
            logger.info("Succeeded to find virtwho.rhsm_log file")
        else:
            logger.error("Failed to find virtwho.rhsm_log file")
            results.setdefault('step2', []).append(False)
        ''' check message is expected or not'''
        for fd in files:
            fd = fd.strip()
            if "destination" in fd:
                ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if d1 is False or d2 is False:
                    logger.error("Failed to validate virtwho.destination file")
                    results.setdefault('step2', []).append(False)
            if "main" in fd:
                ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                m1 = self.vw_msg_search(output, "Report for config", exp_exist=True)
                m2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if m1 is False or m2 is False:
                    logger.error("Failed to validate virtwho.main file")
                    results.setdefault('step2', []).append(False)
            if "rhsm_log" in fd:
                ret, output = self.runcmd("cat %s" % fd, self.ssh_host(), desc="cat file")
                r1 = self.vw_msg_search(output, "Using reporter_id=", exp_exist=True)
                r2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if r1 is False or r2 is False:
                    logger.error("Failed to validate virtwho.rhsm_log file")
                    results.setdefault('step2', []).append(False)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
# - 2018/06/20 yanpliu<yanpliu@redhat.com>
# - update config style and integrate case steps
# - 2018/06/14 yanpliu<yanpliu@redhat.com>
# - Case created
