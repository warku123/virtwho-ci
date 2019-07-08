# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136637')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        host_uuid = self.get_hypervisor_hostuuid()

        # Case Steps
        logger.info(">>>step1: run virt-who with filter_hosts=''")
        self.vw_option_add("filter_hosts", r"''", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step1', []).append(s2)

        logger.info('>>>step2: run virt-who with filter_hosts=""')
        self.vw_option_update_value("filter_hosts", r'\"\"', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step2', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step2', []).append(s2)

        logger.info(">>>step3: run virt-who with filter_hosts='host_uuid'")
        self.vw_option_update_value("filter_hosts", r"'%s'" % host_uuid, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step1', []).append(s2)

        logger.info('>>>step4: run virt-who with filter_hosts="host_uuid"')
        self.vw_option_update_value("filter_hosts", r'\"%s\"' % host_uuid, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step4', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step4', []).append(s2)
        self.vw_option_del("filter_hosts", config_file)

        logger.info(">>>step5: run virt-who with exclude_hosts=''")
        self.vw_option_add("exclude_hosts", r"''", config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step5', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step5', []).append(s2)

        logger.info('>>>step6: run virt-who with exclude_hosts=""')
        self.vw_option_update_value("exclude_hosts", r'\"\"', config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step6', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=True)
        results.setdefault('step6', []).append(s2)

        logger.info(">>>step7: run virt-who with exclude_hosts='host_uuid'")
        self.vw_option_update_value("exclude_hosts", r"'%s'" % host_uuid, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step7', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step7', []).append(s2)

        logger.info('>>>step8: run virt-who with exclude_hosts="host_uuid"')
        self.vw_option_update_value("exclude_hosts", r'\"%s\"' % host_uuid, config_file)
        data, tty_output, rhsm_output = self.vw_start()
        s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step8', []).append(s1)
        s2 = self.vw_msg_search(str(data), host_uuid, exp_exist=False)
        results.setdefault('step8', []).append(s2)
        self.vw_option_del("exclude_hosts", config_file)

        # Case Result
        self.vw_case_result(results)
