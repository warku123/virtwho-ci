# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136709')
        hypervisor_type = self.get_config('hypervisor_type')
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        sysconfig_file = "/etc/sysconfig/virt-who"
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        self.vw_etc_d_mode_create('virtwho-config', '/etc/virt-who.d/virtwho-config.conf')
        good_squid_server = "10.73.3.248:3128"
        wrong_squid_server = "10.73.3.24:3128"
        types = {'type1':'http_proxy', 'type2':'https_proxy'}

        # Case Steps
        logger.info(">>>step1: run with good proxy server")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s" % (type, option))
            if option == "http_proxy":
                value = "http://{0}".format(good_squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(good_squid_server)
            self.vw_option_add(option, value, filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(rhsm_output, "Connection built.*%s" % good_squid_server)
            res3 = self.vw_msg_search(rhsm_output, "Using proxy.*%s" % good_squid_server)
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            results.setdefault('step1', []).append(res3)
            self.vw_option_del(option, filename=sysconfig_file)

        logger.info(">>>step2: run with wrong proxy server and 'NO_PROXY'")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to check %s with wrong proxy" % (type, option))
            if option == "http_proxy":
                value = "http://{0}".format(wrong_squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(wrong_squid_server)
            self.vw_option_add(option, value, filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            error_msg = "Connection refused|Cannot connect to proxy|Connection timed out"
            res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            res2 = self.vw_msg_search(rhsm_output, error_msg)
            self.vw_option_add("NO_PROXY", "*", filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
            results.setdefault('step2', []).append(res3)
            self.vw_option_del(option, filename=sysconfig_file)
            self.vw_option_del("NO_PROXY", filename=sysconfig_file)

        # Case Result
        notes = list()
        if "hyperv" in hypervisor_type:
            notes.append("Bug(Step1): hyperv doesn't support http_proxy")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1638250")
        self.vw_case_result(results, notes)