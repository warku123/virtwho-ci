# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133743')
        rhel_compose = self.get_exported_param("RHEL_COMPOSE")
        trigger_type = self.get_exported_param("TRIGGER_TYPE") 
        virtwho_host_ip = self.get_exported_param("VIRTWHO_HOST_IP") 
        virtwho_host_user = self.get_exported_param("VIRTWHO_HOST_USER") 
        virthwo_host_passwd = self.get_exported_param("VIRTWHO_HOST_PASSWD") 
        hypervisor1_type = self.get_exported_param("HYPERVISOR_01_TYPE") 
        hypervisor1_server = self.get_exported_param("HYPERVISOR_01_SERVE") 
        hypervisor1_username = self.get_exported_param("HYPERVISOR_01_USERNAME") 
        hypervisor1_password = self.get_exported_param("HYPERVISOR_01_PASSWORD") 
        hypervisor1_ssh_user = self.get_exported_param("HYPERVISOR_01_SSH_USER") 
        hypervisor1_ssh_passwd = self.get_exported_param("HYPERVISOR_01_SSH_PASSWD") 
        hypervisor1_guest_ip = self.get_exported_param("HYPERVISOR_01_GUEST_IP") 
        hypervisor1_guest_name = self.get_exported_param("HYPERVISOR_01_GUEST_NAME") 
        hypervisor1_guest_user = self.get_exported_param("HYPERVISOR_01_GUEST_USER") 
        hypervisor1_guest_passwd = self.get_exported_param("HYPERVISOR_01_GUEST_PASSWD") 
        hypervisor2_type = self.get_exported_param("HYPERVISOR_02_TYPE") 
        hypervisor2_sever = self.get_exported_param("HYPERVISOR_02_SERVER") 
        hypervisor2_username = self.get_exported_param("HYPERVISOR_02_USERNAME") 
        hypervisor2_password = self.get_exported_param("HYPERVISOR_02_PASSWORD") 
        hypervisor2_ssh_user = self.get_exported_param("HYPERVISOR_02_SSH_USER") 
        hypervisor2_ssh_passwd = self.get_exported_param("HYPERVISOR_02_SSH_PASSWD") 
        hypervisor2_guest_ip = self.get_exported_param("HYPERVISOR_02_GUEST_IP") 
        hypervisor2_guest_name = self.get_exported_param("HYPERVISOR_02_GUEST_NAME") 
        hypervisor2_guest_user = self.get_exported_param("HYPERVISOR_02_GUEST_USER") 
        hypervisor2_guest_passwd = self.get_exported_param("HYPERVISOR_02_GUEST_PASSWD") 
        register_type = self.get_exported_param("REGISTER_TYPE") 
        register_server = self.get_exported_param("REGISTER_SERVER") 
        register_owner = self.get_exported_param("REGISTER_OWNER") 
        register_env = self.get_exported_param("REGISTER_ENV") 
        register_admin_user = self.get_exported_param("REGISTER_ADMIN_USER") 
        register_admin_passwd = self.get_exported_param("REGISTER_ADMIN_PASSWD") 
        register_ssh_user = self.get_exported_param("REGISTER_SSH_USER") 
        register_ssh_passwd = self.get_exported_param("REGISTER_SSH_PASSWD") 

        logger.info(virtwho_host_ip)
        logger.info(hypervisor1_type)
        logger.info(hypervisor1_server)
        logger.info(hypervisor1_guest_ip)
        logger.info(hypervisor2_type)
        logger.info(hypervisor2_sever)
        logger.info(hypervisor2_guest_ip)
        logger.info(register_type)
        logger.info(register_server)

        results.setdefault('step1', []).append(True)

        # Case Result
        self.vw_case_result(results)
