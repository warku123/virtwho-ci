# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        # case and env init
        case_name = os.path.basename(__file__)
        self.vw_case_info(case_name, "RHEL-150336")
        mode, host_ip, guest_ip = self.vw_env_info()
        server_type, server_ip, owner, env = self.vw_server_info()
        compose_id = self.get_exported_param("COMPOSE_ID")
        self.perf_env_init(mode)
        self.perf_vms_check(mode)

        # create virt-who config file
        conf_name = "%s_config" % mode
        conf_file = "/etc/virt-who.d/%s.conf" % mode
        self.vw_etc_d_mode_create(mode, conf_name, filename=conf_file, perf=True)

        """RUN virt-who oneshot mode
        :check oneshot time
        :check cpu/memory of virt-who process
        :check error message
        """
        logger.info("*********************************************")
        logger.info("Run virt-who with: oneshot(enable), debug(on)")
        logger.info("*********************************************")
        t1 = threading.Thread(target=self.perf_virtwho_start, kwargs = {"oneshot": True, "debug": True});
        t2 = threading.Thread(target=self.perf_cpu_check, args=(t1, ));
        t1.start()
        t2.start()
        t1.join()
        t2.join()
