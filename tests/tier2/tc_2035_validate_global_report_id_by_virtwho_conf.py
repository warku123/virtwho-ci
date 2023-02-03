# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136716')
        self.vw_case_init()

        # Case Config
        results = dict()
        virtwho_conf = "/etc/virt-who.conf"
        register_config = self.get_register_config()
        register_type = register_config['type']
        self.vw_option_enable('[global]', virtwho_conf)
        self.vw_option_enable('debug', virtwho_conf)
        self.vw_option_update_value('debug', 'True', virtwho_conf)
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        reporter_id_null = ''
        reporter_id_non_ascii = "红帽©¥®ðπ∉"
        steps = {'step2': reporter_id_null,
                 'step3': reporter_id_non_ascii}
        if "satellite" in register_type:
            del steps['step3']

        # Case Steps
        logger.info(">>>step1: get default reporter_id")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        default_reporter_id = data['reporter_id']
        logger.info("default reporter_id is {0}".format(default_reporter_id))
        results.setdefault("step1", []).append(res)

        for step, value in sorted(steps.items(), key=lambda item: item[0]):
            logger.info(">>>{0}: run virt-who to check reporter_id({1})".format(
                step, value))
            self.vw_option_enable("reporter_id", virtwho_conf)
            self.vw_option_update_value("reporter_id", value, virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(res)
            data['reporter_id'] = data['reporter_id']
            if value == reporter_id_null:
                value = default_reporter_id
            if value == data['reporter_id']:
                logger.info("Succeeded to check, reporter_id({0}) is expected".format(
                    data['reporter_id']))
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to check, reporter_id({0}) is not expected".format(
                    data['reporter_id']))
                results.setdefault(step, []).append(False)

        # Case Result
        notes = list()
        notes.append("Bug(step2): virt-who still uses null value for reporter_id")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1750206")
        notes.append("Bug(step3): error when configured the report_id with special")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1910274")
        self.vw_case_result(results, notes)
