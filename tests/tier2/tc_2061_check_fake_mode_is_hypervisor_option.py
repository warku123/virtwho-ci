# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-175058')
        self.vw_case_init()

        # case config
        results = dict()
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        hypervisor_type = self.get_config('hypervisor_type')
        json_file = "/tmp/fake.json"
        conf_file = "/etc/virt-who.d/fake.conf"

        # case steps
        logger.info(">>>step1: create json file with bad is_hypervisor")
        cli = "virt-who -d"
        self.vw_fake_json_create(cli, json_file)
        self.vw_etc_d_delete_all()
        if hypervisor_type in ("libvirt-local", "vdsm"):
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=True)
        else:
            self.vw_fake_conf_create(conf_file, json_file, is_hypervisor=False)

        logger.info(">>>step2: run virt-who with fake conf")
        error_msg = "Fake virt file.*is not properly formed"
        data, tty_output, rhsm_output = self.vw_start(exp_send=0)
        res1 = self.op_normal_value(data, exp_error=2, exp_thread=0, exp_send=0)
        res2 = self.vw_msg_search(rhsm_output, error_msg)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: disabel is_hypervisor option")
        war_msg = 'Required option: "is_hypervisor" is missing in: ' \
                  '"fake" using default "True"'
        self.vw_option_disable('is_hypervisor', conf_file)
        if hypervisor_type in ("libvirt-local", "vdsm"):
            data, tty_output, rhsm_output = self.vw_start(exp_send=0)
            res1 = self.op_normal_value(data, exp_error=2, exp_thread=0, exp_send=0)
            res2 = self.vw_msg_search(rhsm_output, error_msg)
            res3 = self.vw_msg_search(rhsm_output, war_msg)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)
            results.setdefault('step3', []).append(res3)
        else:
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(rhsm_output, war_msg)
            results.setdefault('step3', []).append(res1)
            results.setdefault('step3', []).append(res2)

        # case result
        self.vw_case_result(results)
