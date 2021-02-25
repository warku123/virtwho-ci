# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-198867')
        compose_id = self.get_config('rhel_compose')
        hypervisor_type = self.get_config('hypervisor_type')
        if "kubevirt" not in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        if "RHEL-9" not in compose_id:
            self.vw_case_skip(compose_id)
        self.vw_case_init()

        # case config
        results = dict()
        self.vw_option_enable('[global]', "/etc/virt-who.conf")
        self.vw_option_enable('debug', "/etc/virt-who.conf")
        self.vw_option_update_value('debug', 'True', "/etc/virt-who.conf")
        config_name = "virtwho-config"
        config_file = "/etc/virt-who.d/{0}.conf".format(config_name)
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: configure kubeconfig without cert and run virt-who")
        kube_config_file = "/root/kube.conf_no_cert"
        kube_config_url = deploy.kubevirt.kube_config_url_no_cert
        cmd = "rm -f {1}; curl -L {0} -o {1}; sync".format(kube_config_url, kube_config_file)
        self.runcmd(cmd, self.ssh_host())
        self.vw_option_update_value("kubeconfig", kube_config_file, config_file)

        for option in ("none", "", "0", "False"):
            if option == "none":
                logger.info("> run virt-who without insecure= option")
            else:
                self.vw_option_add("insecure", option, config_file)
                logger.info("> configure virt-who run with insecure={0}".format(option))
            data, tty_output, rhsm_output = self.vw_start(exp_error=True, exp_send=0)
            error_msg = "certificate verify failed"
            res1 = self.op_normal_value(data, exp_error=1, exp_thread=1, exp_send=0)
            res2 = self.vw_msg_search(rhsm_output, error_msg)
            results.setdefault('step1', []).append(res1)
            results.setdefault('step1', []).append(res2)
            self.vw_option_del("insecure", config_file)

        logger.info(">>>step2: test insecure=1/True can ignore checking cert")
        for option in ("1", "True"):
            logger.info("> configure virt-who run with insecure={0}".format(option))
            self.vw_option_add("insecure", option, config_file)
            data, tty_output, rhsm_output = self.vw_start(exp_error=False, exp_send=1)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault('step2', []).append(res)
            self.vw_option_del("insecure", config_file)

        self.runcmd("rm -rf {0}".format(kube_config_file), self.ssh_host())

        # case result
        self.vw_case_result(results)
