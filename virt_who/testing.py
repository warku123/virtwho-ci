from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.provision import Provision

class Testing(Provision):
    def get_config(self, name, value=None):
        if name == 'trigger_type':
            value = self.get_exported_param("TRIGGER_TYPE")
            if not value:
                value = config.virtwho.trigger_type
        if name == 'rhel_compose':
            value = self.get_exported_param("RHEL_COMPOSE")
            if not value:
                value = config.virtwho.rhel_compose
        if name == 'hypervisor_type':
            value = self.get_exported_param("HYPERVISOR_TYPE")
            if not value:
                value = config.hypervisor.type
        if name == "register_type":
            value = self.get_exported_param("REGISTER_TYPE")
            if not value:
                value = config.register.type
        if not value:
            raise FailException("no {0} config found".format(name))
        return value

    def ssh_host(self):
        host_ip = self.get_exported_param("VIRTWHO_HOST_IP")
        host_user = self.get_exported_param("VIRTWHO_HOST_USER")
        host_passwd = self.get_exported_param("VIRTWHO_HOST_PASSWD")
        if not host_ip:
            host_ip = config.virtwho.host_ip
        if not host_user:
            host_user = config.virtwho.host_user
        if not host_passwd:
            host_passwd = config.virtwho.host_passwd
        if not host_ip:
            raise FailException("no virtwho host ip defined")
        ssh_host = {"host":host_ip,"username":host_user,"password":host_passwd}
        return ssh_host

    def ssh_guest(self, uid=None):
        config = self.get_hypervisor_config(uid)
        return config['ssh_guest']

    def get_hypervisor_config(self, uid=None):
        if uid:
            hypervisor_type = self.get_exported_param("HYPERVISOR_{0}_TYPE".format(uid))
            server = self.get_exported_param("HYPERVISOR_{0}_SERVER".format(uid))
            username = self.get_exported_param("HYPERVISOR_{0}_USERNAME".format(uid))
            password = self.get_exported_param("HYPERVISOR_{0}_PASSWORD".format(uid))
            ssh_user = self.get_exported_param("HYPERVISOR_{0}_SSH_USER".format(uid))
            ssh_passwd = self.get_exported_param("HYPERVISOR_{0}_SSH_PASSWD".format(uid))
            guest_ip = self.get_exported_param("HYPERVISOR_{0}_GUEST_IP".format(uid))
            guest_name = self.get_exported_param("HYPERVISOR_{0}_GUEST_NAME".format(uid))
            guest_user = self.get_exported_param("HYPERVISOR_{0}_GUEST_USER".format(uid))
            guest_passwd = self.get_exported_param("HYPERVISOR_{0}_GUEST_PASSWD".format(uid))
            server_config = self.get_exported_param("HYPERVISOR_{0}_CONFIG_FILE")
        else:
            hypervisor_type = self.get_config('hypervisor_type')
            server = self.get_exported_param("HYPERVISOR_SERVER")
            username = self.get_exported_param("HYPERVISOR_USERNAME")
            password = self.get_exported_param("HYPERVISOR_PASSWORD")
            ssh_user = self.get_exported_param("HYPERVISOR_SSH_USER")
            ssh_passwd = self.get_exported_param("HYPERVISOR_SSH_PASSWD")
            guest_ip = self.get_exported_param("GUEST_IP")
            guest_name = self.get_exported_param("GUEST_NAME")
            guest_user = self.get_exported_param("GUEST_USER")
            guest_passwd = self.get_exported_param("GUEST_PASSWD")
            server_config = self.get_exported_param("HYPERVISOR_CONFIG_FILE")
            if not server:
                server = config.hypervisor.server
            if not username:
                username = config.hypervisor.server_username
            if not password:
                password = config.hypervisor.server_password
            if not ssh_user:
                ssh_user = config.hypervisor.server_ssh_user
            if not ssh_passwd:
                ssh_passwd = config.hypervisor.server_ssh_passwd
            if not guest_name:
                guest_name = config.hypervisor.guest_name
            if not guest_ip:
                guest_ip = config.hypervisor.guest_ip
            if not guest_user:
                guest_user = config.hypervisor.guest_user
            if not guest_passwd:
                guest_passwd = config.hypervisor.guest_passwd
            if not server_config:
                server_config = config.hypervisor.server_config

        if server is not None and "//" in server:
            server_ip = self.get_url_domain(server)
        else:
            server_ip = server
        ssh_hypervisor = {"host":server_ip,"username":username,"password":password}
        ssh_guest = {"host":guest_ip,"username":guest_user,"password":guest_passwd}
        if "libvirt-local" in hypervisor_type:
            ssh_hypervisor = self.ssh_host()
        if "rhevm" in hypervisor_type or "vdsm" in hypervisor_type:
            ssh_hypervisor = {"host":server_ip,"username":ssh_user,"password":ssh_passwd}
            if "//" not in server:
                server = self.rhevm_admin_get(ssh_hypervisor)
        if "esx" in hypervisor_type:
            ssh_hypervisor = {"host":server_ip,"username":ssh_user,"password":ssh_passwd}
        configs = {
                'type':hypervisor_type,
                'server':server,
                'username':username,
                'password':password,
                'guest_name':guest_name,
                'ssh_hypervisor':ssh_hypervisor,
                'ssh_guest':ssh_guest,
                'server_config':server_config
                }
        return configs

    def get_register_config(self):
        register_type = self.get_config('register_type')
        server = self.get_exported_param("REGISTER_SERVER")
        owner = self.get_exported_param("REGISTER_OWNER")
        env = self.get_exported_param("REGISTER_ENV")
        admin_user = self.get_exported_param("REGISTER_ADMIN_USER")
        admin_passwd = self.get_exported_param("REGISTER_ADMIN_PASSWD")
        ssh_user = self.get_exported_param("REGISTER_SSH_USER")
        ssh_passwd = self.get_exported_param("REGISTER_SSH_PASSWD")
        if not register_type:
            register_type = config.register.type
        if not server:
            server = config.register.server
        if not owner:
            owner = config.register.owner
        if not env:
            env = config.register.env
        if not admin_user:
            admin_user = config.register.admin_user
        if not admin_passwd:
            admin_passwd = config.register.admin_passwd
        if not ssh_user:
            ssh_user = config.register.ssh_user
        if not ssh_passwd:
            ssh_passwd = config.register.ssh_passwd
        vdc = config.manifest.vdc
        vdc_bonus = config.manifest.vdc_bonus
        instance = config.manifest.instance
        limit = config.manifest.limit
        unlimit = config.manifest.unlimit
        if "stage" in register_type:
            api = "https://{0}/subscription".format(server)
            ssh_sat = ""
            prefix = "/subscription"
        if "satellite" in register_type:
            api = "https://{0}".format(server)
            ssh_sat = {"host": server,"username":ssh_user,"password":ssh_passwd}
            prefix = "/rhsm"
        if not vdc:
            vdc = "RH00001"
        if not vdc_bonus:
            vdc_bonus = "RH00049"
        if not instance:
            instance = "RH00003"
        if not limit:
            limit = "RH00204"
        if not unlimit:
            unlimit = "RH00060"
        configs = {
                'type':register_type,
                'server':server,
                'username':admin_user,
                'password':admin_passwd,
                'owner':owner,
                'env':env,
                'prefix':prefix,
                'ssh_user': ssh_user,
                'ssh_passwd':ssh_passwd,
                'api':api,
                'ssh_sat':ssh_sat,
                'vdc':vdc,
                'vdc_bonus':vdc_bonus,
                'instance':instance,
                'limit':limit,
                'unlimit':unlimit
                }
        return configs

    def hypervisor_supported(self, hypervisor_type):
        if hypervisor_type in (
                'esx',
                'hyperv',
                'rhevm',
                'vdsm',
                'xen',
                'kubevirt',
                'libvirt-remote',
                'libvirt-local'
                ):
            return True
        raise FailException("Unsupported hypervisor_type: {0}".format(hypervisor_type))

    def get_hypervisor_hostname(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            esx_host = self.vcenter_host_get(cert, ssh_hypervisor, guest_name)
            hostname = self.vcenter_fqdn_get(cert, ssh_hypervisor, esx_host)
        if hypervisor_type == "hyperv":
            hostname = self.hyperv_host_name(ssh_hypervisor)
        if hypervisor_type == "xen":
            hostname = self.get_hostname(ssh_hypervisor)
        if hypervisor_type == "kubevirt":
            hostname = self.kubevirt_guest_node_name(ssh_hypervisor, guest_name)
        if hypervisor_type == "rhevm":
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            hostname = self.rhevm_host_name_by_guestname(ssh_hypervisor, rhevm_shell, guest_name)
        if hypervisor_type == "vdsm":
            hostname = self.get_hostname(self.ssh_host())
        if hypervisor_type == "libvirt-local":
            hostname = self.get_hostname(self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            hostname = self.get_hostname(ssh_hypervisor)
        return hostname

    def get_hypervisor_hostuuid(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            esx_host = self.vcenter_host_get(cert, ssh_hypervisor, guest_name)
            uuid = self.vcenter_host_uuid(cert, ssh_hypervisor, esx_host)
        if hypervisor_type == "hyperv":
            uuid = self.hyperv_host_uuid(ssh_hypervisor)
        if hypervisor_type == "xen":
            uuid = self.xen_host_uuid(ssh_hypervisor)
        if hypervisor_type == "kubevirt":
            node_name = self.kubevirt_guest_node_name(ssh_hypervisor, guest_name)
            uuid = self.kubevirt_host_uuid(ssh_hypervisor, node_name)
        if hypervisor_type == "libvirt-local":
            uuid = self.libvirt_host_uuid(self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            uuid = self.libvirt_host_uuid(ssh_hypervisor)
        if hypervisor_type in ("rhevm", "vdsm"):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            uuid = self.rhevm_host_uuid_by_guestname(ssh_hypervisor, rhevm_shell, guest_name)
        return uuid

    def get_hypervisor_hwuuid(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            esx_host = self.vcenter_host_get(cert, ssh_hypervisor, guest_name)
            hwuuid = self.vcenter_host_hwuuid(cert, ssh_hypervisor, esx_host)
        elif hypervisor_type == "rhevm":
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            host_uuid = self.rhevm_host_uuid_by_guestname(ssh_hypervisor, rhevm_shell, guest_name)
            hwuuid = self.rhevm_host_hwuuid_by_uuid(ssh_hypervisor, rhevm_shell, host_uuid)
        else:
            hwuuid = "unsupported hypervisor type"
        return hwuuid
        
    def get_hypervisor_guestuuid(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            uuid = self.vcenter_guest_uuid(cert, ssh_hypervisor, guest_name)
        if hypervisor_type == "hyperv":
            uuid = self.hyperv_guest_uuid(ssh_hypervisor, guest_name)
        if hypervisor_type == "xen":
            uuid = self.xen_guest_uuid(ssh_hypervisor, guest_name)
        if hypervisor_type == "kubevirt":
            uuid = self.kubevirt_guest_uuid(ssh_hypervisor, guest_name)
        if hypervisor_type == "libvirt-local":
            uuid = self.libvirt_guest_uuid(guest_name, self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            uuid = self.libvirt_guest_uuid(guest_name, ssh_hypervisor)
        if hypervisor_type in ("rhevm", "vdsm"):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            uuid = self.rhevm_guest_uuid(ssh_hypervisor, rhevm_shell, guest_name)
        return uuid

    def hypervisor_guest_start(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        guest_ip = config['ssh_guest']['host']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "kubevirt":
            return "unsupport guest start"
        if hypervisor_type in ('rhevm', 'vdsm'):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            self.rhevm_guest_start(ssh_hypervisor, rhevm_shell, guest_name)
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            guest_ip = self.vcenter_guest_start(cert, ssh_hypervisor, guest_name)
        if hypervisor_type == "hyperv":
            guest_ip = self.hyperv_guest_start(ssh_hypervisor, guest_name)
        if hypervisor_type == "xen":
            guest_ip =  self.xen_guest_start(ssh_hypervisor, guest_name)
        if hypervisor_type == "libvirt-local":
            guest_ip = self.libvirt_guest_start(guest_name, self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            guest_ip = self.libvirt_guest_start(guest_name, ssh_hypervisor)
        if guest_ip:
            self.set_exported_param("GUEST_IP", guest_ip)
            logger.info("Succeeded to start guest for mode {0}, guest ip: {1}".format(hypervisor_type, guest_ip))

    def hypervisor_guest_stop(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "kubevirt":
            return "unsupport guest stop"
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            self.vcenter_guest_stop(cert, ssh_hypervisor, guest_name)
        if hypervisor_type == "hyperv":
            self.hyperv_guest_stop(ssh_hypervisor, guest_name)
        if hypervisor_type == "xen":
            self.xen_guest_stop(ssh_hypervisor, guest_name)
        if hypervisor_type == "libvirt-local":
            self.libvirt_guest_stop(guest_name, self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            self.libvirt_guest_stop(guest_name, ssh_hypervisor)
        if hypervisor_type in ('rhevm', 'vdsm'):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            self.rhevm_guest_stop(ssh_hypervisor, rhevm_shell, guest_name)
        logger.info("Succeeded to stop guest for mode {0}".format(hypervisor_type))

    def hypervisor_guest_suspend(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "kubevirt":
            return "unsupport guest suspend"
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            self.vcenter_guest_suspend(cert, ssh_hypervisor, guest_name)
        if hypervisor_type == "hyperv":
            self.hyperv_guest_suspend(ssh_hypervisor, guest_name)
        if hypervisor_type == "xen":
            self.xen_guest_suspend(ssh_hypervisor, guest_name)
        if hypervisor_type == "libvirt-local":
            self.libvirt_guest_suspend(guest_name, self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            self.libvirt_guest_suspend(guest_name, ssh_hypervisor)
        if hypervisor_type in ('rhevm', 'vdsm'):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            self.rhevm_guest_suspend(ssh_hypervisor, rhevm_shell, guest_name)
        logger.info("Succeeded to suspend guest for mode {0}".format(hypervisor_type))

    def hypervisor_guest_resume(self, uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        guest_name = config['guest_name']
        self.hypervisor_supported(hypervisor_type)
        if hypervisor_type == "kubevirt":
            return "unsupport guest resume"
        if hypervisor_type == "esx":
            cert = self.vcenter_cert(config['server'], config['username'], config['password'])
            self.vcenter_guest_resume(cert, ssh_hypervisor, guest_name)
        if hypervisor_type == "hyperv":
            self.hyperv_guest_resume(ssh_hypervisor, guest_name)
        if hypervisor_type == "xen":
            self.xen_guest_resume(ssh_hypervisor, guest_name)
        if hypervisor_type == "libvirt-local":
            self.libvirt_guest_resume(guest_name, self.ssh_host())
        if hypervisor_type == "libvirt-remote":
            self.libvirt_guest_resume(guest_name, ssh_hypervisor)
        if hypervisor_type in ('rhevm', 'vdsm'):
            rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_hypervisor)
            self.rhevm_guest_resume(ssh_hypervisor, rhevm_shell, guest_name)
        logger.info("Succeeded to resume guest for mode {0}".format(hypervisor_type))

    def hypervisor_firewall_setup(self, action="on", uid=None):
        config = self.get_hypervisor_config(uid)
        hypervisor_type = config['type']
        ssh_hypervisor = config['ssh_hypervisor']
        ssh_host = self.ssh_host()
        host = ssh_host['host']
        if ":" in host:
            var = host.split(':')
            host = var[0]
        if hypervisor_type == "rhevm" \
                or hypervisor_type == "libvirt-remote" \
                or hypervisor_type == "kubevirt" \
                or hypervisor_type == "xen":
            if action == "off":
                cmd = "iptables -I INPUT -s {0} -j DROP".format(host)
            if action == "on":
                cmd = "iptables -D INPUT -s {0} -j DROP".format(host)
            ret, output = self.runcmd(cmd, ssh_hypervisor)
        if hypervisor_type == "esx" or hypervisor_type == "hyperv":
            if action == "off":
                cmd1 = "NetSh Advfirewall set allprofiles state on"
                cmd2 = r'netsh advfirewall firewall add rule name="BLOCKED IP" interface=any dir=in action=block remoteip={0}'.format(host)
            if action == "on":
                cmd1 = r'netsh advfirewall firewall delete rule name="BLOCKED IP" remoteip={0}'.format(host)
                cmd2 = "NetSh Advfirewall set allprofiles state off"
            ret, output = self.runcmd(cmd1, ssh_hypervisor)
            ret, output = self.runcmd(cmd2, ssh_hypervisor)

    #******************************************
    # virt-who config function
    #******************************************
    def vw_case_info(self, case_name, case_id=None):
        logger.info("+"*30)
        msg = case_name
        if case_id:
            msg = "{0}:{1}".format(case_id, case_name)
        logger.info(msg)
        fd = open(DEBUG_FILE, 'a')
        fd.write("{0}\n".format(msg))
        fd.close()
        if self.pkg_check(self.ssh_host(), 'virt-who') is False:
            self.pkg_install(self.ssh_host(), 'virt-who')

    def vw_case_skip(self, skip_reason=None):
        try:
            self.skipTest("SkipTest, not avaialbe for {0}".format(skip_reason))
        except Exception, SkipTest:
            logger.info(str(SkipTest))
            raise SkipTest
        finally:
            logger.info("Succeeded to skip case\n")

    def vw_case_result(self, results, notes=None):
        for key, value in results.items():
            if False in value:
                logger.error('Failed step: {0}'.format(key))
                print 'Failed step: {0}'.format(key)
        if notes is not None:
            for msg in notes:
                logger.warning(msg)
                print msg
        if any(False in res for res in results.values()):
            raise FailException("Failed to run case, please check the failed steps\n")
        else:
            logger.info("Succeeded to run case, all steps passed\n")

    def vw_case_init(self, uid=None):
        hypervisor_config = self.get_hypervisor_config(uid)
        register_config = self.get_register_config()
        hypervisor_type = hypervisor_config['type']
        ssh_hypervisor = hypervisor_config['ssh_hypervisor']
        register_type = register_config['type']
        if "libvirt-remote" in hypervisor_type:
            self.ssh_no_passwd_access(self.ssh_host(), ssh_hypervisor)
        if "vdsm" in hypervisor_type or "rhevm" in hypervisor_type:
            cmd = "ovirt-aaa-jdbc-tool user unlock admin"
            self.runcmd(cmd, ssh_hypervisor)
        self.vw_thread_clean()
        host_name = self.get_hypervisor_hostname(uid)
        host_uuid = self.get_hypervisor_hostuuid(uid)
        self.vw_web_host_delete(host_name, host_uuid, retry=False)
        self.system_register_config(self.ssh_host(), register_type, register_config)
        self.system_register(self.ssh_host(), register_type, register_config)
        self.system_register_config(self.ssh_guest(uid), register_type, register_config)
        self.system_register(self.ssh_guest(uid), register_type, register_config)
        self.vw_etc_conf_disable_all()
        self.vw_etc_sys_disable_all()
        self.vw_etc_d_delete_all()

    def vw_hypervisor_event(self, event):
        if event == "guest_suspend":
            self.hypervisor_guest_suspend()
        elif event == "guest_resume":
            self.hypervisor_guest_resume()
        elif event == "guest_stop":
            self.hypervisor_guest_stop()
        elif event == "guest_start":
            self.hypervisor_guest_start()
        else:
            raise FailException("Unsupported hypervisor event")

    def vw_etc_conf_disable_all(self):
        op_1 = '-e "/;/d"'
        op_2 = '-e "s|^[^#]|#&|g"'
        cmd = 'sed -i %s %s /etc/virt-who.conf' % (op_1, op_2)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret != 0:
            raise FailException("Failed to disable all options in /etc/virt-who.conf")
        else:
            logger.info("Succeeded to disable all options in /etc/virt-who.conf")

    def vw_etc_sys_disable_all(self):
        op_1 = '-e "s|^[^#]|#&|g"'
        cmd = 'sed -i %s /etc/sysconfig/virt-who' % op_1
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret != 0:
            raise FailException("Failed to disable all modes in /etc/sysconfig/virt-who")
        else:
            logger.info("Succeeded to disable all options in /etc/sysconfig/virt-who")

    def vw_etc_d_delete_all(self):
        cmd = "rm -rf /etc/virt-who.d/*; rm -f /etc/virt-who.d/.*swp"
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret != 0:
            raise FailException("Failed to delete all files in /etc/virt-who.d/")
        else:
            logger.info("Succeeded to delete all files in /etc/virt-who.d/")

    def vw_etc_sys_mode_enable(self, uid=None):
        filename = "/etc/sysconfig/virt-who"
        hypervisor_config = self.get_hypervisor_config(uid)
        register_config = self.get_register_config()
        mode = hypervisor_config['type']
        server = hypervisor_config['server']
        username = hypervisor_config['username']
        password = hypervisor_config['password']
        owner = register_config['owner']
        env = register_config['env']
        mode = mode.upper()
        if mode == "LIBVIRT-REMOTE":
            mode = "LIBVIRT"
        if mode == "LIBVIRT-LOCAL":
            logger.info("libvirt local mode is default, don't need to configure")
            return True
        cf_type = '-e "s|.*{0}=.*|VIRTWHO_{0}=1|g"'.format(mode)
        cf_owner = '-e "s|.*{0}_OWNER=.*|VIRTWHO_{0}_OWNER={1}|g"'.format(mode, owner)
        cf_env = '-e "s|.*{0}_ENV=.*|VIRTWHO_{0}_ENV={1}|g"'.format(mode, env)
        cf_server = '-e "s|.*{0}_SERVER=.*|VIRTWHO_{0}_SERVER={1}|g"'.format(mode, server)
        cf_username = '-e "s|.*{0}_USERNAME=.*|VIRTWHO_{0}_USERNAME={1}|g"'.format(mode, username)
        cf_password = '-e "s|.*{0}_PASSWORD=.*|VIRTWHO_{0}_PASSWORD={1}|g"'.format(mode, password)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            cf_env = ''
        if mode == "VDSM":
            cmd = 'sed -i -e "s|.*VIRTWHO_VDSM=.*|VIRTWHO_VDSM=1|g" {0}'.format(filename)
        elif mode == "KUBEVIRT":
            server_config = hypervisor_config['server_config']
            cmd = 'sed -i "/^KUBECONFIG/d" %s; sed -i "/^#KUBECONFIG/d" %s' % (filename, filename)
            ret, output = self.runcmd(cmd, self.ssh_host())
            cmd = 'echo -e "\nKUBECONFIG=%s" >> %s' % (server_config, filename)
            ret, output = self.runcmd(cmd, self.ssh_host())
            cmd = 'sed -i {0} {1} {2} {3}'.format(cf_type, cf_owner, cf_env, filename)
        else:
            cmd = 'sed -i {0} {1} {2} {3} {4} {5} {6}'.format(
                    cf_type, cf_owner, cf_env, cf_server, cf_username, cf_password, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret != 0:
            raise FailException("Failed to enable mode {0} in /etc/sysconfig/virt-who".format(mode))
        else:
            logger.info("Succeeded to enable mode {0} in /etc/sysconfig/virt-who".format(mode))

    def vw_etc_d_mode_create(self, config_name, config_file, uid=None):
        hypervisor_config = self.get_hypervisor_config(uid)
        register_config = self.get_register_config()
        mode = hypervisor_config['type']
        server = hypervisor_config['server']
        username = hypervisor_config['username']
        password = hypervisor_config['password']
        owner = register_config['owner']
        env = register_config['env']
        mode = mode.lower()
        if mode == "libvirt-remote":
            mode = "libvirt"
        if mode == "libvirt-local":
            logger.info("libvirt local mode is default, don't need to configure")
            return True
        cf_file = '{0}\n'.format(config_file)
        cf_title = '[{0}]\n'.format(config_name)
        cf_type = 'type={0}\n'.format(mode)
        cf_server = 'server={0}\n'.format(server)
        cf_username = 'username={0}\n'.format(username)
        cf_password = 'password={0}\n'.format(password)
        cf_owner = 'owner={0}\n'.format(owner)
        cf_env = 'env={0}\n'.format(env)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            cf_env = ''
        if mode == "vdsm":
            cmd = "echo -e '[{0}]\ntype={1}' > {2}".format(config_name, mode, config_file)
        elif mode == "kubevirt":
            cf_kube = 'kubeconfig={0}\n'.format(hypervisor_config['server_config'])
            cmd = ('cat <<EOF > {0}''{1}''{2}''{3}''{4}''{5}''EOF').format(
                    cf_file, cf_title, cf_type, cf_kube, cf_owner, cf_env)
        else:
            cmd = ('cat <<EOF > {0}''{1}''{2}''{3}''{4}''{5}''{6}''{7}''EOF').format(
                    cf_file, cf_title, cf_type, cf_server, cf_username, cf_password, cf_owner, cf_env)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret != 0:
            raise FailException("Failed to create config file {0}".format(config_file))
        else:
            logger.info("Succeeded to create config file {0}".format(config_file))

    def vw_fake_json_create(self, cli, json_file):
        self.vw_stop()
        cmd ="{0} -p -d > {1}".format(cli, json_file)
        ret, output = self.runcmd(cmd, self.ssh_host())
        ret, output = self.runcmd("cat {0}".format(json_file), self.ssh_host())
        logger.info(output)
        if "guestId" not in output:
            raise FailException("Failed to create json data: {0}".format(json_file))
        logger.info("Succeeded to create json data: {0}".format(json_file))

    def vw_fake_conf_create(self, conf_file, json_file, is_hypervisor=True):
        register_config = self.get_register_config()
        owner = register_config['owner']
        env = register_config['env']
        cf_file = '{0}\n'.format(conf_file)
        cf_title = '[fake]\n'
        cf_type = 'type=fake\n'
        cf_json = 'file={0}\n'.format(json_file)
        cf_is_hypervisor = 'is_hypervisor={0}\n'.format(is_hypervisor)
        cf_owner = 'owner={0}\n'.format(owner)
        cf_env = 'env={0}\n'.format(env)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            cf_env=''
        cmd = ('cat <<EOF > {0}''{1}''{2}''{3}''{4}''{5}''{6}''EOF').format(
                cf_file, cf_title, cf_type, cf_json, cf_is_hypervisor, cf_owner, cf_env)
        ret, output = self.runcmd(cmd, self.ssh_host())
        ret, output = self.runcmd("ls {0}".format(conf_file), self.ssh_host())
        if ret != 0 :
            raise FailException("Failed to create fake config file: {0}".format(conf_file))
        logger.info("Succeeded to create fake config file: {0}".format(conf_file))

    def vw_option_update_name(self, option, rename, filename):
        option = self.shell_escape_char(option)
        rename = self.shell_escape_char(rename)
        cmd = 'sed -i "s|^%s|%s|g" %s' % (option, rename, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to update option name %s to %s" % (option, rename))
        else:
            raise FailException("Failed to update option name %s to %s" % (option, rename))

    def vw_option_update_value(self, option, value, filename):
        option = self.shell_escape_char(option)
        value = self.shell_escape_char(value)
        cmd = 'sed -i "s|^%s.*|%s=%s|g" %s' % (option, option, value, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to set option %s value to %s" % (option, value))
        else:
            raise FailException("Failed to set option %s value to %s" % (option, value))

    def vw_option_enable(self, option, filename):
        option = self.shell_escape_char(option)
        op_1 = '-e "s|^#%s$|%s|g"' % (option, option)
        op_2 = '-e "s|^#%s=|%s=|g"' % (option, option)
        op_3 = '-e "s|^# %s$|%s|g"' % (option, option)
        op_4 = '-e "s|^# %s=|%s=|g"' % (option, option)
        cmd = 'sed -i %s %s %s %s %s' % (op_1, op_2, op_3, op_4, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to enable option %s" % option)
        else:
            raise FailException("Failed to enable option %s" % option)

    def vw_option_disable(self, option, filename):
        option = self.shell_escape_char(option)
        cmd = 'sed -i "s|^%s|#%s|g" %s' % (option, option, filename) 
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to disable option %s" % option)
        else:
            raise FailException("Failed to disable option %s" % option)

    def vw_option_add(self, option, value, filename):
        cmd = 'echo -e "\n%s=%s" >> %s' % (option, value, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to add option %s=%s" % (option, value))
        else:
            raise FailException("Failed to add option %s=%s" % (option, value))

    def vw_option_del(self, option, filename):
        option = self.shell_escape_char(option)
        cmd = 'sed -i "/^%s/d" %s; sed -i "/^#%s/d" %s' % (option, filename, option, filename)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0:
            logger.info("Succeeded to delete option %s" % option)
        else:
            raise FailException("Failed to delete option %s" % option)

    def vw_option_get(self, option, filename):
        cmd = "grep -v '^#' %s |grep ^%s" % (filename, option)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0 and option in output:
            value = output.split('=')[1].strip()
            return value
        else:
            raise FailException("No this option or option is not enabled")

    def vw_cli_base(self, uid=None):
        hypervisor_config = self.get_hypervisor_config(uid)
        register_config = self.get_register_config()
        mode = hypervisor_config['type']
        server = hypervisor_config['server']
        username = hypervisor_config['username']
        password = hypervisor_config['password']
        owner = register_config['owner']
        env = register_config['env']
        mode = mode.lower()
        if mode == "libvirt-remote":
            mode = "libvirt"
        cf_type = "--{0}".format(mode)
        cf_owner = "--{0}-owner={1}".format(mode, owner)
        cf_env = "--{0}-env={1}".format(mode, env)
        cf_server = "--{0}-server={1}".format(mode, server)
        cf_username = "--{0}-username={1}".format(mode, username)
        cf_password = "--{0}-password={1}".format(mode, password)
        if self.pkg_check(self.ssh_host(), 'virt-who')[9:15] >= '0.24.6':
            cf_env=''
        if mode == "libvirt-local" or mode == "" or mode is None: 
            cmd = "virt-who "
        elif mode == "vdsm":
            cmd = "virt-who --vdsm "
        elif mode == "kubevirt":
            server_config = hypervisor_config['server_config']
            ret, output = self.runcmd("export KUBECONFIG={0}".format(server_config), self.ssh_host())
            cmd = "virt-who {0} {1} {2} ".format(cf_type, cf_owner, cf_env)
        else:
            cmd = "virt-who {0} {1} {2} {3} {4} {5} ".format(
                    cf_type, cf_owner, cf_env, cf_server, cf_username, cf_password)
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
                    facts['dmi'] = item['facts']['dmi.system.uuid']
                    if item['facts'].has_key('hypervisor.cluster'):
                        facts['cluster'] = item['facts']['hypervisor.cluster']
                    else:
                        facts['cluster'] = ''
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
        if not env_mode:
            env_mode = self.get_exported_param("HYPERVISOR_01_TYPE")
        if not env_mode:
            env_mode = self.get_exported_param("HYPERVISOR_02_TYPE")
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
        register_config = self.get_register_config()
        register_type = register_config['type']
        cmd = "cat /var/log/rhsm/rhsm.log"
        ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), debug=False)
        if rhsm_output is None or rhsm_output == "":
            ret1, output1 = self.runcmd("ls /var/log/rhsm/virtwho/rhsm.log", self.ssh_host())
            ret2, output2 = self.runcmd("ls /var/log/rhsm/virtwho/virtwho.log", self.ssh_host())
            ret3, output3 = self.runcmd("ls /var/log/rhsm/virtwho.destination_*.log", self.ssh_host())
            if ret1 == 0:
                cmd = "cat {0}".format(output1)
            elif ret2 == 0:
                cmd = "cat {0}".format(output2)
            elif ret3 == 0:
                cmd = "cat {0}".format(output3)
            ret, rhsm_output = self.runcmd(cmd, self.ssh_host(), debug=False)
        mode_type = self.vw_rhsm_modes_check(rhsm_output)
        if "0 hypervisors and 0 guests found" in rhsm_output:
            logger.info("virt-who send terminated because '0 hypervisors and 0 guests found'")
            msg = "0 hypervisors and 0 guests found"
        elif "virtwho.main DEBUG" in rhsm_output or "rhsm.connection DEBUG" in rhsm_output:
            if "satellite" in register_type:
                if mode_type == "libvirt-local" or mode_type == "vdsm":
                    msg = r'Response: status=200, request="PUT /rhsm/consumers'
                else:
                    msg = r'Response: status=200, request="POST /rhsm/hypervisors'
            if "stage" in register_type:
                if mode_type == "libvirt-local" or mode_type == "vdsm":
                    msg = r'Response: status=20.*requestUuid.*request="PUT /subscription/consumers'
                else:
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
        ret, output = self.runcmd(cmd, self.ssh_host())
        if output is not None and output != "":
            error_list = output.strip().split('\n')
            error_num = len(error_list)
        return error_num, error_list

    def vw_callback_thread_num(self):
        thread_num = 0
        cmd = "ps -ef | grep virt-who -i | grep -v grep |wc -l"
        ret, output = self.runcmd(cmd, self.ssh_host())
        if output is not None and output != "":
            thread_num = int(output.strip())
        return thread_num

    def vw_callback_429_check(self):
        cmd = 'grep "status=429" /var/log/rhsm/rhsm.log |sort'
        ret, output = self.runcmd(cmd, self.ssh_host())
        if output is not None and output != "":
            return "yes"
        else:
            return "no"

    def vw_callback_pending_job(self):
        register_config = self.get_register_config()
        register_type = register_config['type']
        pending_job = list()
        if "stage" in register_type:
            cmd = "cat /var/log/rhsm/rhsm.log"
            ret, rhsm_output = self.runcmd(cmd, self.ssh_host(),debug=False)
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

    def vw_thread_timeout(
            self, t1, q, timeout, exp_send, exp_loopnum, oneshot, exp_error, event):
        while t1.is_alive():
            time.sleep(3)
        if event is not None:
            time.sleep(60)
            self.vw_hypervisor_event(event)
        while True:
            time.sleep(6)
            ret, output = self.runcmd("ls /var/log/rhsm/", self.ssh_host())
            if (
                ret == 0
                and output is not None
                and output != ""
                and "Unable to connect to" not in output
                and "No such file or directory" not in output
            ):
                break
        start = time.time()
        while True:
            time.sleep(5)
            end = time.time()
            spend_time = int(end-start)
            (
                pending_job,
                is_429,
                loop_num,
                loop_time,
                send_num,
                error_num,
                error_list,
                thread_num
            ) = self.vw_thread_callback()
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
                logger.info("virt-who is terminated by timeout(900s)")
                break
            if oneshot is False:
                if send_num >= exp_send and loop_num >= exp_loopnum:
                    logger.info(
                        "virt-who is terminated by expected_send and expected_loop ready"
                    )
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
        ret, rhsm_output = self.runcmd(cmd, self.ssh_host())
        q.put(("rhsm_output", rhsm_output, data))

    def vw_thread_run(self, t1, q, cli):
        while t1.is_alive():
            time.sleep(3)
        if cli is not None:
            logger.info("Start to run virt-who by cli: %s" % cli)
            ret, tty_output = self.runcmd(cli, self.ssh_host())
        else:
            logger.info("Start to run virt-who by service")
            ret, tty_output = self.run_service(self.ssh_host(), "virt-who", "start")
        q.put(("tty_output", tty_output))

    def vw_thread_clean(self):
        self.vw_stop()
        cmd = "rm -rf /var/log/rhsm/*"
        ret, output = self.runcmd(cmd, self.ssh_host())

    def vw_start_thread(
            self, cli, timeout, exp_send, exp_loopnum, oneshot, event, exp_error):
        q = queue.Queue()
        results = list()
        threads = list()
        t1 = threading.Thread(target=self.vw_thread_clean, args=())
        threads.append(t1)
        t2 = threading.Thread(target=self.vw_thread_run, args=(t1, q, cli))
        threads.append(t2)
        t3 = threading.Thread(
            target=self.vw_thread_timeout,
            args=(t1, q, timeout, exp_send, exp_loopnum, oneshot, exp_error, event)
        )
        threads.append(t3)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        while not q.empty():
            results.append(q.get())
        for item in results:
            if item[0] == "tty_output":
                tty_output = item[1]
            if item[0] == "rhsm_output":
                rhsm_output = item[1]
                data = item[2]
        return data, tty_output, rhsm_output

    def vw_start(self, cli=None, timeout=900, exp_send=1, exp_loopnum=0, oneshot=False, event=None, web_check=True, exp_error=False):
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
        if self.kill_pid_by_name(self.ssh_host(), "virt-who") is False:
            raise FailException("Failed to stop and clean virt-who process")

    def vw_gen_json(self, hypervisors, guests):
        virtwho = {}
        for i in range(hypervisors):
            guest_list = []
            for c in range(guests):
                guest_list.append({
                    "guestId": str(uuid.uuid4()),
                    "state": 1,
                    "attributes": {
                        "active": 1,
                        "virtWhoType": "esx"
                    }
                })
            virtwho[str(uuid.uuid4()).replace("-", ".")] = guest_list
        return virtwho

    def vw_rhsm_associate(self, data, host_uuid, guest_uuid, uid=None):
        hypervisor_config = self.get_hypervisor_config(uid)
        register_config = self.get_register_config()
        mode = hypervisor_config['type']
        owner = register_config['owner']
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
                ret, output = self.runcmd("cat /tmp/vw.log", self.ssh_host())
                if output is not None and output != "":
                    encrypted_value  = output.strip()
                    logger.info("Succeeded to get encrypted_password with %s option: %s" % (option,encrypted_value))
                    return encrypted_value
                else: raise FailException("Failed to run virt-who-password")
            else: raise FailException("Failed to run virt-who-password")
    
    def vw_pending_job_cancel(self, job_ids):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            self.stage_job_delete(self.ssh_host(), register_config, job_ids)
        if "satellite" in register_type:
            logger.warning("not support to delete job currently")

    def vw_web_host_delete(self, host_name, host_uuid, retry=True):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            self.stage_consumer_delete(self.ssh_host(), register_config, host_name, host_uuid, retry)
        elif "satellite" in register_type:
            self.satellite_host_delete(self.ssh_host(), register_config, host_name, host_uuid, retry)
        else:
            raise FailException("Unkonwn server type for web host delete")

    def vw_web_attach(self, host_name, host_uuid, pool_id, quantity=1):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            self.stage_consumer_attach(self.ssh_host(), register_config, host_name, host_uuid, pool_id)
        elif "satellite" in register_type:
            self.satellite_host_attach(self.ssh_host(), register_config, host_name, host_uuid, pool_id, quantity)
        else:
            raise FailException("Unkonwn server type for web attach")

    def vw_web_unattach(self, host_name, host_uuid):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            self.stage_consumer_unattach(self.ssh_host(), register_config, host_name, host_uuid)
        elif "satellite" in register_type:
            self.satellite_host_unattach(self.ssh_host(), register_config, host_name, host_uuid)
        else:
            raise FailException("Unkonwn server type for web unattach")

    def vw_web_associate(self, host_name, host_uuid, guest_name, guest_uuid):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            return self. stage_consumer_associate(self.ssh_host(), register_config, host_name, host_uuid, guest_uuid)
        elif "satellite" in register_type:
            return self.satellite_host_associate(self.ssh_host(), register_config, host_name, host_uuid, guest_name, guest_uuid)
        else:
            raise FailException("Unkonwn server type for web associate")

    def vw_web_registered_id(self, host_name, host_uuid):
        register_config = self.get_register_config()
        register_type = register_config['type']
        if "stage" in register_type:
            registered_id = self.stage_consumer_uuid(self.ssh_host(), register_config, host_name, host_uuid)
        if "satellite" in register_type:
            registered_id = self.satellite_host_id(self.ssh_host(), register_config, host_name, host_uuid)
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
            ret, output = self.runcmd(cmd, self.ssh_host(), debug=False)
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
