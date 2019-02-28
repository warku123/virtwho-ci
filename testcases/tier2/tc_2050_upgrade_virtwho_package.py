# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136706")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        compose_id = self.get_exported_param("COMPOSE_ID")
        trigger_name = self.get_exported_param("TRIGGER_NAME")
        if "trigger-rhel" not in trigger_name:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % trigger_name)
        if "libvirt-local" not in mode and "vdsm" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        vw_original = self.vw_pkg_check()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)

        # Case Steps
        try:
            logger.info(">>>step1: uninstall original virt-who")
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_pkg_uninstall()
            results.setdefault('step1', []).append(res1)
            if res2 == False:
                raise FailException("step1: failed to uninstall virt-who")

            logger.info(">>>step2: install old virt-who")
            backup_path = '/root/tmp/'
            cmd = 'mkdir %s ; mv /etc/yum.repos.d/* %s' % (backup_path, backup_path)
            ret, output = self.runcmd(cmd, self.ssh_host(), 'backup repos')
            if "RHEL-8" in compose_id:
                vw_pkg = 'virt-who-0.23.1-1.el8.noarch.rpm'
                cmd_1 = 'wget -P /root/ http://10.66.144.9/projects/virtwho/package/%s' % vw_pkg
                cmd_2 = 'rpm -ivh /root/%s' % vw_pkg
                cmd_3 = 'rm -f /root/%s' % vw_pkg
                ret, output = self.runcmd('%s ; %s ; %s' % (cmd_1, cmd_2, cmd_3), self.ssh_host())
            else:
                self.system_unregister(self.ssh_host())
                self.qa_register(self.ssh_host())
                self.qa_enable_rhel_repo(self.ssh_host())
                cmd = 'rm -rf /var/lib/yum/history/*.sqlite ; yum install virt-who -y'
                ret, output = self.runcmd(cmd, self.ssh_host(), desc='install old virt-who by cdn')
            vw_old = self.vw_pkg_check()
            if ret == 0 and vw_old[9:15] < vw_original[9:15]:
                logger.info('succeeded to install old %s' % vw_old)
                results.setdefault('step2', []).append(True)
            else:
                raise FailException("step2: failed to install old virt-who")

            logger.info(">>>step3: configure options, then run old virt-who")
            if self.system_isregister(self.ssh_host(), server_type, server_ip, mode) is False:
                self.vw_sub_register(self.ssh_host())
            self.vw_etc_d_mode_create(mode, conf_name, conf_file)
            self.vw_etc_conf_disable_all()
            self.vw_option_enable('VIRTWHO_INTERVAL', '/etc/sysconfig/virt-who')
            self.vw_option_update_value('VIRTWHO_INTERVAL', '60', '/etc/sysconfig/virt-who')
            self.vw_option_enable('[global]', '/etc/virt-who.conf')
            self.vw_option_enable('debug', '/etc/virt-who.conf')
            self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res)

            logger.info(">>>step4: upgrade virt-who to original")
            cmd = 'mv %s* /etc/yum.repos.d/ ; rm -rf %s' % (backup_path, backup_path)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc='restore rhel repo')
            cmd = 'yum upgrade virt-who -y'
            ret, output = self.runcmd(cmd, self.ssh_host(), desc='upgrade virt-who package')
            if ret == 0 and self.vw_pkg_check() == vw_original:
                logger.info('succeeded to upgrade virt-who to %s' % vw_original)
                results.setdefault('step4', []).append(True)
            else:
                raise FailException("step4: failed to upgrade virt-who")

            logger.info(">>>step5: check configured options are not covered, then run virt-who")
            ret, output_1 = self.runcmd('cat /etc/sysconfig/virt-who', self.ssh_host())
            ret, output_2 = self.runcmd('cat /etc/virt-who.conf', self.ssh_host())
            ret, output_3 = self.runcmd('ls /etc/virt-who.d', self.ssh_host())
            res1 = self.vw_msg_search(output_1, 'VIRTWHO_INTERVAL=60')
            res2 = self.vw_msg_search(output_2, 'debug=True')
            res3 = self.vw_msg_search(output_3, '%s.conf' % mode.lower())
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)
            results.setdefault('step5', []).append(res3)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res4 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step5', []).append(res4)
            self.fd_delete(self.ssh_host(), backup_path)
        except:
            results.setdefault('step', []).append(False)
            pass

        finally:
            logger.info(">>>step 6: recovery virt-who to original")
            vw_final = self.vw_pkg_check()
            if vw_final == vw_original:
                logger.info('virt-who is the tested version, no need to recovery')
                results.setdefault('step6', []).append(True)
            else:
                ret, output = self.runcmd('rm -rf /etc/yum.repos.d/*', self.ssh_host())
                repo_file = '/etc/yum.repos.d/compose.repo'
                self.rhel_compose_repo(self.ssh_host(), compose_id, repo_file)
                if vw_final is None:
                    cmd = 'yum install virt-who -y'
                else:
                    cmd = 'rpm -e virt-who ; yum install virt-who -y'
                ret, output = self.runcmd(cmd, self.ssh_host())
                if ret == 0 and self.vw_pkg_check() == vw_original:
                    logger.info('succeeded to recovery virt-who package')
                    results.setdefault('step6', []).append(True)
                else:
                    raise FailException('step6: failed to recovery virt-who package')

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/11 Yuefen<yuefliu@redhat.com>
# - 2018/12/11 Use virt-who-0.23.1-1 as old pkg to support esx
# - 2018/08/01 Yuefen<yuefliu@redhat.com>
# - 2018/08/01 Upgrade step3 for rhel8 testing
# - 2018/08/01 Yuefen<yuefliu@redhat.com>
