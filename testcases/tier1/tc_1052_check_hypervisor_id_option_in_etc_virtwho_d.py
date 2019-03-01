# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-133705")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
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
        if "esx" in mode or "rhevm" in mode:
            steps = {'step1':'uuid', 'step2':'hostname', 'step3':'hwuuid'}
        else:
            steps = {'step1':'uuid', 'step2':'hostname'}

        # Case Steps
        for step, option in sorted(steps.items(),key=lambda item:item[0]):
            logger.info(">>>%s: run virt-who with hypervisor_id=%s" % (step, option))
            self.vw_option_add("hypervisor_id", option, filename=conf_file)
            data, tty_output, rhsm_output = self.vw_start()
            s1 = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
            results.setdefault(step, []).append(s1)
            if option == "hwuuid":
                hypervisorId = host_hwuuid
            elif option == "hostname":
                hypervisorId = host_name
            else:
                hypervisorId = host_uuid
            if data[owner].has_key(hypervisorId):
                logger.info("Succeeded to search hypervisorId:%s" % hypervisorId )
                results.setdefault(step, []).append(True)
            else:
                logger.error("Failed to search hypervisorId:%s" % hypervisorId )
                results.setdefault(step, []).append(False)
            self.vw_option_del("hypervisor_id", filename=conf_file)
            if "satellite" in server_type:
                if "62" in server_type:
                    self.vw_web_host_delete(self.ssh_host(), hypervisorId, host_uuid)
                else:
                    self.vw_web_host_delete(self.ssh_host(), host_name, host_uuid)
        if "stage" in server_type:
            self.stage_consumer_clean(self.ssh_host(), mode)

        # Case Result
        self.vw_case_result(results)
if __name__ == "__main__":
    unittest.main()

#===changelog===
#- 2018/06/13 Eko<hsun@redhat.com>
#- Case created to validate hypervisor_id option
