# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # Case Header
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-134056")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        if "satellite62" in server_type or "libvirt-local" in mode or "vdsm" in mode:
            logger.warning("'hypervisors_async' capability only for remote hypervisors and candlepin > 2.0")
            self.vw_case_skip("skipped - this case is not avaialbe for %s and %s" % (mode, server_type))
        self.vw_env_init(mode)

        # Case Config
        results = dict()
        conf_name = "%s_config" % mode.lower()
        conf_file = "/etc/virt-who.d/%s.conf" % mode.lower()
        self.vw_option_enable("VIRTWHO_DEBUG", filename="/etc/sysconfig/virt-who")
        self.vw_option_update_value("VIRTWHO_DEBUG", '1', filename="/etc/sysconfig/virt-who")
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file)
        host_uuid = self.mode_host_uuid(mode)

        # Case Steps
        logger.info(">>>step1: Run virt-who servie to check hypervisor's facts")
        data, tty_output, rhsm_output = self.vw_start(exp_send=1)
        res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1)
        results.setdefault('step1', []).append(res)
        results.setdefault('step1', []).append(data['is_async'] == "hypervisors_async")
        results.setdefault('step1', []).append(data[owner][host_uuid].has_key('type'))
        results.setdefault('step1', []).append(data[owner][host_uuid].has_key('version'))
        results.setdefault('step1', []).append(data[owner][host_uuid].has_key('socket'))
        logger.info("hypervisor.type: %s " % data[owner][host_uuid]['type'])
        logger.info("cpu.cpu_socket(s): %s" % data[owner][host_uuid]['socket'])
        logger.info("hypervisor.version: %s" % data[owner][host_uuid]['version'])

        # Case Result
        self.vw_case_result(results)

if __name__ == "__main__":
    unittest.main()

#===changelog===
# - 2018/07/09 Eko<hsun@redhat.com>
# - update this case for the wrong check point
