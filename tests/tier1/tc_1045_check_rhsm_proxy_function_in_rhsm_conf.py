# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133691')
        hypervisor_type = self.get_config('hypervisor_type')
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable('[global]', '/etc/virt-who.conf')
        self.vw_option_enable('debug', '/etc/virt-who.conf')
        self.vw_option_update_value('debug', 'True', '/etc/virt-who.conf')
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)
        register_config = self.get_register_config()
        register_server = register_config['server']
        if "libvirt-local" in hypervisor_type:
            owner = register_config['owner']
            cmd = "echo -e '[{0}]\ntype=libvirt\nowner={1}' > {2}".format(
                config_name, owner, config_file)
            ret, output = self.runcmd(cmd, self.ssh_host())
        proxy_server = deploy.proxy.server
        proxy_port = deploy.proxy.port
        bad_proxy_server = "xxx.eng.pek2.redhat.com"
        bad_proxy_port = "0000"
        error_msg = ["Connection refused|"
                     "Unable to connect to: .*{0}".format(bad_proxy_server)]

        # Case Steps
        try:
            logger.info(">>>step1: set /etc/rhsm/rhsm.conf with good "
                        "proxy_hostname and proxy_port")
            self.vw_option_update_value(
                "proxy_hostname", proxy_server, '/etc/rhsm/rhsm.conf')
            self.vw_option_update_value("proxy_port", proxy_port, '/etc/rhsm/rhsm.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step1', []).append(s1)
            s2 = self.vw_msg_search(
                rhsm_output, "Connection built.*{0}".format(proxy_server))
            results.setdefault('step1', []).append(s2)
            s3 = self.vw_msg_search(rhsm_output, "Using proxy.*{0}".format(proxy_server))
            results.setdefault('step1', []).append(s3)

            logger.info(">>>step2: set wrong proxy in /etc/rhsm/rhsm.conf")
            self.vw_option_update_value(
                "proxy_hostname", bad_proxy_server, '/etc/rhsm/rhsm.conf')
            self.vw_option_update_value(
                "proxy_port", bad_proxy_port, '/etc/rhsm/rhsm.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            s2 = self.msg_validation(rhsm_output, error_msg, exp_exist=True)
            results.setdefault('step2', []).append(s1)
            results.setdefault('step2', []).append(s2)

            logger.info(">>>step3: set no_proxy=[server_hostname] in /etc/rhsm/rhsm.conf")
            self.vw_option_update_value(
                "no_proxy", register_server, '/etc/rhsm/rhsm.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step3', []).append(s1)

            logger.info(">>>step4: set no_proxy=* in /etc/rhsm/rhsm.conf")
            self.vw_option_update_value("no_proxy", '*', '/etc/rhsm/rhsm.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step4', []).append(s1)
            self.vw_option_update_value("no_proxy", '', '/etc/rhsm/rhsm.conf')

            logger.info(">>>step5: set rhsm_no_proxy=[server_hostname]"
                        " in /etc/virt-who.conf")
            self.vw_option_enable('[defaults]', '/etc/virt-who.conf')
            self.vw_option_enable('rhsm_no_proxy', '/etc/virt-who.conf')
            self.vw_option_update_value(
                'rhsm_no_proxy', register_server, '/etc/virt-who.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step5', []).append(s1)

            logger.info(">>>step6: set rhsm_no_proxy=* in /etc/virt-who.conf")
            self.vw_option_update_value('rhsm_no_proxy', '*', '/etc/virt-who.conf')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step6', []).append(s1)
            self.vw_option_disable('rhsm_no_proxy', '/etc/virt-who.conf')

            if hypervisor_type not in ('libvirt-local', 'vdsm'):
                logger.info(">>>step7: set rhsm_no_proxy=[server_hostname] "
                            "in /etc/virt-who.d/x.conf")
                self.vw_option_add('rhsm_no_proxy', register_server, config_file)
                data, tty_output, rhsm_output = self.vw_start()
                s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                results.setdefault('step7', []).append(s1)

                logger.info(">>>step8: set rhsm_no_proxy=* in /etc/virt-who.d/x.conf")
                self.vw_option_update_value('rhsm_no_proxy', '*', config_file)
                data, tty_output, rhsm_output = self.vw_start()
                s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                results.setdefault('step8', []).append(s1)
                self.vw_option_del('rhsm_no_proxy', config_file)
            else:
                logger.info('Skip step7 and step8 for {0}'.format(hypervisor_type))

            logger.info(">>>step9: set no_proxy=[server_hostname]"
                        " in /etc/sysconfig/virt-who")
            self.vw_option_add('no_proxy', register_server, '/etc/sysconfig/virt-who')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step9', []).append(s1)

            logger.info(">>>step10: set no_proxy=* in /etc/sysconfig/virt-who")
            self.vw_option_update_value('no_proxy', '*', '/etc/sysconfig/virt-who')
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step10', []).append(s1)
            self.vw_option_del('rhsm_no_proxy', '/etc/sysconfig/virt-who')

        except:
            results.setdefault('step except', []).append(False)
            pass

        finally:
            self.vw_option_update_value('proxy_hostname', '', '/etc/rhsm/rhsm.conf')
            self.vw_option_update_value('proxy_port', '', '/etc/rhsm/rhsm.conf')
            self.vw_option_update_value('no_proxy', '', "/etc/rhsm/rhsm.conf")

        # case result
        self.vw_case_result(results)
