# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133741')
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        compose_id = self.get_config('rhel_compose')
        keywords = "test virt-who instead or not"
        steps = {'step1':'/root/virt-who.py', 'step2':'/root/virt-who'}
        self.vw_thread_clean()

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>{0}: run virt-who to check {1} instead or not".format(step, option))
            if "RHEL-7" in compose_id:
                cmd = ('cat <<EOF > %s\n'
                        '#!/usr/bin/python\n'
                        'print "%s"\n'
                        'EOF'
                      ) % (option, keywords)
                ret, output = self.runcmd(cmd, self.ssh_host())
                cmd = "python {0}".format(option)
                ret, output = self.runcmd(cmd, self.ssh_host())
            else:
                cmd = ('cat <<EOF > %s\n'
                        '#!/usr/libexec/platform-python\n'
                        'print("%s")\n'
                        'EOF'
                      ) % (option, keywords)
                ret, output = self.runcmd(cmd, self.ssh_host())
                cmd = "/usr/libexec/platform-python {0}".format(option)
                ret, output = self.runcmd(cmd, self.ssh_host())
            if ret == 0 and keywords in output:
                logger.info("Succeeded to run {0}".format(option))
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to run {0}".format(option))
                results.setdefault(step, []).append(False)
            cmd = "virt-who -d"
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(tty_output, keywords, exp_exist=False)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # case result
        self.vw_case_result(results)
