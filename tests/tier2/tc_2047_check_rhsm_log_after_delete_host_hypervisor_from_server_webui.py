# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137103')
        hypervisor_type = self.get_config('hypervisor_type')
        register_config = self.get_register_config()
        register_type = register_config['type']
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: delete virt-who host from webui")
        try:
            vw_host_name = self.get_hostname(self.ssh_host())
            vw_host_uuid='xxx'
            res1 = self.vw_web_host_delete(vw_host_name, vw_host_uuid)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            res2 = self.op_normal_value(data, exp_error="1|2", exp_thread=1, exp_send=0)
            error_msg = ["consumer no longer exists|"
                         ".*has been deleted"]
            res3 = self.msg_validation(rhsm_output, error_msg, exp_exist=True)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
            results.setdefault('step2', []).append(res3)
        except:
            results.setdefault('step2', []).append(False)
            pass
        finally:
            logger.info(">>>step3: re-register host and run virt-who")
            self.system_unregister(self.ssh_host())
            self.system_register(self.ssh_host(), register_type, register_config)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res)

        if "libvirt-local" not in hypervisor_type and "vdsm" not in hypervisor_type:
            logger.info(">>>step4: delete hypervisor from webui")
            host_uuid = self.get_hypervisor_hostuuid()
            host_name = self.get_hypervisor_hostname()
            self.vw_web_host_delete(host_name, host_uuid)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(res)

        # Case Result
        self.vw_case_result(results)
