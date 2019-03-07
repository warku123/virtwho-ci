from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.provision import Provision
# from virtwho.testcase import Testcase

class tc_ID0000_stop_guest(Provision):
    def test_run(self):
        case_name = self.__class__.__name__
                # ssh_esx_slave = {
                # "host":args_esx['esx_slave'],
                # "username":args_esx['esx_slave_user'],
                # "password":args_esx['esx_slave_passwd'],
                # }

        # ssh = {
                # "host":"10.73.131.237:53221",
                # "username":"root",
                # "password":"redhat"}
        # self.rhel_version(ssh)
        # self.provision_start()
        # self.provision_register_servers(queue="test")
 
        # self.provision_libvirt_local_host(queue="demo", compose_id="RHEL-7.6-20181010.0")
        # self.satellite_setup(sat_queue="queue", sat_type="satellite63-cdn-rhel7", sat_host="ent-02-vm-07.lab.eng.nay.redhat.com")

        # self.guest_rhevm_setup(mode_queue="demo", mode_type="rhevm")

        # register_servers = {
                # 'satellite65-repo-rhel7': 'ent-02-vm-03.lab.eng.nay.redhat.com',
                # }
        # virtwho_hosts = {
                # 'virtwho-host-rhevm-ip':'10.73.131.237:53224',
                # 'virtwho-host-esx-ip':'10.73.131.237:53221',
                # 'virtwho-host-libvirt-remote-ip':'10.73.131.237:53225',
                # }
        # guests = {
                # 'libvirt-remote-guest-ip': '10.66.146.13',
                # 'rhevm-guest-ip':'10.66.146.102',
                # 'esx-guest-ip': '10.73.131.171'
                # }
        # self.jenkins_job_scheduler(register_servers, virtwho_hosts, guests)

        # conf_hosts = self.docker_compose_setup("RHEL-8.0.0-20190213.0", ['esx','xen'])

        vcenter_ip = deploy.vcenter.ip
        vcenter_ssh_user = deploy.vcenter.ssh_user
        vcenter_ssh_passwd = deploy.vcenter.ssh_passwd
        vcenter_admin_user = deploy.vcenter.admin_user
        vcenter_admin_passwd = deploy.vcenter.admin_passwd
        guest_name = deploy.vcenter.guest_name
        ssh_vcenter = {"host":vcenter_ip,"username":vcenter_ssh_user,"password":vcenter_ssh_passwd}
        cert = self.vcenter_cert(vcenter_ip, vcenter_admin_user, vcenter_admin_passwd)
        host = self.vcenter_host_get(cert, ssh_vcenter, guest_name)
        self.vcenter_hostname_get(cert, ssh_vcenter, host)



if __name__ == "__main__":
    unittest.main()


