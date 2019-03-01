# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-136636")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "esx" not in mode:
            self.vw_case_skip("skipped - this case is not avaialbe for %s" % mode)
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        host_uuid = self.mode_host_uuid(mode)
        host_hwuuid = self.mode_host_hwuuid(mode)
        host_name = self.mode_host_name(mode)
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)

        # Case Steps
        logger.info(">>>step1: run virt-who with filter_host_parents=* to check the domain_id")
        self.vw_option_add("filter_host_parents", "*", conf_file)
        data, tty_output, rhsm_output = self.vw_start()
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        domain_id = re.findall(r"Skipping host '%s' because its parent '(.*?)'" % host_hwuuid, rhsm_output)[-1]
        logger.info("Succeeded to find: %s:%s:%s" % (host_hwuuid, domain_id, host_uuid))
        self.vw_option_del("filter_host_parents", conf_file)

        steps = {'step2':'uuid', 'step3':'hostname', 'step4':'hwuuid'}
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who to with hypervisor_id=%s and set filter_host_parents" % (step, option))
            self.vw_option_add("hypervisor_id", option, conf_file)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
            else:
                hypervisorId = host_uuid
            wildcard = domain_id[:3] + '*' + domain_id[4:]
            sub_steps = {'step1':domain_id, 'step2': "*", 'step3': wildcard, 'step4': wildcard}
            for key, value in sorted(sub_steps.items(),key=lambda item:item[0]):
                if key == "step4":
                    logger.info("++++ Set filter_host_parents=%s and exclude_host_parents=* ++++" % value)
                    self.vw_option_add("exclude_host_parents", "*", conf_file)
                    self.vw_option_add("filter_host_parents", value, conf_file)
                else:
                    logger.info("++++ Set filter_host_parents=%s ++++" % value)
                    self.vw_option_add("filter_host_parents", value, conf_file)
                data, tty_output, rhsm_output = self.vw_start()
                res1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
                if key == "step2":
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=False)
                else:
                    res2 = self.vw_msg_search(str(data), hypervisorId, exp_exist=True)
                results.setdefault(step, []).append(res1)
                results.setdefault(step, []).append(res2)
                self.vw_option_del("exclude_host_parents", conf_file)
                self.vw_option_del("filter_host_parents", conf_file)
            self.vw_option_del("hypervisor_id", conf_file)
            if "satellite" in server_type:
                if "62" in server_type:
                    self.vw_web_host_delete(self.ssh_host(), hypervisorId, host_uuid)
                else:
                    self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
        if "stage" in server_type:
            self.stage_consumer_clean(self.ssh_host(), mode)

        # Case Result
        notes = list()
        notes.append("Bug: wildcard(*) is not valid for filter_host_parents and exclude_host_parents")
        notes.append("Bug: https://bugzilla.redhat.com/show_bug.cgi?id=1461272")
        self.vw_case_result(results, notes)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/07/16 Eko<hsun@redhat.com>
#- Case created to validate hypervisor_id and filter_host_parents with wildcard
# if filter_host_parents = *, no mapping info
# if filter_host_parents =  , no mapping info
# if filter_host_parents = domain_id, mapping info with domain_id
# if filter_host_parents = do*_id, no mapping info, it's a bug: https://bugzilla.redhat.com/show_bug.cgi?id=1461272
# if exclude_host_parents = *, all mapping info
# if exclude_host_parents =  , all mapping info
# if exclude_host_parents = domain_id , no domain_id mapping info
