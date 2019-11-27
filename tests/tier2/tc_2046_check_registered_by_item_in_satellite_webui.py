# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-137102')
        hypervisor_type = self.get_config('hypervisor_type')
        register_type = self.get_config('register_type')
        if 'stage' in register_type:
            self.vw_case_skip(register_type)
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
        host_name = self.get_hypervisor_hostname()
        guest_name = self.get_hostname(self.ssh_guest())
        guest_uuid = self.get_hypervisor_guestuuid()
        register_config = self.get_register_config()

        # Case Steps
        logger.info(">>>step1: run virt-who to send mappings")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)

        logger.info(">>>step2: get guest_id and vw_host_uuid")
        if 'libvirt-local' in hypervisor_type or 'vdsm' in hypervisor_type:
            exp_list = {'hypervisor':'admin', 'guest':'admin'}
        else:
            # vw_host_name = self.get_hostname(self.ssh_host())
            # out = self.satellite_hosts_get(self.ssh_host(), register_config, vw_host_name, "xxx")
            # vw_host_uuid = out['subscription_facet_attributes']['uuid']
            # hypervisor should be vw_host_uuid, but due to Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1455041
            exp_list = {'hypervisor':'null', 'guest':'admin'}

        logger.info(">>>step3: check registered_by info for hypervisor and guest")
        for check_type, exp in sorted(exp_list.items(), key=lambda item:item[0]):
            logger.info(">>>check {0}".format(check_type))
            logger.info(">>>exp:{0}".format(exp))
            if check_type == "hypervisor":
                output = self.satellite_hosts_get(self.ssh_host(), register_config,
                                                  host_name, host_uuid, "get hypervisor info")
            else:
                output = self.satellite_hosts_get(self.ssh_host(), register_config,
                                                  guest_name, guest_uuid, "get guest info")
            if output is not None:
                user = output["subscription_facet_attributes"]["user"]
                if user is not False and user is not None and 'login' in user.keys():
                    registered_by = user['login']
                    if registered_by == exp:
                        logger.info("succeded to check registered_by is '{}'".format(exp))
                        results.setdefault('step3', []).append(True)
                    else:
                        logger.error("failed to check registered_by is {0}, actually it's '{1}'" \
                                .format(exp, registered_by))
                        results.setdefault('step3', []).append(False)
                else:
                    if output == exp:
                        logger.info("succeded to check registered_by is '{}'".format(exp))
                        results.setdefault('step3', []).append(True)
            else:
                logger.error("failed to get satellite {} info".format(check_type))
                results.setdefault('step3', []).append(False)

        # Case Result
        # notes = list()
        # if "libvirt-local" not in hypervisor_type and "vdsm" not in hypervisor_type:
        #     notes.append("Bug(step3): should show virt-who UUID under 'registered by' for hypervisor")
        #     notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1455041")
        # self.vw_case_result(results, notes)
        self.vw_case_result(results)

