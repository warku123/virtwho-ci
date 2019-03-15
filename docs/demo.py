from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.provision import Provision
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

        # cmd = "curl -s -i -X POST https://virtwho-qe-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/job/runtest-esx/buildWithParameters --user hsun:1638cb39d73ec1d61c700ff9b8f74887 -d RHEL_COMPOSE=RHEL-7.6-20181010.0 -d TRIGGER_TYPE=trigger-rhel -d TRIGGER_LEVEL=tier1 -d VIRTWHO_HOST_IP=10.73.131.237:53221 -d VIRTWHO_HOST_USER=root -d VIRTWHO_HOST_PASSWD=redhat -d HYPERVISOR_TYPE=esx -d HYPERVISOR_SERVER=10.73.131.219 -d HYPERVISOR_USERNAME=administrator@vsphere.local -d HYPERVISOR_PASSWORD=Welcome1! -d HYPERVISOR_SSH_USER=Administrator -d HYPERVISOR_SSH_PASSWD=Welcome1 -d GUEST_IP=10.73.131.213 -d GUEST_NAME=7.6_Server_x86_64 -d GUEST_USER=root -d GUEST_PASSWD=redhat -d REGISTER_TYPE=satellite65-repo-rhel7 -d REGISTER_SERVER=ent-02-vm-08.lab.eng.nay.redhat.com -d REGISTER_OWNER=Default_Organization -d REGISTER_ENV=Library -d REGISTER_ADMIN_USER=admin -d REGISTER_ADMIN_PASSWD=admin -d REGISTER_SSH_USER=root -d REGISTER_SSH_PASSWD=red2015"
        # is_created = ""
        # for i in range(3):
            # output = os.popen(cmd).readlines()
            # if 'Location:' in str(output):
                # is_created = 'yes'
                # break
            # logger.info(cmd)
            # logger.warning(output)
            # logger.warning("Failed to post data to create jenkinks job, try again...")
            # time.sleep(30)
        # if is_created != 'yes':
            # raise FailException("Failed to get jenkins job url")
        # job_url = self.jenkins_job_url(output)
        # logger.info(job_url)

        master = deploy.xen.master
        master_user = deploy.xen.master_user
        master_passwd = deploy.xen.master_passwd
        guest_name = deploy.xen.guest_name
        guest_user = deploy.xen.guest_user
        guest_passwd = deploy.xen.guest_passwd
        sr_name = deploy.xen.sr_name
        sr_server = deploy.xen.sr_server
        sr_path = deploy.xen.sr_path
        image_path = deploy.xen.image_path
        # set ssh env for xen master
        ssh_master ={"host":master,"username":master_user,"password":master_passwd}
        guest_ip = self.xen_guest_ip(ssh_master, guest_name)
        if not guest_ip:
            self.xen_host_ready(ssh_master, sr_name, sr_server, sr_path)
            guest_ip = self.xen_guest_add(ssh_master, guest_name, sr_name, image_path)
        logger.info("Successed to get xen guest ip: {0}".format(guest_ip))
        ssh_guest = {"host":guest_ip, "username":guest_user, "password":guest_passwd}
        self.system_init("ci-guest-xen", ssh_guest)


if __name__ == "__main__":
    unittest.main()


