# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133741")
        compose_id = self.get_exported_param("COMPOSE_ID")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_etc_d_mode_create(mode, conf_name, conf_file)
        instead_file1 = "/root/virt-who.py"
        instead_file2 = "/root/virt-who"
        keywords = "test virt-who instead or not"
        steps = {'step1':instead_file1, 'step2':instead_file2}
        self.vw_thread_clean()

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s instead or not" % (step, option))
            if "RHEL-8" in compose_id:
                cmd = ('cat <<EOF > %s\n'
                        '#!/usr/libexec/platform-python\n'
                        'print("%s")\n'
                        'EOF'
                      ) % (option, keywords)
                ret, output = self.runcmd(cmd, self.ssh_host(), desc="create file")
                cmd = "/usr/libexec/platform-python %s" % (option)
                ret, output = self.runcmd(cmd, self.ssh_host(), desc="chmod file and run")
            else:
                cmd = ('cat <<EOF > %s\n'
                        '#!/usr/bin/python\n'
                        'print "%s"\n'
                        'EOF'
                      ) % (option, keywords)
                ret, output = self.runcmd(cmd, self.ssh_host(), desc="create file")
                cmd = "python %s" % (option)
                ret, output = self.runcmd(cmd, self.ssh_host(), desc="chmod file and run")
            if ret == 0 and keywords in output:
                logger.info("Succeeded to run %s" % option)
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to run %s" % option)
                results.setdefault(step, []).append(False)
            cmd = "virt-who -d"
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(tty_output, keywords, exp_exist=False)
            results.setdefault(step, []).append(res1)
            results.setdefault(step, []).append(res2)

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/12/10 Yuefen<yuefliu@redhat.com>
# - Add vw_etc_d_mode_create() to enable mode
# - 2018/12/05 Yuefen<yuefliu@redhat.com>
# - Update to use vw_etc_d_mode_create due to Bug1655626 fix
# - 2018/06/14 Eko<hsun@redhat.com>
# - improve the test steps
# - 2018/06/07 yuefliu<yuefliu@redhat.com>
# - Case created and support to run rhel6/7/8
