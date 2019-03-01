from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.provision import Provision

class Testcase(Provision):
    #****************************************
    # ssh define
    #****************************************
    def testcase_register_config(self):
        register_type = config.register.type
        regist_server = config.register.server
        admin_user = config.register.admin_user
        admin_passwd = config.register.admin_passwd
        org = config.register.org
        env = config.register.env
        if "stage" in register_type:
            return (register_type, regist_server,
                    admin_user, admin_passwd, org, env)
        if "satellite" in register_type:
            ssh_user = config.register.admin_passwd
            ssh_passwd = config.register.admin_passwd
            return (register_type, regist_server,
                    admin_user, admin_passwd, ssh_user, ssh_passwd, org, env)


    def ssh_host(self):
        host_ip = self.get_exported_param("VIRTWHO_HOST_IP")
        ssh_host = {
                "host": host_ip,
                "username": args_global['host_user'],
                "password": args_global['host_passwd'],
                }
        return ssh_host

    def ssh_guest(self):
        guest_ip = self.get_exported_param("GUEST_IP")
        ssh_guest = {
                "host": guest_ip,
                "username": args_global['guest_user'],
                "password": args_global['guest_passwd'],
                }
        return ssh_guest

    def ssh_vcenter_env(self):
        ssh_vcenter = {
                "host": args_esx['vcenter'],
                "username": args_esx['win_user'],
                "password": args_esx['win_passwd'],
                }
        ssh_esx_master = {
                "host": args_esx['esx_master'],
                "username": args_esx['esx_master_user'],
                "password": args_esx['esx_master_passwd'],
                }
        ssh_esx_slave = {
                "host": args_esx['esx_slave'],
                "username": args_esx['esx_slave_user'],
                "password": args_esx['esx_slave_passwd'],
                }
        return ssh_vcenter, ssh_esx_master, ssh_esx_slave

    def ssh_xen_env(self):
        ssh_xen_master = {
                "host": args_xen['master'],
                "username": args_xen['master_user'],
                "password": args_xen['master_passwd'],
                }
        ssh_xen_slave = {
                "host": args_xen['slave'],
                "username": args_xen['slave_user'],
                "password": args_xen['slave_passwd'],
                }
        return ssh_xen_master, ssh_xen_slave

    def ssh_hyperv_env(self):
        ssh_hyperv_master = {
                "host": args_hyperv['master'],
                "username": args_hyperv['master_user'],
                "password": args_hyperv['master_passwd'],
                }
        ssh_hyperv_slave = {
                "host": args_hyperv['slave'],
                "username": args_hyperv['slave_user'],
                "password": args_hyperv['slave_passwd'],
                }
        return ssh_hyperv_master, ssh_hyperv_slave

    def ssh_rhevm_env(self, mode):
        if mode == "rhevm":
            args_rhevm = args_rhevm_mode_rhv4
            ssh_rhevm = {
                    "host":args_rhevm['server'],
                    "username":args_rhevm['server_user'],
                    "password":args_rhevm['server_passwd']}
            ssh_vdsm_master = {
                    "host":args_rhevm['vdsm_master'],
                    "username":args_rhevm['vdsm_master_user'],
                    "password":args_rhevm['vdsm_master_passwd']}
            ssh_vdsm_slave = {
                    "host":args_rhevm['vdsm_slave'],
                    "username":args_rhevm['vdsm_slave_user'],
                    "password":args_rhevm['vdsm_slave_passwd']}
        elif mode == "vdsm":
            ssh_vdsm_master = {
                    "host":self.get_exported_param("VIRTWHO_HOST_IP"),
                    "username":args_global['host_user'],
                    "password":args_global['host_passwd']}
            rhel_ver = self.rhel_version(ssh_vdsm_master)
            if rhel_ver == "6":
                args_rhevm = args_vdsm_mode_rhv3
            elif rhel_ver == "7":
                args_rhevm = args_vdsm_mode_rhv4
            ssh_rhevm = {
                    "host":args_rhevm['server'],
                    "username":args_rhevm['server_user'],
                    "password":args_rhevm['server_passwd']}            
            ssh_vdsm_slave = dict()
        else:
            raise FailException("Unsupported mode for ssh_rhevm_env fucntion")
        return args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave

    def ssh_libvirt_env(self, mode):
        if mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = {
                    "host":args_libvirt['remote_server'],
                    "username":args_global['host_user'],
                    "password":args_global['host_passwd']}
        elif mode == "libvirt-local":
            ssh_libvirt = {
                    "host":self.get_exported_param("VIRTWHO_HOST_IP"),
                    "username":args_global['host_user'],
                    "password":args_global['host_passwd']}
        else:
            raise FailException("Unsupported mode for ssh_libvirt_env fucntion")
        return ssh_libvirt

    def ssh_extra_env(self, mode):
        if mode == "xen":
            server = args_xen['extra']
            username = args_xen['extra_user']
            password = args_xen['extra_passwd']
        elif mode == "libvirt-remote" or mode == "libvirt":
            server = args_libvirt['extra_remote_server']
            username = args_global['host_user']
            password = args_global['host_passwd']
        else:
            raise FailException("Only support xen and libvirt-remote as extral mode")
        ssh_extra = {"host": server, "username": username, "password": password}
        return ssh_extra, server, username, password

    #******************************************
    # guest add/delete/start/stop/pause/resume
    #******************************************
    def mode_guest_add(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            guest_ip = self.vcenter_guest_add(guest_name, ssh_esx_master, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            guest_ip = self.xen_guest_add(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            guest_ip = self.hyperv_guest_add(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            guest_ip = self.rhevm_guest_add(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            guest_ip = self.rhevm_guest_add(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            guest_ip = self.libvirt_guest_add(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            guest_ip = self.libvirt_guest_add(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to add guest for mode: %s" % mode)
        logger.info("Successed to add guest for mode %s, guest_ip is: %s" % (mode, guest_ip))
        self.set_exported_param("GUEST_IP", guest_ip)

    def mode_guest_delete(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            self.vcenter_guest_delete(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            self.xen_guest_delete(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            self.hyperv_guest_delete(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_delete(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_delete(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_delete(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_delete(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to delete guest for mode: %s" % mode)
        logger.info("Successed to delete guest for mode %s" % mode)

    def mode_guest_start(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            guest_ip = self.vcenter_guest_start(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            guest_ip = self.xen_guest_start(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            guest_ip = self.hyperv_guest_start(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            guest_ip = self.rhevm_guest_start(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            guest_ip = self.rhevm_guest_start(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            guest_ip = self.libvirt_guest_start(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            guest_ip = self.libvirt_guest_start(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to start guest for mode: %s" % mode)
        logger.info("Successed to start guest for mode %s, guest ip: %s" % (mode, guest_ip))
        guest_ip_old = self.get_exported_param("GUEST_IP")
        if guest_ip_old == guest_ip:
            logger.info("guest_ip(%s) is not changed after guest start" % (guest_ip_old))
        else:
            logger.warning("guest_ip(%s) is changed to %s after guest start" % (guest_ip_old, guest_ip))
            self.set_exported_param("GUEST_IP", guest_ip)

    def mode_guest_stop(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            self.vcenter_guest_stop(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            self.xen_guest_stop(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            self.hyperv_guest_stop(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_stop(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_stop(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_stop(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_stop(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to stop guest for mode: %s" % mode)
        logger.info("Successed to stop guest for mode %s" % mode)

    def mode_guest_suspend(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            self.vcenter_guest_suspend(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            self.xen_guest_suspend(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            self.hyperv_guest_suspend(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_suspend(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_suspend(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_suspend(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_suspend(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to suspend guest for mode: %s" % mode)
        logger.info("Successed to suspend guest for mode %s" % mode)

    def mode_guest_resume(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            self.vcenter_guest_resume(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            self.xen_guest_resume(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            self.hyperv_guest_resume(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_resume(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            self.rhevm_guest_resume(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_resume(guest_name, ssh_libvirt, args_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            self.libvirt_guest_resume(guest_name, ssh_libvirt, args_libvirt)
        else:
            raise FailException("Unsupported to resume guest for mode: %s" % mode)
        logger.info("Successed to resume guest for mode %s" % mode)

    def mode_guest_uuid(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            guest_name = args_esx['guest_name']
            uuid = self.vcenter_guest_uuid(guest_name, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            guest_name = args_xen['guest_name']
            uuid = self.xen_guest_uuid(guest_name, ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            guest_name = args_hyperv['guest_name']
            uuid = self.hyperv_guest_uuid(guest_name, ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            uuid = self.rhevm_guest_uuid(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            guest_name = args_rhevm['guest_name']
            uuid = self.rhevm_guest_uuid(guest_name, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            uuid = self.libvirt_guest_uuid(guest_name, ssh_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            guest_name =  args_libvirt['guest_name']
            uuid = self.libvirt_guest_uuid(guest_name, ssh_libvirt)
        else:
            uuid = "unsupported mode"
        return uuid

    def mode_host_uuid(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            uuid = self.vcenter_host_uuid(ssh_esx_master, ssh_vcenter)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            uuid = self.xen_host_uuid(ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            uuid = self.hyperv_host_uuid(ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            hostname = self.get_hostname(ssh_vdsm_master)
            uuid = self.rhevm_host_uuid(hostname, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            hostname = self.get_hostname(ssh_vdsm_master)
            uuid = self.rhevm_host_uuid(hostname, ssh_rhevm, args_rhevm)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            uuid = self.libvirt_host_uuid(ssh_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            uuid = self.libvirt_host_uuid(ssh_libvirt)
        else:
            uuid = "unsupported mode"
        return uuid

    def mode_host_hwuuid(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            hwuuid = self.vcenter_host_hwuuid(ssh_esx_master, ssh_vcenter)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            hostname = self.get_hostname(ssh_vdsm_master)
            hwuuid = self.rhevm_host_hwuuid(hostname, ssh_rhevm, args_rhevm)
        else:
            hwuuid = "unsupported mode"
        return hwuuid

    def mode_host_name(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            name = self.get_hostname(ssh_esx_master)
        elif mode == "xen":
            ssh_xen_master, ssh_xen_slave = self.ssh_xen_env()
            name = self.get_hostname(ssh_xen_master)
        elif mode == "hyperv":
            ssh_hyperv_master, ssh_hyperv_slave = self.ssh_hyperv_env()
            name = self.hyperv_host_name(ssh_hyperv_master)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            hostname = self.get_hostname(ssh_vdsm_master)
            name = self.rhevm_host_display_name(hostname, ssh_rhevm, args_rhevm)
        elif mode == "vdsm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            name = self.get_hostname(ssh_vdsm_master)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            name = self.get_hostname(ssh_libvirt)
        elif mode == "libvirt-local":
            ssh_libvirt = self.ssh_libvirt_env(mode)
            name = self.get_hostname(ssh_libvirt)
        else:
            name = "unsupported mode"
        return name

    def mode_host_add(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            self.vcenter_host_ready(ssh_esx_master, ssh_vcenter)
            self.vcenter_host_ready(ssh_esx_slave, ssh_vcenter)
            guest_name = args_esx['guest_name']
            guest_ip = self.vcenter_guest_add(guest_name, ssh_esx_master, ssh_vcenter)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            self.rhevm_host_ready(ssh_vdsm_master, ssh_rhevm, args_rhevm)
            self.rhevm_host_ready(ssh_vdsm_slave, ssh_rhevm, args_rhevm)
            guest_name = args_rhevm['guest_name']
            guest_ip = self.rhevm_guest_add(guest_name, ssh_vdsm_master, ssh_rhevm, args_rhevm)
        else:
            raise FailException("Unsupported to add host for mode: %s" % mode)
        logger.info("Successed to add host for mode %s" % mode)
        self.set_exported_param("GUEST_IP", guest_ip)

    def mode_host_delete(self, mode):
        if mode == "esx":
            ssh_vcenter, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
            self.vcenter_host_delete(ssh_esx_master, ssh_vcenter)
            self.vcenter_host_delete(ssh_esx_slave, ssh_vcenter)
        elif mode == "rhevm":
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            self.rhevm_hosts_all_clean(ssh_rhevm, args_rhevm)
        else:
            raise FailException("Unsupported to delete host for mode: %s" % mode)
        logger.info("Successed to delete host for mode %s" % mode)


    def hypervisors_ssh(self, mode):
        if mode == "esx":
            ssh_args, ssh_esx_master, ssh_esx_slave = self.ssh_vcenter_env()
        elif mode == "xen":
            ssh_args, ssh_xen_slave = self.ssh_xen_env()
        elif mode == "hyperv":
            ssh_args, ssh_hyperv_slave = self.ssh_hyperv_env()
        elif mode == "rhevm":
            args_rhevm, ssh_args, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
        elif mode == "vdsm":
            args_rhevm, ssh_args, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
        elif mode == "libvirt-remote" or mode == "libvirt":
            ssh_args = self.ssh_libvirt_env(mode)
        elif mode == "libvirt-local":
            ssh_args = self.ssh_libvirt_env(mode)
        return ssh_args

    def hypervisors_access(self, mode, connected):
        ssh_hypervisor = self.hypervisors_ssh(mode)
        ssh_host = self.ssh_host()
        host = ssh_host['host']
        if ":" in host:
            var = host.split(':')
            host = var[0]
            port = int(var[1])
        if mode == "rhevm" or mode == "libvirt-remote" or mode == "xen":
            if connected == "no":
                cmd = "iptables -I INPUT -s %s -j DROP" % host
            if connected == "yes":
                cmd = "iptables -D INPUT -s %s -j DROP" % host
            ret, output = self.runcmd(cmd, ssh_hypervisor, desc="linux iptables set")
        if mode == "esx" or mode == "hyperv":
            if connected == "no":
                cmd1 = "NetSh Advfirewall set allprofiles state on"
                cmd2 = r'netsh advfirewall firewall add rule name="BLOCKED IP" interface=any dir=in action=block remoteip=%s' % host
            if connected == "yes":
                cmd1 = r'netsh advfirewall firewall delete rule name="BLOCKED IP" remoteip=%s' % host
                cmd2 = "NetSh Advfirewall set allprofiles state off"
            ret, output = self.runcmd(cmd1, ssh_hypervisor, desc="windows firewall turn")
            ret, output = self.runcmd(cmd2, ssh_hypervisor, desc="windows firewall rule")

    #******************************************
    # virt-who config function
    #******************************************
    def vw_pkg_check(self):
        cmd = "rpm -qa virt-who"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who package check")
        pkg = ""
        if ret == 0 and output is not None and output != "":
            pkg = output.strip()+".rpm"
            logger.info("Succeeded to check virtwho pkg: %s" % pkg)
        return pkg

    def vw_pkg_install(self):
        cmd = "yum install -y virt-who"
        ret, output = self.runcmd(
            cmd, self.ssh_host(), desc="virt-who package install")
        if self.vw_pkg_check() == "":
            logger.error("Failed to install virt-who package")
            return False
        else:
            logger.info("Succeeded to install virt-who package")
            return True

    def vw_pkg_uninstall(self):
        cmd = "rpm -e virt-who"
        ret, output = self.runcmd(
            cmd, self.ssh_host(), desc="virt-who package uninstall")
        if self.vw_pkg_check() != "":
            logger.error("Failed to uninstall virt-who package")
            return False
        else:
            logger.info("Succeeded to uninstall virt-who package")
            return True

    def vw_pkg_info(self):
        cmd = "rpm -qi virt-who"
        _, stdout = self.runcmd(
            cmd, self.ssh_host(), desc="get virt-who package info")
        dic = stdout.split("\n")
        info = {}
        for d in dic:
            try:
                kv_entry = d.split(': ')
                k = kv_entry[0].strip()
                v = kv_entry[1].strip()
                info.update({k: v})
            except:
                pass
        return info

    def vw_case_info(self, case_name, polarion_id):
        polarion_baseurl = "https://polarion.engineering.redhat.com/polarion/redirect/project"
        polarion_workitem = "%s/RedHatEnterpriseLinux7/workitem?id=%s" % (polarion_baseurl, polarion_id)
        log_prex = "************************"
        logger.info(log_prex)
        logger.info(case_name)
        logger.info(polarion_workitem)
        logger.info(log_prex)
        logfile = self.get_exported_param("LOGFILE")
        if os.path.exists(logfile):
            fd = open(logfile, 'a')
            fd.write(log_prex+'\n')
            fd.write(case_name+'\n')
            fd.write(polarion_workitem+'\n')
            fd.write(log_prex+'\n')
            fd.close()

    def vw_case_skip(self, skip_reason):
        try:
            self.skipTest(skip_reason)
        except Exception, SkipTest:
            logger.info(str(SkipTest))
            raise SkipTest
        finally:
            logger.info("Successed to skip case")

    def vw_case_result(self, results, notes=None):
        for key, value in results.items():
            if False in value:
                logger.error('Failed step: %s' % key)
                print 'Failed step: %s' % key
        if notes is not None:
            for msg in notes:
                logger.warning(msg)
                print msg
        if any(False in res for res in results.values()):
            raise FailException("Failed to run case, please check the failed steps")
        else:
            logger.info("++++++++++++")
            logger.info("Successed to run case, all steps passed")
            logger.info("++++++++++++")

    def vw_env_info(self):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        host_ip = self.get_exported_param("VIRTWHO_HOST_IP")
        guest_ip = self.get_exported_param("GUEST_IP")
        return mode, host_ip, guest_ip

    def vw_env_init(self, mode):
        server_type, server_ip, owner, env = self.vw_server_info()
        if "vdsm" in mode or "rhevm" in mode:
            args_rhevm, ssh_rhevm, ssh_vdsm_master, ssh_vdsm_slave = self.ssh_rhevm_env(mode)
            cmd = "ovirt-aaa-jdbc-tool user unlock admin"
            ret, output = self.runcmd(cmd, ssh_rhevm, desc="rhevm admin unlock")
            logger.info("Finished to unlock rhevm admin")
        if self.system_isregister(self.ssh_host(), server_type, server_ip, mode) is False:
            self.vw_sub_register(self.ssh_host())
        if self.system_isregister(self.ssh_guest(), server_type, server_ip, mode) is False:
            self.vw_sub_register(self.ssh_guest())
        if self.system_sku_unattach(self.ssh_host()) is False:
            self.vw_sub_register(self.ssh_host())
        if self.system_sku_unattach(self.ssh_guest()) is False:
            self.vw_sub_register(self.ssh_guest())
        self.vw_etc_conf_disable_all()
        self.vw_etc_sys_disable_all()
        self.vw_etc_d_delete_all()

    def vw_server_info(self):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type = self.get_exported_param("SERVER_TYPE")
        server_ip = self.get_exported_param("SERVER_IP")
        if "satellite" in server_type:
            owner = args_satellite['default_owner']
            env = args_satellite['env']
        elif "stage" in server_type:
            stage_user, stage_passwd, owner, env = self.stage_account_get(mode)
        else:
            raise FailException("Unsupported server type")
        return server_type, server_ip, owner, env

    def vw_hypervisor_info(self, mode, perf=False):
        if mode == "esx" and perf is False:
            server = args_esx['vcenter']
            username = args_esx['vcenter_user']
            password = args_esx['vcenter_passwd']
        elif mode == "esx" and perf is True:
            server = args_perf_esx['vcenter']
            username = args_perf_esx['vcenter_user']
            password = args_perf_esx['vcenter_passwd']
        elif mode == "xen":
            server = args_xen['master']
            username = args_xen['master_user']
            password = args_xen['master_passwd']
        elif mode == "hyperv":
            server = args_hyperv['master']
            username = args_hyperv['master_user']
            password = args_hyperv['master_passwd']
        elif mode == "rhevm":
            server = args_rhevm_mode_rhv4['web_server']
            username = args_rhevm_mode_rhv4['web_user']
            password = args_rhevm_mode_rhv4['web_passwd']
        elif mode == "libvirt-remote" or mode == "libvirt":
            server = args_libvirt['remote_server']
            username = args_global['host_user']
            password = args_global['host_passwd']
        elif mode == "vdsm" or mode == "libvirt-local":
            server = self.get_exported_param("VIRTWHO_HOST_IP")
            username = args_global['host_user']
            password = args_global['host_passwd']
        return server, username, password

    def vw_hypervisor_event(self, event):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        if event == "guest_suspend":
            self.mode_guest_suspend(mode)
        elif event == "guest_resume":
            self.mode_guest_resume(mode)
        elif event == "guest_stop":
            self.mode_guest_stop(mode)
        elif event == "guest_start":
            self.mode_guest_start(mode)
        elif event == "guest_delete":
            self.mode_guest_delete(mode)
        elif event == "guest_add":
            self.mode_guest_add(mode)
        elif event == "host_delete":
            self.mode_host_delete(mode)
        elif event == "host_add":
            self.mode_host_add(mode)
        else:
            raise FailException("Unsupported hypervisor event")

    def vw_extra_mode_info(self, mode):
        ssh_extra, server, username, password = self.ssh_extra_env(mode)
        if "xen" == mode:
            host_uuid = self.xen_host_uuid(ssh_extra)
            guest_uuid = self.xen_guest_uuid(args_xen['guest_name'], ssh_extra)
            host_name = self.get_hostname(ssh_extra)
        elif "libvirt-remote" == mode or "libvirt" == mode:
            host_uuid = self.libvirt_host_uuid(ssh_extra)
            guest_uuid = self.libvirt_guest_uuid(args_libvirt['guest_name'], ssh_extra)
            host_name = self.get_hostname(ssh_extra)
        else:
            raise FailException("Only support xen and libvirt-remote as extral mode")
        return host_name, host_uuid, guest_uuid

    def vw_extra_conf_in_sys(self, mode):
        '''Some cases need two config modes in /etc/sysconfig/virt-who, use xen as the extra config'''
        ssh_extra, server, username, password = self.ssh_extra_env(mode)
        server_type, server_ip, owner, env = self.vw_server_info()
        if mode == "libvirt-remote" or mode == "libvirt":
            mode = "LIBVIRT"
            self.ssh_no_passwd_access(self.ssh_host(), ssh_extra)
        filename = "/etc/sysconfig/virt-who"
        mode = mode.upper()
        op_1 = '-e "s|.*%s=.*|VIRTWHO_%s=1|g"' % (mode, mode )
        op_2 = '-e "s|.*%s_OWNER=.*|VIRTWHO_%s_OWNER=%s|g"' % (mode, mode, owner)
        op_3 = '-e "s|.*%s_ENV=.*|VIRTWHO_%s_ENV=%s|g"' % (mode, mode, env) 
        op_4 = '-e "s|.*%s_SERVER=.*|VIRTWHO_%s_SERVER=%s|g"' % (mode, mode, server)
        op_5 = '-e "s|.*%s_USERNAME=.*|VIRTWHO_%s_USERNAME=%s|g"' % (mode, mode, username) 
        op_6 = '-e "s|.*%s_PASSWORD=.*|VIRTWHO_%s_PASSWORD=%s|g"' % (mode, mode, password)
        cmd = 'sed -i %s %s %s %s %s %s %s' % (op_1, op_2, op_3, op_4, op_5, op_6, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who enable mode")
        if ret != 0:
            raise FailException("Failed to enable extra mode(%s) in /etc/sysconfig/virt-who" % mode)
        logger.info("Successed to enable extra mode(%s) in /etc/sysconfig/virt-who" % mode)

    def vw_extra_conf_in_d(self, mode, filename):
        '''Some cases need two config files in /etc/virt-who.d/, use xen as the extra config'''
        ssh_extra, server, username, password = self.ssh_extra_env(mode)
        server_type, server_ip, owner, env = self.vw_server_info()
        if mode == "libvirt-remote" or mode == "libvirt":
            mode = "libvirt"
            self.ssh_no_passwd_access(self.ssh_host(), ssh_extra)
        conf_name = "extra_%s" % mode
        cmd = ('cat <<EOF > %s\n'
                '[%s]\n'
                'type=%s\n'
                'server=%s\n'
                'username=%s\n'
                'password=%s\n'
                'owner=%s\n'
                'env=%s\n'
                'EOF'
              ) % (filename, conf_name, mode.lower(), server, username, password, owner, env)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who config file create")
        if ret != 0:
            raise FailException("Failed to create extra mode(%s) file in /etc/virt-who.d/" % mode)
        logger.info("Successed to create extra mode(%s) file in /etc/virt-who.d/" % mode)

    def vw_etc_conf_disable_all(self):
        op_1 = '-e "/;/d"'
        op_2 = '-e "s|^[^#]|#&|g"'
        cmd = 'sed -i %s %s /etc/virt-who.conf' % (op_1, op_2)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who disable all options virt-who.conf")
        if ret != 0:
            raise FailException("Failed to disable all options in /etc/virt-who.conf")
        else:
            logger.info("Successed to disable all options in /etc/virt-who.conf")

    def vw_etc_sys_disable_all(self):
        op_1 = '-e "s|^[^#]|#&|g"'
        cmd = 'sed -i %s /etc/sysconfig/virt-who' % op_1
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who disable all sysconfig options")
        if ret != 0:
            raise FailException("Failed to disable all modes in /etc/sysconfig/virt-who")
        else:
            logger.info("Successed to disable all options in /etc/sysconfig/virt-who")

    def vw_etc_sys_mode_enable(self, mode):
        filename = "/etc/sysconfig/virt-who"
        if mode == "libvirt-local":
            logger.info("Local libvirt mode is default when using vw_env_init()")
        elif mode == "vdsm":
            cmd = 'sed -i -e "s|.*VIRTWHO_VDSM=.*|VIRTWHO_VDSM=1|g" %s' % filename
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who vdsm mode enable")
        else:
            server_type, server_ip, owner, env = self.vw_server_info()
            server, username, password = self.vw_hypervisor_info(mode)
            if mode == "libvirt-remote" or mode == "libvirt":
                mode = "LIBVIRT"
            mode = mode.upper()
            op_1 = '-e "s|.*%s=.*|VIRTWHO_%s=1|g"' % (mode, mode )
            op_2 = '-e "s|.*%s_OWNER=.*|VIRTWHO_%s_OWNER=%s|g"' % (mode, mode, owner)
            op_3 = '-e "s|.*%s_ENV=.*|VIRTWHO_%s_ENV=%s|g"' % (mode, mode, env) 
            op_4 = '-e "s|.*%s_SERVER=.*|VIRTWHO_%s_SERVER=%s|g"' % (mode, mode, server)
            op_5 = '-e "s|.*%s_USERNAME=.*|VIRTWHO_%s_USERNAME=%s|g"' % (mode, mode, username) 
            op_6 = '-e "s|.*%s_PASSWORD=.*|VIRTWHO_%s_PASSWORD=%s|g"' % (mode, mode, password)
            cmd = 'sed -i %s %s %s %s %s %s %s' % (op_1, op_2, op_3, op_4, op_5, op_6, filename)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who enable mode")
            if ret != 0:
                raise FailException("Failed to enable mode %s in /etc/sysconfig/virt-who" % mode)
            else:
                logger.info("Successed to enable mode %s in /etc/sysconfig/virt-who" % mode)

    def vw_etc_d_delete_all(self):
        cmd = "rm -rf /etc/virt-who.d/*; rm -f /etc/virt-who.d/.*swp"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who delete all files in virt-who.d")
        if ret != 0:
            raise FailException("Failed to delete all files in /etc/virt-who.d/")
        else:
            logger.info("Successed to delete all files in /etc/virt-who.d/")

    def vw_etc_d_mode_create(self, mode, config_name, filename, perf=False):
        if mode == "libvirt-local":
            logger.info("Local libvirt mode is default when using vw_env_init()")
        elif mode == "vdsm":
            cmd = "echo -e '[%s]\ntype=%s' > %s" % (config_name, mode, filename)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who vdsm mode enable")
        else:
            server_type, server_ip, owner, env = self.vw_server_info()
            server, username, password = self.vw_hypervisor_info(mode, perf)
            if mode == "libvirt-remote" or mode == "libvirt":
                mode = "libvirt"
            cmd = ('cat <<EOF > %s\n'
                    '[%s]\n'
                    'type=%s\n'
                    'server=%s\n'
                    'username=%s\n'
                    'password=%s\n'
                    'owner=%s\n'
                    'env=%s\n'
                    'EOF'
                  ) % (filename, config_name, mode.lower(), server, username, password, owner, env)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who config file create")
            if ret != 0:
                raise FailException("Failed to create config file %s" % filename)
            else:
                logger.info("Successed to create config file %s" % filename)

    def vw_fake_json_create(self, cli, json_file):
        self.vw_stop()
        cmd ="%s -p -d > %s" % (cli, json_file)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="json data created")
        ret, output = self.runcmd("cat %s" % json_file, self.ssh_host(), desc="cat json data")
        logger.info(output)
        if "guestId" not in output:
            raise FailException("Failed to create json data: %s" % json_file)
        logger.info("Successed to create json data: %s" % json_file)

    def vw_fake_conf_create(self, conf_file, json_file, is_hypervisor=True):
        server_type, server_ip, owner, env = self.vw_server_info()
        cmd = ('cat <<EOF > %s\n'
                '[fake]\n'
                'type=fake\n'
                'file=%s\n'
                'is_hypervisor=%s\n'
                'owner=%s\n'
                'env=%s\n'
                'EOF'
              ) % (conf_file, json_file, is_hypervisor, owner, env)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who fake file create")
        ret, output = self.runcmd("ls %s" % conf_file, self.ssh_host(), desc="virt-who fake file check")
        if ret != 0 :
            raise FailException("Failed to create fake config file: %s" % conf_file)
        logger.info("Successed to create fake config file: %s" % conf_file)

    def vw_option_update_name(self, option, rename, filename):
        option = self.shell_escape_char(option)
        rename = self.shell_escape_char(rename)
        cmd = 'sed -i "s|^%s|%s|g" %s' % (option, rename, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who update option name")
        if ret == 0:
            logger.info("Successed to update option name %s to %s" % (option, rename))
        else:
            raise FailException("Failed to update option name %s to %s" % (option, rename))

    def vw_option_update_value(self, option, value, filename):
        option = self.shell_escape_char(option)
        value = self.shell_escape_char(value)
        cmd = 'sed -i "s|^%s.*|%s=%s|g" %s' % (option, option, value, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who update option value")
        if ret == 0:
            logger.info("Successed to set option %s value to %s" % (option, value))
        else:
            raise FailException("Failed to set option %s value to %s" % (option, value))

    def vw_option_enable(self, option, filename):
        option = self.shell_escape_char(option)
        op_1 = '-e "s|^#%s$|%s|g"' % (option, option)
        op_2 = '-e "s|^#%s=|%s=|g"' % (option, option)
        op_3 = '-e "s|^# %s$|%s|g"' % (option, option)
        op_4 = '-e "s|^# %s=|%s=|g"' % (option, option)
        cmd = 'sed -i %s %s %s %s %s' % (op_1, op_2, op_3, op_4, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who enable mode")
        if ret == 0:
            logger.info("Successed to enable option %s" % option)
        else:
            raise FailException("Failed to enable option %s" % option)

    def vw_option_disable(self, option, filename):
        option = self.shell_escape_char(option)
        cmd = 'sed -i "s|^%s|#%s|g" %s' % (option, option, filename) 
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who disable option")
        if ret == 0:
            logger.info("Successed to disable option %s" % option)
        else:
            raise FailException("Failed to disable option %s" % option)

    def vw_option_add(self, option, value, filename):
        cmd = 'echo "%s=%s" >> %s' % (option, value, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who add option")
        if ret == 0:
            logger.info("Successed to add option %s=%s" % (option, value))
        else:
            raise FailException("Failed to add option %s=%s" % (option, value))

    def vw_option_del(self, option, filename):
        option = self.shell_escape_char(option)
        cmd = 'sed -i "/^%s/d" %s; sed -i "/^#%s/d" %s' % (option, filename, option, filename)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who delete option")
        if ret == 0:
            logger.info("Successed to delete option %s" % option)
        else:
            raise FailException("Failed to delete option %s" % option)

    def vw_option_get(self, option, filename):
        cmd = "grep -v '^#' %s |grep ^%s" % (filename, option)
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who return option's value")
        if ret == 0 and option in output:
            value = output.split('=')[1].strip()
            return value
        else:
            raise FailException("No this option or option is not enabled")

    def vw_cli_base(self, mode):
        server_type, server_ip, owner, env = self.vw_server_info()
        server, username, password = self.vw_hypervisor_info(mode)
        if mode == "libvirt-remote":
            mode = "libvirt"
        if mode == "libvirt-local" or mode == "" or mode is None: 
            cmd = "virt-who "
        elif mode == "vdsm":
            cmd = "virt-who --vdsm "
        else:
            op_1 = "--%s" % (mode)
            op_2 = "--%s-owner=%s" % (mode, owner)
            op_3 = "--%s-env=%s" % (mode, env)
            op_4 = "--%s-server=%s" % (mode, server)
            op_5 = "--%s-username=%s" % (mode, username)
            op_6 = "--%s-password=%s" % (mode, password)
            cmd = "virt-who %s %s %s %s %s %s " % (op_1, op_2, op_3, op_4, op_5, op_6)
        return cmd

    def vw_cli_base_update(self, cmd, pattern, new_str):
        pattern = r"%s?(?= )" % pattern
        cmd = re.sub(pattern, new_str, cmd)
        return cmd

    def vw_service_status(self):
        ret, output = self.run_service(self.ssh_host(), "virt-who", "status")
        if output is not None and output != "":
            if "is stopped" in output or "Active: inactive (dead)" in output:
                status = "stopped"
            elif "is running" in output or "Active: active (running)" in output:
                status = "running"
            else:
                status = "unknown"
            logger.info("virt-who status is: %s" % status)
            return status
        else:
            raise FailException("Failed to check virt-who status")

    def vw_async_log(self, data, rhsm_output):
        orgs = re.findall(r"Host-to-guest mapping being sent to '(.*?)'", rhsm_output)
        if len(orgs) > 0: 
            data['orgs'] = orgs
            org_data = dict()
            for org in orgs:
                key = "Host-to-guest mapping being sent to '%s'" % org
                rex = re.compile(r'(?<=: ){.*?}\n+(?=201|$)', re.S)
                mapping_info = rex.findall(rhsm_output)[-1]
                try:
                    mapping_info = json.loads(mapping_info.replace('\n', ''), strict=False)
                except:
                    logger.warning("Failed to run json.loads for rhsm.log")
                    return data
                hypervisors = mapping_info['hypervisors']
                org_data["hypervisor_num"] = len(hypervisors)
                for item in hypervisors:
                    hypervisorId =  item['hypervisorId']['hypervisorId']
                    if item.has_key('name'):
                        hypervisor_name =  item['name']
                    else:
                        hypervisor_name = ""
                    facts = dict()
                    facts['name'] = hypervisor_name
                    facts['type'] = item['facts']['hypervisor.type']
                    facts['version'] = item['facts']['hypervisor.version']
                    facts['socket'] = item['facts']['cpu.cpu_socket(s)']
                    guests = list()
                    for guest in item['guestIds']:
                        guestId = guest['guestId']
                        guests.append(guestId)
                        attr = dict()
                        attr['guest_hypervisor'] = hypervisorId
                        attr['state'] = guest['state']
                        attr['active'] = guest['attributes']['active']
                        attr['type'] = guest['attributes']['virtWhoType']
                        org_data[guestId] = attr
                    facts['guests'] = guests
                    org_data[hypervisorId] = facts
                data[org] = org_data
        return data

    def vw_unasync_log(self, data, rhsm_output):
        orgs = re.findall(r"Host-to-guest mapping being sent to '(.*?)'", rhsm_output)
        if len(orgs) > 0: 
            data['orgs'] = orgs
            org_data = dict()
            for org in orgs:
                key = "Host-to-guest mapping being sent to '%s'" % org
                rex = re.compile(r'(?<=: ){.*?}\n+(?=201|$)', re.S)
                mapping_info = rex.findall(rhsm_output)[-1]
                try:
                    mapping_info = json.loads(mapping_info.replace('\n', ''), strict=False)
                except:
                    logger.warning("json.loads failed: %s" % mapping_info)
                    return data
                org_data['hypervisor_num'] = len(mapping_info.keys())
                for hypervisor_id, hypervisors_data in mapping_info.items():
                    facts = dict()
                    guests = list()
                    for guest in hypervisors_data:
                        guestId = guest['guestId']
                        guests.append(guestId)
                        attr = dict()
                        attr['guest_hypervisor'] = hypervisor_id
                        attr['state'] = guest['state']
                        attr['active'] = guest['attributes']['active']
                        attr['type'] = guest['attributes']['virtWhoType']
                        org_data[guestId] = attr
                    facts['guests'] = guests
                    org_data[hypervisor_id] = facts
                data[org] = org_data
        return data

    def vw_local_mode_log(self, data, rhsm_output):
        key = "Domain info:"
        rex = re.compile(r'(?<=Domain info: )\[.*?\]\n+(?=201|$)', re.S)
        mapping_info = rex.findall(rhsm_output)[-1]
        try:
            mapping_info = json.loads(mapping_info.replace('\n', ''), strict=False)
        except:
            logger.warning("json.loads failed: %s" % mapping_info)
            return data
        for item in mapping_info:
            guestId = item['guestId']
            attr = dict()
            attr['state'] = item['state']
            attr['active'] = item['attributes']['active']
            attr['type'] = item['attributes']['virtWhoType']
            data[guestId] = attr
        return data

    def vw_log_analyzer(self, data, tty_output, rhsm_output):
        if "virtwho.main DEBUG" in rhsm_output and \
                ("Domain info:" in rhsm_output or "Host-to-guest mapping being sent to" in rhsm_output):
            res = re.findall(r"reporter_id='(.*?)'", rhsm_output)
            if len(res) > 0:
                reporter_id = res[0].strip()
                data['reporter_id'] = reporter_id
            res = re.findall(r"Starting infinite loop with(.*?)seconds interval", rhsm_output)
            if len(res) > 0: 
                interval_time = res[0].strip()
                data['interval_time'] = int(interval_time)
            if "Domain info:" in rhsm_output:
                data = self.vw_local_mode_log(data, rhsm_output)
            res = re.findall(r"Server has capability '(.*?)'", rhsm_output)
            if len(res) > 0:
                is_async = res[0].strip()
                data['is_async'] = is_async
                data = self.vw_async_log(data, rhsm_output)
            else:
                data['is_async'] = "not_async"
                data = self.vw_unasync_log(data, rhsm_output)
        return data

    def vw_callback_loop_num(self):
        key= ""; loop_num = 0
        cmd = "grep 'Report for config' /var/log/rhsm/rhsm.log |grep 'placing in datastore' | head -1"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who placing number check")
        keys = re.findall(r'Report for config "(.*?)"', output)
        if output is not None and output != "" and len(keys) > 0:
            key = "Report for config \"%s\" gathered, placing in datastore" % keys[0]
            cmd = "grep '%s' /var/log/rhsm/rhsm.log | wc -l" % key
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who placing number check")
            if output is not None or output != "":
                loop_num = int(output)-1
        return key, loop_num

    def vw_callback_loop_time(self):
        loop_time = -1
        key, loop_num = self.vw_callback_loop_num()
        if loop_num != 0:
            cmd = "grep '%s' /var/log/rhsm/rhsm.log | head -2" % key
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who placing number check")
            output = output.split('\n')
            if len(output) > 0:
                d1 = re.findall(r"\d{2}:\d{2}:\d{2}", output[0])[0]
                d2 = re.findall(r"\d{2}:\d{2}:\d{2}", output[1])[0]
                h,m,s = d1.strip().split(":")
                s1 = int(h) * 3600 + int(m) * 60 + int(s)
                h,m,s = d2.strip().split(":")
                s2 = int(h) * 3600 + int(m) * 60 + int(s)
                loop_time = s2-s1
        return loop_time

    def vw_rhsm_modes_check(self, rhsm_output):
        env_mode = self.get_exported_param("HYPERVISOR_TYPE")
        rhsm_modes = re.findall(r'Using configuration.*\("(.*?)" mode\)', rhsm_output)
        if len(rhsm_modes) == 0:
            return env_mode
        elif len(rhsm_modes) == 1 and "fake" in rhsm_modes:
            return env_mode
        elif len(rhsm_modes) == 1 and "libvirt" in rhsm_modes and 'Using libvirt url: ""' in rhsm_output:
            return "libvirt-local"
        elif len(rhsm_modes) == 1 and "vdsm" in rhsm_modes and "vdsm" in env_mode:
            return "vdsm"
        elif len(rhsm_modes) == 2 and "vdsm" in rhsm_modes[0] and "vdsm" in rhsm_modes[1] and "vdsm" in env_mode:
            return "vdsm"
        else:
            return "mix"

    def vw_callback_send_num(self):
        server_type, server_ip, owner, env = self.vw_server_info()
        cmd = "cat /var/log/rhsm/rhsm.log"
        ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), desc="virt-who return rhsm.log", showlogger=False)
        if rhsm_output is None or rhsm_output == "":
            ret1, output1 = self.runcmd("ls /var/log/rhsm/virtwho/rhsm.log", self.ssh_host(), desc="rhsm.log check")
            ret2, output2 = self.runcmd("ls /var/log/rhsm/virtwho/virtwho.log", self.ssh_host(), desc="virtwho.log check")
            ret3, output3 = self.runcmd("ls /var/log/rhsm/virtwho.destination_*.log", self.ssh_host(), desc="destination.log check")
            if ret1 == 0:
                cmd = "cat %s" % output1
            elif ret2 == 0:
                cmd = "cat %s" % output2
            elif ret3 == 0:
                cmd = "cat %s" % output3
            ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), desc="virt-who return rhsm.log", showlogger=False)
        mode_type = self.vw_rhsm_modes_check(rhsm_output)
        if "0 hypervisors and 0 guests found" in rhsm_output:
            logger.warning("virt-who send terminated because '0 hypervisors and 0 guests found'")
            msg = "0 hypervisors and 0 guests found"
        elif "virtwho.main DEBUG" in rhsm_output or "rhsm.connection DEBUG" in rhsm_output:
            if "satellite" in server_type:
                if mode_type == "libvirt-local" or mode_type == "vdsm":
                    msg = r'Response: status=200, request="PUT /rhsm/consumers'
                else:
                    #if sat63/sat64, maybe need to check msg as below
                    #msg = r'Response: status=200, request="GET /rhsm/jobs/hypervisor_update'
                    msg = r'Response: status=200, request="POST /rhsm/hypervisors'
            if "stage" in server_type:
                if mode_type == "libvirt-local" or mode_type == "vdsm":
                    msg = r'Response: status=20.*requestUuid.*request="PUT /subscription/consumers'
                else:
                    #msg = r'Response: status=20.*requestUuid.*request="GET /subscription/jobs/hypervisor_update'
                    msg = r'Response: status=20.*requestUuid.*request="POST /subscription/hypervisors'
        else:
            if mode_type == "libvirt-local" or mode_type == "vdsm":
                msg = r"Sending update in guests lists for config"
            else:
                msg = r"Sending updated Host-to-guest mapping to"
        res = re.findall(msg, rhsm_output, re.I)
        return len(res)

    def vw_callback_error_num(self):
        error_num = 0 
        error_list = list()
        cmd = 'grep "\[.*ERROR.*\]" /var/log/rhsm/rhsm.log |sort'
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who error number check")
        if output is not None and output != "":
            error_list = output.strip().split('\n')
            error_num = len(error_list)
        return error_num, error_list

    def vw_callback_thread_num(self):
        thread_num = 0
        cmd = "ps -ef | grep virt-who -i | grep -v grep |wc -l"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who process number check")
        if output is not None and output != "":
            thread_num = int(output.strip())
        return thread_num

    def vw_callback_429_check(self):
        cmd = 'grep "status=429" /var/log/rhsm/rhsm.log |sort'
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="check 429 exist or not")
        if output is not None and output != "":
            return "yes"
        else:
            return "no"

    def vw_callback_pending_job(self):
        server_type, server_ip, owner, env = self.vw_server_info()
        pending_job = list()
        if "stage" in server_type:
            cmd = "cat /var/log/rhsm/rhsm.log"
            ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), desc="cat rhsm.log", showlogger=False)
            pending_job = re.findall(r"Job (.*?) not finished", rhsm_output)
        return pending_job

    def vw_thread_callback(self):
        pending_job = list()
        is_429 = self.vw_callback_429_check()
        error_num, error_list = self.vw_callback_error_num()
        thread_num = self.vw_callback_thread_num()
        key, loop_num = self.vw_callback_loop_num()
        loop_time = self.vw_callback_loop_time()
        send_num = self.vw_callback_send_num()
        if send_num > 0:
            pending_job = self.vw_callback_pending_job()
        logger.info("pending_job: %s, is_429: %s, loop_num: %s, loop_time: %s, send_num: %s, error_num: %s, thread_num: %s" \
                % (len(pending_job), is_429, loop_num, loop_time, send_num, error_num, thread_num))
        return pending_job, is_429, loop_num, loop_time, send_num, error_num, error_list, thread_num

    def vw_thread_timeout(self, t1, queue, timeout, exp_send, exp_loopnum, oneshot, event, exp_error):
        if event is not None:
            time.sleep(60)
            self.vw_hypervisor_event(event)
        while(t1.is_alive()):
            time.sleep(3)
        while True:
            time.sleep(6)
            ret, output = self.runcmd("ls /var/log/rhsm/", self.ssh_host(), desc="rhsm.log check")
            if ret == 0 and output is not None and output !="" \
                    and "Unable to connect to" not in output and "No such file or directory" not in output:
                break
        start=time.clock()
        while True:
            time.sleep(5)
            end=time.clock()
            spend_time = int((end-start)*10)
            pending_job, is_429, loop_num, loop_time, send_num, error_num, error_list, thread_num = self.vw_thread_callback()
            if is_429 == "yes":
                logger.info("virt-who is terminated by 429 status")
                break
            if thread_num == 0:
                logger.info("virt-who is terminated by pid exit")
                break
            if error_num != 0 and exp_error is False:
                logger.info("virt-who is terminated by error msg")
                break
            if spend_time >= timeout:
                logger.info("virt-who is terminated by timeout(10m)")
                break
            if oneshot is False:
                if send_num >= exp_send and loop_num >= exp_loopnum:
                    logger.info("virt-who is terminated by expected_send and expected_loop ready")
                    break
        data = dict()
        data['pending_job'] = pending_job
        data['is_429'] = is_429
        data['thread_num'] = thread_num
        data['error_num'] = error_num
        data['error_list'] = error_list
        data['send_num'] = send_num
        data['loop_num'] = loop_num
        data['loop_time'] = loop_time
        self.vw_stop()
        cmd = "cat /var/log/rhsm/rhsm.log"
        ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), desc="virt-who return rhsm.log")
        queue.put(("rhsm_output", rhsm_output, data))

    def vw_thread_run(self, t1, queue, cli):
        while(t1.is_alive()):
            time.sleep(3)
        if cli is not None:
            logger.info("Start to run virt-who by cli: %s" % cli)
            ret, tty_output = self.runcmd(cli, self.ssh_host(), desc="virt-who start by cli")
        else:
            logger.info("Start to run virt-who by service")
            ret, tty_output = self.run_service(self.ssh_host(), "virt-who", "start")
        queue.put(("tty_output", tty_output))

    def vw_thread_clean(self):
        self.vw_stop()
        cmd = "rm -rf /var/log/rhsm/*"
        ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who rhsm.log clean")

    def vw_start_thread(self, cli, timeout, exp_send, exp_loopnum, oneshot, event, exp_error):
        queue = Queue.Queue()
        results = list()
        threads = list()
        t1 = threading.Thread(target=self.vw_thread_clean, args=( ))
        threads.append(t1)
        t2 = threading.Thread(target=self.vw_thread_run, args=(t1, queue, cli))
        threads.append(t2)
        t3 = threading.Thread(target=self.vw_thread_timeout, args=(t1, queue, timeout, exp_send, exp_loopnum, oneshot, event, exp_error))
        threads.append(t3)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        while not queue.empty():
            results.append(queue.get())
        for item in results:
            if item[0] == "tty_output":
                tty_output = item[1]
            if item[0] == "rhsm_output":
                rhsm_output = item[1]
                data = item[2]
        return data, tty_output, rhsm_output

    def vw_start(self, cli=None, timeout=100, exp_send=1, exp_loopnum=0, oneshot=False, event=None, web_check=True, exp_error=False):
        for i in range(3):
            data, tty_output, rhsm_output = self.vw_start_thread(cli, timeout, exp_send, exp_loopnum, oneshot, event, exp_error)
            if data['is_429'] == "yes":
                wait_time = 60*(i+3)
                logger.warning("429 code found, try again after %s seconds..." % wait_time)
                time.sleep(wait_time)
            elif len(data['pending_job']) > 0:
                wait_time = 60*(i+1)
                logger.warning("Job is not finished, cancel it and try again after %s seconds..." % wait_time)
                self.vw_pending_job_cancel(data['pending_job'])
                time.sleep(wait_time)
            elif len(re.findall('RemoteServerException: Server error attempting a GET.*returned status 500', rhsm_output, re.I)) > 0:
                logger.warning("RemoteServerException return 500 code, restart virt-who again after 60s")
                time.sleep(60)
            else:
                logger.info("Succeeded to run vw_start and return log")
                data = self.vw_log_analyzer(data, tty_output, rhsm_output)
                if web_check and data['error_num'] == 0 and data['send_num'] > 0:
                    if self.vw_web_host_exist():
                        return data, tty_output, rhsm_output
                    else:
                        logger.warning("Mapping info is not sent to website, restart virt-who again after 15s")
                        time.sleep(15)
                else:
                    return data, tty_output, rhsm_output
        if data['is_429'] == "yes":
            raise FailException("Failed to due to 429 code, please check")
        elif len(data['pending_job']) > 0:
            raise FailException("Failed to due to not finished job, please check")
        else:
            logger.warning("Exception to run virt-who, please check")
            return data, tty_output, rhsm_output

    def vw_stop(self):
        ret, output = self.run_service(self.ssh_host(), "virt-who", "stop")
        if self.kill_pid_by_name(self.ssh_host(), "virt-who"):
            logger.info("Succeeded to stop and clean virt-who process")
        else:
            raise FailException("Failed to stop and clean virt-who process")

    def vw_rhsm_associate(self, data, host_uuid, guest_uuid):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "libvirt-local" in mode or "vdsm" in mode:
            if data.has_key(guest_uuid):
                logger.info("Succeeded to check the associated info by rhsm.log")
                return True
            else:
                logger.error("Faild to check the associated info by rhsm.log")
                return False
        else:
            if data[owner].has_key(guest_uuid) and host_uuid in data[owner][guest_uuid]['guest_hypervisor']:
                logger.info("Succeeded to check the associated info by rhsm.log")
                return True
            else:
                logger.error("Faild to check the associated info by rhsm.log")
                return False

    def vw_encrypted(self, password, option=None):
        if option is None or option == "":
            attrs = ["Password:|%s" % password]
            ret, output = self.run_expect(self.ssh_host(), "virt-who-password", attrs)
            if ret == 0 and output is not None:
                encrypted_value = output.split('\n')[-1].strip()
                logger.info("Succeeded to get encrypted_password without option: %s" % encrypted_value)
                return encrypted_value
            else: raise FailException("Failed to run virt-who-password")
        else:
            cmd = "virt-who-password %s %s > /tmp/vw.log" % (option, password)
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="virt-who-password to encrypted")
            if ret == 0:
                ret, output = self.runcmd("cat /tmp/vw.log", self.ssh_host(), desc="check encrypted value")
                if output is not None and output != "":
                    encrypted_value  = output.strip()
                    logger.info("Succeeded to get encrypted_password with %s option: %s" % (option,encrypted_value))
                    return encrypted_value
                else: raise FailException("Failed to run virt-who-password")
            else: raise FailException("Failed to run virt-who-password")
    
    def vw_pending_job_cancel(self, job_ids):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.stage_job_delete(self.ssh_host(), mode, job_ids)
        if "satellite" in server_type:
            logger.warning("not support to delete job currently")

    def vw_sub_register(self, ssh_args, sat_org=None):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            stage_user, stage_passwd, owner, env = self.stage_account_get(mode)
            self.system_register(ssh_args, server_type, stage_user=stage_user)
        if "satellite" in server_type:
            if sat_org is None:
                sat_org = args_satellite['default_owner']
            self.system_register(ssh_args, server_type, sat_org=sat_org)

    def vw_web_host_delete(self, ssh_args, host_name, host_uuid):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.stage_consumer_delete(ssh_args, mode, host_name, host_uuid)
        elif "satellite" in server_type:
            self.satellite_host_delete(ssh_args, server_ip, host_name, host_uuid)
        else:
            raise FailException("Unkonwn server type for web host delete")

    def vw_web_attach(self, ssh_args, host_name, host_uuid, pool_id, quantity=1):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.stage_consumer_attach(ssh_args, mode, host_name, host_uuid, pool_id)
        elif "satellite" in server_type:
            self.satellite_host_attach(ssh_args, server_ip, host_name, host_uuid, pool_id, quantity)
        else:
            raise FailException("Unkonwn server type for web attach")

    def vw_web_unattach(self, ssh_args, host_name, host_uuid):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            self.stage_consumer_unattach(ssh_args, mode, host_name, host_uuid)
        elif "satellite" in server_type:
            self.satellite_host_unattach(ssh_args, server_ip, host_name, host_uuid)
        else:
            raise FailException("Unkonwn server type for web unattach")

    def vw_web_associate(self, ssh_args, host_name, host_uuid, guest_name, guest_uuid):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            return self.stage_consumer_associate(ssh_args, mode, host_name, host_uuid, guest_uuid)
        elif "satellite" in server_type:
            return self.satellite_host_associate(ssh_args, server_ip, host_name, host_uuid, guest_name, guest_uuid)
        else:
            raise FailException("Unkonwn server type for web associate")

    def vw_web_registered_id(self, host_name, host_uuid):
        mode = self.get_exported_param("HYPERVISOR_TYPE")
        server_type, server_ip, owner, env = self.vw_server_info()
        if "stage" in server_type:
            registered_id = self.stage_consumer_uuid(self.ssh_host(), mode, host_name, host_uuid)
        if "satellite" in server_type:
            registered_id = self.satellite_host_id(self.ssh_host(), server_ip, host_name, host_uuid)
        if registered_id is None or registered_id == "" or registered_id is False:
            return False
        else:
            return True

    def vw_web_host_exist(self):
        keys = {'key1':'hypervisorId', 'key2':'name'}
        hypervisorId_list = list()
        name_list = list()
        for key, value in sorted(keys.items(),key=lambda item:item[0]):
            cmd = "grep '\"%s\": \"' /var/log/rhsm/* -r" % value
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="mapping info check", showlogger=False)
            if output.strip() is not None and output.strip() != "":
                lines = output.strip().split('\n')
                if len(lines) > 0:
                    for line in lines:
                        res = re.findall(r'"%s": "(.*?)"' % value, line)
                        if len(res) > 0 and key == "key1":
                                hypervisorId_list.append(res[-1])
                        if len(res) > 0 and key == "key2":
                                name_list.append(res[-1])
        if len(hypervisorId_list) > 0 and len(name_list) > 0:
            dictionary = dict(zip(name_list, hypervisorId_list))
            for name, uuid in dictionary.items():
                if self.vw_web_registered_id(name, uuid) is False:
                    return False
        if len(hypervisorId_list) > 0 and len(name_list) == 0:
            for hypervisorId in hypervisorId_list:
                if self.vw_web_registered_id(hypervisorId, hypervisorId) is False:
                    return False
        if len(hypervisorId_list) == 0 and len(name_list) > 0:
            for name in name_list:
                if self.vw_web_registered_id(name, name) is False:
                    return False
        return True

    def vw_msg_search(self, output, msg, exp_exist=True):
        res = re.findall(msg, output, re.I)
        num = len(res)
        if num > 0 and exp_exist is True:
            logger.info("Succeeded to search, expected msg(%s) is exist(%s)" %(msg, num))
            return True
        if num > 0 and exp_exist is False:
            logger.error("Failed to search, unexpected msg(%s) is exist(%s)" %(msg, num))
            return False
        if num == 0 and exp_exist is True:
            logger.error("Failed to search, expected msg(%s) is not exist(%s)" %(msg, num))
            return False
        if num == 0 and exp_exist is False:
            logger.info("Succeeded to search, unexpected msg(%s) is not exist(%s)" %(msg, num))
            return True

    def msg_validation(self, output, msg_list, exp_exist=True):
        matched_list = list()
        for msg in msg_list:
            is_matched = ""
            if "|" in msg:
                keys = msg.split("|")
                for key in keys:
                    if len(re.findall(key, output, re.I)) > 0:
                        logger.info("Found msg: %s" % key)
                        is_matched = "Yes"
            else:
                if len(re.findall(msg, output, re.I)) > 0:
                    logger.info("Found msg: %s" % msg)
                    is_matched = "Yes"
            if is_matched == "Yes":
                matched_list.append("Yes")
            else:
                matched_list.append("No")
        if "No" in matched_list and exp_exist is True:
            logger.error("Failed to search, expected msg(%s) is not exist" % msg_list)
            return False
        if "No" in matched_list and exp_exist is False:
            logger.info("Succeeded to search, unexpected msg(%s) is not exist" % msg_list)
            return True
        if "No" not in matched_list and "Yes" in matched_list and exp_exist is True:
            logger.info("Succeeded to search, expected msg(%s) is exist" % msg_list)
            return True
        if "No" not in matched_list and "Yes" in matched_list and exp_exist is False:
            logger.error("Failed to search, unexpected msg(%s) is exist" % msg_list)
            return False

    def op_normal_value(self, data, exp_error=None, exp_thread=None, exp_send=None, \
            exp_interval=None, exp_loopnum=None, exp_looptime=None):
        '''validate thread number'''
        if exp_thread is not None:
            if data['thread_num'] == exp_thread:
                logger.info("virtwho thread number(%s) is expected" % data['thread_num'])
            else:
                logger.error("virtwho thread number(%s) is not expected" % data['thread_num'])
                return False
        '''validate error number'''
        if exp_error is not None:
            if "|" in str(exp_error):
                if str(data['error_num']) in exp_error.split('|'):
                    logger.info("virtwho error number(%s) is expected" % data['error_num'])
                else:
                    logger.error("virtwho error number(%s) is not expected" % data['error_num'])
                    return False
            elif str(exp_error) == "nonzero" or str(exp_error) == "nz":
                if str(data['error_num']) == 0:
                    logger.error("virtwho error number(%s) is not expected" % data['error_num'])
                    return False
                else:
                    logger.info("virtwho error number(%s) is expected" % data['error_num'])
            else:
                if str(data['error_num']) == str(exp_error):
                    logger.info("virtwho error number(%s) is expected" % data['error_num'])
                else:
                    logger.error("virtwho error number(%s) is not expected" % data['error_num'])
                    return False
        '''validate send number'''
        if exp_send is not None:
            if data['send_num'] == exp_send:
                logger.info("virtwho send number(%s) is expected" % data['send_num'])
            else:
                logger.error("virtwho send number(%s) is not expected" % data['send_num'])
                return False
        '''validate interval time'''
        if exp_interval is not None:
            if data['interval_time'] == exp_interval:
                logger.info("virtwho interval time(%s) is expected" % data['interval_time'])
            else:
                logger.error("virtwho interval time(%s) is not expected" % data['interval_time'])
                return False
        '''validate loop number'''
        if exp_loopnum is not None:
            if data['loop_num'] == exp_loopnum:
                logger.info("virtwho loop number(%s) is expected" % data['loop_num'])
            else:
                logger.error("virtwho loop number(%s) is not expected" % data['loop_num'])
                return False
        '''validate loop time'''
        if exp_looptime is not None:
            loop_time = data['loop_time']
            if loop_time > exp_looptime+20 or loop_time < exp_looptime-20:
                logger.error("virtwho loop time(%s) is not expected" % loop_time)
                return False
            else:
                logger.info("virtwho loop time(%s) is expected" % loop_time)
        logger.info("Finished to validate all the expected options")
        return True

    #*********************************************
    # Performance Function
    #*********************************************
    def perf_env_init(self, mode):
        server_type, server_ip, owner, env = self.vw_server_info()
        if self.system_isregister(self.ssh_host(), server_type, server_ip, mode) is False:
            self.vw_sub_register(self.ssh_host())
        if self.system_sku_unattach(self.ssh_host()) is False:
            self.vw_sub_register(self.ssh_host())
        self.vw_etc_conf_disable_all()
        self.vw_etc_sys_disable_all()
        self.vw_etc_d_delete_all()

    def perf_cpu_check(self, t1):
        while(t1.is_alive()):
            time.sleep(2)
            cmd = "ps -ef | grep virt-who -i | grep -v grep | awk '{print $2}'"
            ret, output = self.runcmd(cmd, self.ssh_host(), desc="check virt-who pid")
            if ret == 0 and output is not None and output !="":
                pids = output.strip().split('\n')
                for pid in pids:
                    cmd = "ps -p %s" %pid +" -o %cpu,%mem,pid,cmd |tail -n+2"
                    ret, output = self.runcmd(cmd, self.ssh_host(), desc="check pid's cpu and memory")
                    if ret == 0 and output.split():
                        logger.info(output)

    def perf_virtwho_start(self, interval=None, oneshot=False, debug=True):
        virtwho_conf = "/etc/virt-who.conf"
        self.vw_option_enable("[global]", virtwho_conf)
        self.vw_option_enable("debug", virtwho_conf)
        if oneshot is True:
            self.vw_option_disable("interval", virtwho_conf)
            self.vw_option_enable("oneshot", virtwho_conf)
            self.vw_option_update_value("oneshot", 'True', virtwho_conf)
            if debug is True:
                self.vw_option_update_value("debug", 'True', virtwho_conf)
            else:
                self.vw_option_update_value("debug", 'False', virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start(exp_send=1, oneshot=True)
            res = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
            start_line = rhsm_output.splitlines()[0]
            end_line = rhsm_output.splitlines()[-1]
            d1 = re.findall(r"\d{2}:\d{2}:\d{2}", start_line)[0]
            d2 = re.findall(r"\d{2}:\d{2}:\d{2}", end_line)[0]
            h,m,s = d1.strip().split(":")
            s1 = int(h) * 3600 + int(m) * 60 + int(s)
            h,m,s = d2.strip().split(":")
            s2 = int(h) * 3600 + int(m) * 60 + int(s)
            oneshot_time = s2-s1
            logger.info("[Time] of oneshot: %s seconds" % oneshot_time)
        else:
            self.vw_option_disable("oneshot", virtwho_conf)
            self.vw_option_enable("interval", virtwho_conf)
            self.vw_option_update_value("interval", str(interval), virtwho_conf)
            if debug is True:
                self.vw_option_update_value("debug", 'True', virtwho_conf)
            else:
                self.vw_option_update_value("debug", 'False', virtwho_conf)
            data, tty_output, rhsm_output = self.vw_start(timeout=1200, exp_send=1, exp_loopnum=3)
            res = self.op_normal_value(data, exp_error=0, exp_thread=1, exp_send=1, exp_interval=interval, exp_loopnum=3, exp_looptime=interval)
            for line in rhsm_output.splitlines():
                if "Starting infinite loop with" in line:
                    logger.info(line)
            for line in rhsm_output.splitlines():
                if "No data to send" in line:
                    logger.info(line)
        for line in rhsm_output.splitlines():
            if "Sending updated Host-to-guest mapping to" in line:
                    logger.info(line)

    def perf_vms_add(self, mode, start, end):
        if mode == "esx":
            self.esx_vms_add(start, end)
        if mode == "rhevm":
            self.rhevm_vms_add(start, end)

    def perf_vms_del(self, mode):
        if mode == "esx":
            self.esx_vms_del()
        if mode == "rhevm":
            self.rhevm_vms_del()

    def perf_vms_check(self, mode):
        if mode == "esx":
            vm_num = len(self.esx_vms_list())
        elif mode == "rhevm":
            vm_num = len(self.rhevm_vms_list())
        else:
            vm_num = 0
        if vm_num < 900:
            new_vm = (900-vm_num)/5
            logger.info("Only %s guests ready, will add %s new guests" % (vm_num, 900-vm_num))
            self.perf_vms_add(mode, 1, new_vm+1)
        logger.info("%s guests are ready for testing" % len(self.esx_vms_list()))

