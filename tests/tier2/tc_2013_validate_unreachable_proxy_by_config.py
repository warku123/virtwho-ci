# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-136709')
        hypervisor_type = self.get_config('hypervisor_type')
        compose_id = self.get_config('rhel_compose')
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] < '0.25.7':
            self.vw_case_skip("virt-who version")
        if hypervisor_type in ('libvirt-local', 'vdsm'):
            self.vw_case_skip(hypervisor_type)
        self.vw_case_init()

        # Case Config
        results = dict()
        sysconfig_file = "/etc/sysconfig/virt-who"
        vw_conf = "/etc/virt-who.conf"
        conf_file = "/etc/virt-who.d/virtwho-config.conf"
        self.vw_option_enable('[global]', vw_conf)
        self.vw_option_enable('debug', vw_conf)
        self.vw_option_update_value('debug', 'True', vw_conf)
        self.vw_option_enable('[defaults]', vw_conf)
        self.vw_etc_d_mode_create('virtwho-config', conf_file)
        register_config = self.get_register_config()
        register_server = register_config['server']
        hypervisor_config = self.get_hypervisor_config()
        hypervisor_server = hypervisor_config['ssh_hypervisor']['host']
        good_squid_server = "{0}:{1}".format(deploy.proxy.server, deploy.proxy.port)
        wrong_squid_server = "10.73.3.24:9999"
        types = {'type1': 'http_proxy',
                 'type2': 'https_proxy'}

        # Case Steps
        logger.info(">>>step1: run with good proxy server")
        for name, option in sorted(types.items(), key=lambda item: item[0]):
            logger.info("+++ {0}: run virt-who to check {1} +++".format(name, option))
            if option == "http_proxy":
                value = "http://{0}".format(good_squid_server)
            else:
                value = "https://{0}".format(good_squid_server)
            self.vw_option_add(option, value, filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            res2 = self.vw_msg_search(
                rhsm_output, "Connection built.*{0}".format(good_squid_server))
            res3 = self.vw_msg_search(
                rhsm_output, "Using proxy.*{0}".format(good_squid_server))
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            results.setdefault('step1', []).append(res3)
            self.vw_option_del(option, filename=sysconfig_file)

        logger.info(">>>step2: run with bad proxy server and no_proxy")
        for name, option in sorted(types.items(), key=lambda item: item[0]):
            logger.info("=== {0}: bad {1} test ===".format(name, option))
            logger.info("+++ run virt-who with bad {0} +++".format(option))
            if option == "http_proxy":
                value = "http://{0}".format(wrong_squid_server)
            if option == "https_proxy":
                value = "https://{0}".format(wrong_squid_server)
            self.vw_option_add(option, value, filename=sysconfig_file)
            data, tty_output, rhsm_output = self.vw_start(exp_send=0, exp_error=True)
            error_msg = ["Connection refused|"
                         "Cannot connect to proxy|"
                         "Connection timed out"]
            res1 = self.op_normal_value(data, exp_error='1|2', exp_thread=1, exp_send=0)
            res2 = self.msg_validation(rhsm_output, error_msg)
            results.setdefault('step2', []).append(res1)
            results.setdefault('step2', []).append(res2)

            logger.info("+++ Configure no_proxy=[hypervisor_server] "
                        "and rhsm_no_proxy=[register_server] +++")
            self.vw_option_add("no_proxy", register_server, sysconfig_file)
            self.vw_option_update_value("no_proxy", hypervisor_server, sysconfig_file)
            self.vw_option_enable("rhsm_no_proxy", vw_conf)
            self.vw_option_update_value("rhsm_no_proxy", register_server, vw_conf)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1)
            res3 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res3)
            self.vw_option_del('no_proxy', sysconfig_file)
            self.vw_option_del(option, sysconfig_file)
            self.vw_option_disable('rhsm_no_proxy', vw_conf)

        # Case Result
        notes = list()
        if hypervisor_type == 'xen':
            notes.append("(step2) [XEN] Print errors when send mapping")
            if "RHEL-8" in compose_id:
                notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1739358")
            elif "RHEL-7" in compose_id:
                notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1764004")
        self.vw_case_result(results, notes)

        '''WONTFI bz1716337 - virt-who doesn't connect all hypervisors by proxy'''

        '''
        For below scenarios, virt-who connect hypervisor not by proxy.
        "RHEL-8" + ('libvirt-remote', 'hyperv', 'kubevirt')
        "RHEL-7" + "http_proxy" + ('esx', 'libvirt-remote', 'xen', 'rhevm', 'kubevirt')
        "RHEL-7" + "http_proxy" + ('libvirt-remote', 'hyperv', 'kubevirt')
        '''
