# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-198375')
        compose_id = self.get_config('rhel_compose')
        if 'RHEL-9' not in compose_id:
            self.vw_case_skip(compose_id)
        self.vw_case_init()

        # Case Config
        results = dict()
        conf_file = "/etc/virt-who.conf"
        conf_file_backup = "/etc/virt-who.conf.backup"
        sysconfig_file = "/etc/sysconfig/virt-who"
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        try:
            logger.info(">>>step1: configure and backup /etc/virt-who.conf")
            self.vw_etc_conf_disable_all()
            self.runcmd('cp {0} {1}'.format(conf_file, conf_file_backup), self.ssh_host())

            logger.info(">>>step2: create /etc/sysconfig/virt-who file")
            cmd = ('cat <<EOF > {0}\n'
                   'VIRTWHO_DEBUG = 1\n'
                   'VIRTWHO_ONE_SHOT = 0\n'
                   'VIRTWHO_INTERVAL = 120\n'
                   'http_proxy = {1}:{2}\n'
                   'no_proxy = *\n'
                   'EOF'
                   ).format(sysconfig_file, deploy.proxy.server, deploy.proxy.port)
            self.runcmd(cmd, self.ssh_host())

            logger.info(">>>step3: run migrateconfiguration.py script")
            cmd = "/usr/bin/python3 /usr/lib/python3.9/site-packages/virtwho/migrate/migrateconfiguration.py"
            self.runcmd(cmd, self.ssh_host())

            logger.info(">>>step4: check the configurations in {0} are migrated to {1}"
                        .format(sysconfig_file, conf_file))
            ret, output = self.runcmd("cat {0}".format(conf_file), self.ssh_host())
            msg1 = "[global]\n" \
                   "#migrated\n" \
                   "interval=120\n" \
                   "#migrated\n" \
                   "debug=True\n" \
                   "#migrated\n" \
                   "oneshot=False"
            msg2 = "[system_environment]\n" \
                   "#migrated\n" \
                   "http_proxy=squid.corp.redhat.com:3128\n" \
                   "#migrated\n" \
                   "no_proxy=*"
            results.setdefault('step4', []).append(msg1 in output)
            results.setdefault('step4', []).append(msg2 in output)

            logger.info(">>>step5: run virt-who to test the migrated options working well")
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=120)
            res2 = self.vw_msg_search(rhsm_output, msg="\[.*DEBUG\]")
            results.setdefault('step5', []).append(res1)
            results.setdefault('step5', []).append(res2)


        finally:
            logger.info(">>>step6: recover environments")
            self.runcmd('cp {0} {1} ; rm -f {0}'.format(conf_file_backup, conf_file),
                        self.ssh_host(), desc="recover the /etc/virt-who.conf file")
            self.runcmd('rm -f {0}'.format(sysconfig_file),
                        self.ssh_host(), desc="remove the /etc/sysconfig/virt-who file")

        # Case Result
        self.vw_case_result(results)
