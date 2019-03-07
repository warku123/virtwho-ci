from virtwho import *

class tc_ID0000_stop_guest(unittest.TestCase):
    def test_run(self):
        case_name = self.__class__.__name__
        logger.info("========== Begin of Running Test Case %s ==========" % case_name)

        logger.info(deploy.trigger.type)
        logger.info(deploy.trigger.level)
        logger.info(deploy.trigger.hypervisor_list)

        logger.info(deploy.jenkins.url)
        logger.info(deploy.jenkins.username)
        logger.info(deploy.jenkins.password)

        logger.info(deploy.docker.server)
        logger.info(deploy.docker.server_user)
        logger.info(deploy.docker.server_passwd)

        logger.info(deploy.beaker.client)
        logger.info(deploy.beaker.client_user)
        logger.info(deploy.beaker.client_passwd)

        logger.info(deploy.polarion.url)
        logger.info(deploy.polarion.username)
        logger.info(deploy.polarion.password)

        logger.info(deploy.nfs.server)
        logger.info(deploy.nfs.server_user)
        logger.info(deploy.nfs.server_passwd)

        logger.info(deploy.stage.server)
        logger.info(deploy.stage.esx_user)
        logger.info(deploy.stage.esx_passwd)

        logger.info(deploy.satellite.admin_user)
        logger.info(deploy.satellite.admin_passwd)
        logger.info(deploy.satellite.default_org)

        logger.info(deploy.vcenter.ip)
        logger.info(deploy.vcenter.master_user)
        logger.info(deploy.vcenter.master_passwd)

        logger.info(deploy.xen.master)
        logger.info(deploy.xen.master_user)
        logger.info(deploy.xen.master_passwd)

        logger.info(deploy.hyperv.master)
        logger.info(deploy.hyperv.master_user)
        logger.info(deploy.hyperv.master_passwd)

        logger.info(deploy.rhevm.rhevm_ip)
        logger.info(deploy.rhevm.rhevm_ssh_user)
        logger.info(deploy.rhevm.rhevm_ssh_passwd)
        logger.info(deploy.rhevm.rhevm_admin_user)
        logger.info(deploy.rhevm.rhevm_admin_passwd)
        logger.info(deploy.rhevm.master)
        logger.info(deploy.rhevm.slave)


        logger.info(deploy.vdsm.rhevm_ip)
        logger.info(deploy.vdsm.master)

        logger.info(config.virtwho.rhel_compose)

        logger.info(config.hypervisor.type)
        logger.info(config.hypervisor.server)

        logger.info(config.register.type)
        logger.info(config.register.server)

        logger.info(config.manifest.vdc)

        logger.info(config.vcenter.vcenter_ip)
        logger.info(config.vcenter.vcenter_ssh_user)

        logger.info(config.rhevm.rhevm_ip)
        logger.info(config.rhevm.rhevm_ssh_user)

        logger.info(config.vdsm.rhevm_ip)
        logger.info(config.vdsm.rhevm_ssh_user)

        logger.info(config.performance.vcenter_admin_user)
        logger.info(config.performance.esxi_hosts)


if __name__ == "__main__":
    unittest.main()

