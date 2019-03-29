# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133689')
        self.vw_case_init()

        # case config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()

        # case steps
        logger.info(">>>step1: Run virt-who with log-per-config=False in /etc/virt-who.conf")
        self.vw_option_enable("log_per_config", virtwho_conf)
        self.vw_option_update_value("log_per_config", 'False', virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        ret, output = self.runcmd('ls /var/log/rhsm/virtwho*', self.ssh_host())
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
        ret, output = self.runcmd('ls /var/log/rhsm/virtwho*', self.ssh_host())
        if ret != 0 or output is None:
            logger.error("Failed to find /var/log/rhsm/virtwho* files")
            results.setdefault('step2', []).append(False)
        files = output.split('\n')
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
        for fd in files:
            fd = fd.strip()
            ret, output = self.runcmd("cat {0}".format(fd), self.ssh_host())
            if "destination" in fd:
                d1 = self.vw_msg_search(output, guest_uuid, exp_exist=True)
                d2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if d1 is False or d2 is False:
                    logger.error("Failed to validate virtwho.destination file")
                    results.setdefault('step2', []).append(False)
            if "main" in fd:
                m1 = self.vw_msg_search(output, "Report for config", exp_exist=True)
                m2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if m1 is False or m2 is False:
                    logger.error("Failed to validate virtwho.main file")
                    results.setdefault('step2', []).append(False)
            if "rhsm_log" in fd:
                r1 = self.vw_msg_search(output, "Using reporter_id=", exp_exist=True)
                r2 = self.vw_msg_search(output, "ERROR", exp_exist=False)
                if r1 is False or r2 is False:
                    logger.error("Failed to validate virtwho.rhsm_log file")
                    results.setdefault('step2', []).append(False)

        # case result
        self.vw_case_result(results)
