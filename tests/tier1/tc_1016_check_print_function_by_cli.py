# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133653')
        self.vw_case_init()

        # case config
        results = dict()
        json_file = "/tmp/file.json"
        host_uuid = self.get_hypervisor_hostuuid()
        guest_uuid = self.get_hypervisor_guestuuid()
        compose_id = self.get_config('rhel_compose')
        hypervisor_type = self.get_config('hypervisor_type')
        if "RHEL-8" in compose_id:
            config_name = "virtwho-config"
            config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
            self.vw_etc_d_mode_create(config_name, config_file)
            cmd = "virt-who -p > {0}".format(json_file)
            cmd_debug = "virt-who -d -p > {0}".format(json_file)
        else:
            cmd = self.vw_cli_base() + "-p > {0}".format(json_file)
            cmd_debug = self.vw_cli_base() + "-d -p > {0}".format(json_file)
        steps = {
            'step1': cmd,
            'step2': cmd_debug
        }

        # case steps
        for step, cmd in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(">>>{0}: run virt-who cli to check print option".format(step))
            data, tty_output, rhsm_output = self.vw_start(cmd, exp_send=0,
                                                          web_check=False)
            res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=0)
            results.setdefault(step, []).append(res)
            ret, output = self.runcmd("cat {0}".format(json_file),
                                      self.ssh_host())
            res = self.vw_msg_search(output, guest_uuid, exp_exist=True)
            results.setdefault(step, []).append(res)
            if hypervisor_type not in ('libvirt-local', 'vdsm'):
                res = self.vw_msg_search(output, host_uuid, exp_exist=True)
                results.setdefault(step, []).append(res)

        # case result
        notes = list()
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type == 'kubevirt':
            notes.append("(step1,2) No kubeconfig option for cli")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1751441")
        self.vw_case_result(results, notes)
