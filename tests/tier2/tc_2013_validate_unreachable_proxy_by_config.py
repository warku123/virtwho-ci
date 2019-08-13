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
        vw_conf = "/etc/virt-who.conf"
        self.vw_option_enable('[global]', vw_conf)
        self.vw_option_enable('debug', vw_conf)
        self.vw_option_update_value('debug', 'True', vw_conf)
        self.vw_option_enable('[defaults]', vw_conf)
        self.vw_etc_d_mode_create('virtwho-config', '/etc/virt-who.d/virtwho-config.conf')
        register_config = self.get_register_config()
        register_server = register_config['server']
        hypervisor_config = self.get_hypervisor_config()
        hypervisor_server = hypervisor_config['ssh_hypervisor']['host']
        if hypervisor_type == 'rhevm':
            hypervisor_server = self.get_hostname(hypervisor_config['ssh_hypervisor'])
        good_squid_server = "10.73.3.248:3128"
        wrong_squid_server = "10.73.3.24:3128"
        types = {'type1':'http_proxy', 'type2':'https_proxy'}

        # Case Steps
        logger.info(">>>step1: run with good proxy server")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>%s: run virt-who to check %s" % (type, option))
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

        logger.info(">>>step2: run with bad proxy server and no_proxy")
        for type, option in sorted(types.items(), key=lambda item:item[0]):
            logger.info(">>%s: ------ %s test------" % (type, option))
            logger.info("> run virt-who with bad {0}".format(option))
            if option == "http_proxy":
                value = "http://{0}".format(wrong_squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(wrong_squid_server)
            self.vw_option_add(option, value, filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            error_msg = "Connection refused|Cannot connect to proxy|Connection timed out"
            res1 = self.op_normal_value(data, exp_error='1|2', exp_thread=1, exp_send=0)
            res2 = self.vw_msg_search(rhsm_output, error_msg)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)
            logger.info("> configure no_proxy=[register_server] in /etc/sysconfig/virt-who")
            self.vw_option_add("no_proxy", register_server, sysconfig_file)
            if hypervisor_type in ('libvirt-remote', 'hyperv', 'kubevirt'):
                logger.info("virt-who connect hypervisor '{0}' not by proxy".format(hypervisor_type))
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                results.setdefault('step2', []).append(res3)
            else:
                logger.info("virt-who connect hypervisor '{0}' by proxy".format(hypervisor_type))
                error_msg = "Cannot connect to proxy"
                data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
                res3 = self.op_normal_value(data, exp_error='1|2', exp_thread=1, exp_send=0)
                res4 = self.vw_msg_search(rhsm_output, error_msg)
                logger.info("> Configure no_proxy=[hypervisor_server] and rhsm_no_proxy=[register_server]")
                self.vw_option_update_value("no_proxy", hypervisor_server, sysconfig_file)
                self.vw_option_enable("rhsm_no_proxy", vw_conf)
                self.vw_option_update_value("rhsm_no_proxy", register_server, vw_conf)
                data, tty_output, rhsm_output = self.vw_start(exp_send=1)
                res5 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                results.setdefault('step2', []).append(res3)
                results.setdefault('step2', []).append(res4)
                results.setdefault('step2', []).append(res5)
            self.vw_option_del('no_proxy', sysconfig_file)
            self.vw_option_del(option, sysconfig_file)
            self.vw_option_disable('rhsm_no_proxy', vw_conf)

        # Case Result
        logger.info("WONTFI bz1716337 - virt-who doesn't connect all hypervisors by proxy")
        notes = list()
        if hypervisor_type == 'xen':
            notes.append("(step2) [XEN] Succeeded to send mapping but always print errors")
            notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1739358")
        self.vw_case_result(results, notes)