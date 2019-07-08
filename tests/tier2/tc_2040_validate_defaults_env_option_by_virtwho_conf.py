# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136724')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            self.vw_case_skip("virt-who version")
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        self.vw_option_enable("[defaults]", virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        guest_uuid = self.get_hypervisor_guestuuid()
        register_config = self.get_register_config()
        register_env = register_config['env']

        # Case Steps
        logger.info(">>>step1: disable env option in /etc/virt-who.d/, set correct env in /etc/virt-who.conf")
        self.vw_option_disable("env", config_file)
        self.vw_option_enable("env", virtwho_conf)
        self.vw_option_update_value("env", register_env, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: disable env option in /etc/virt-who.d/, set env=xxxxxx in /etc/virt-who.conf")
        self.vw_option_update_value("env", "xxxxxx", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env.*differs|env.* is different|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: disable env option in /etc/virt-who.d/, set env=红帽©¥®ðπ∉ in /etc/virt-who.conf")
        self.vw_option_update_value("env", "红帽©¥®ðπ∉", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["codec can't decode|Communication with subscription manager failed|env.*differs"]
        res1 = self.op_normal_value(data, exp_error="1|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step3', []).append(res1)
        results.setdefault('step3', []).append(res2)

        logger.info(">>>step4: disable env option in /etc/virt-who.d/, set env= in /etc/virt-who.conf")
        self.vw_option_update_value("env", "", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env not in|env.* not set|virt-who can't be started|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: correct env in /etc/virt-who.conf, but wrong env in /etc/virt-who.d/ config file")
        self.vw_option_update_value("env", register_env, virtwho_conf)
        self.vw_option_enable("env", config_file)
        self.vw_option_update_value("env", "xxxxxx", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["env.*differs|env.* is different|Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        notes = list()
        register_type = self.get_config('register_type')
        if "stage" in register_type:
            notes.append("Bug(Step2,Step3,Step4,Step5): Set env to wrong or special or null value, still can sent report normally for stage")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530426")
        else:
            notes.append("Bug(Step4): Set env to null value, still can sent report normally for sat62/sat63")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1530290")
        self.vw_case_result(results, notes)
