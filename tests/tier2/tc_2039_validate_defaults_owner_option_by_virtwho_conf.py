# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136727')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
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
        register_owner = register_config['owner']

        # Case Steps
        logger.info(">>>step1: disable owner option in /etc/virt-who.d/, "
                    "set correct owner in /etc/virt-who.conf")
        self.vw_option_disable("owner", config_file)
        self.vw_option_enable("owner", virtwho_conf)
        self.vw_option_update_value("owner", register_owner, virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        res2 = self.vw_msg_search(rhsm_output, guest_uuid, exp_exist=True)
        results.setdefault('step1', []).append(res1)
        results.setdefault('step1', []).append(res2)

        logger.info(">>>step2: disable owner option in /etc/virt-who.d/, "
                    "set owner=xxxxxx in /etc/virt-who.conf")
        self.vw_option_update_value("owner", "xxxxxx", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner.* is different|"
                    "Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step2', []).append(res1)
        results.setdefault('step2', []).append(res2)

        logger.info(">>>step3: skip this step because owner cannot be set to no-ascci")
        # logger.info(">>>step3: disable owner option in /etc/virt-who.d/, "
        #             "set owner=红帽©¥®ðπ∉ in /etc/virt-who.conf")
        # self.vw_option_update_value("owner", "红帽©¥®ðπ∉", virtwho_conf)
        # data, tty_output, rhsm_output = self.vw_start()
        # res1 = self.op_normal_value(data, exp_error="nz", exp_thread=1, exp_send=0)
        # results.setdefault('step3', []).append(res1)

        logger.info(">>>step4: disable owner option in /etc/virt-who.d/, "
                    "set owner= in /etc/virt-who.conf")
        self.vw_option_update_value("owner", "", virtwho_conf)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner not in|"
                    "owner.* not set|"
                    "virt-who can't be started|"
                    "Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2|3", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step4', []).append(res1)
        results.setdefault('step4', []).append(res2)

        logger.info(">>>step5: correct owner in /etc/virt-who.conf, "
                    "but wrong owner in /etc/virt-who.d/ config file")
        self.vw_option_update_value("owner", register_owner, virtwho_conf)
        self.vw_option_enable("owner", config_file)
        self.vw_option_update_value("owner", "xxxxxx", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        msg_list = ["owner.* is different|"
                    "Communication with subscription manager failed"]
        res1 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
        res2 = self.msg_validation(rhsm_output, msg_list, exp_exist=True)
        results.setdefault('step5', []).append(res1)
        results.setdefault('step5', []).append(res2)

        # Case Result
        self.vw_case_result(results)


if __name__ == "__main__":
    unittest.main()
