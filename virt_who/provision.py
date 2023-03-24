from virt_who import *
from virt_who.base import Base
from virt_who.register import Register


class Provision(Register):
    # ****************************************
    # Provision Entry
    # ****************************************
    def provision_validation(self):
        if deploy.trigger.type == "trigger-rhev":
            if not deploy.trigger.rhev_iso:
                raise FailException("no rhev iso url")
        elif deploy.trigger.type == "trigger-gating":
            logger.info("gating tests should be trigger by umb")
        else:
            if not deploy.trigger.rhel_compose:
                raise FailException("no rhel compose_id")
        if deploy.trigger.type == "trigger-brew":
            if not deploy.trigger.brew_package:
                raise FailException("no brew package url")
        if deploy.trigger.type == "trigger-upstream":
            if not deploy.trigger.virtwho_upstream:
                raise FailException("no upstream git url")
        if deploy.trigger.type == "trigger-multiarch":
            if not deploy.trigger.arch_type:
                raise FailException("no arch defined")
        if not deploy.trigger.hypervisor_list:
            raise FailException("no hypervisor list")
        if not deploy.trigger.register_list:
            raise FailException("no register list")
        if self.beaker_kinit() is False:
            raise FailException("beaker client is not working")

    def hypervisors_validation(self):
        hypervisor_list = deploy.trigger.hypervisor_list.lower()
        remote_modes = list()
        local_modes = list()
        if "esx" in hypervisor_list:
            remote_modes.append("esx")
        if "xen" in hypervisor_list:
            remote_modes.append("xen")
        if "hyperv" in hypervisor_list:
            remote_modes.append("hyperv")
        if "rhevm" in hypervisor_list:
            remote_modes.append("rhevm")
        if "kubevirt" in hypervisor_list:
            remote_modes.append("kubevirt")
        if "libvirt-remote" in hypervisor_list:
            remote_modes.append("libvirt-remote")
        if "ahv" in hypervisor_list:
            remote_modes.append("ahv")
        if "libvirt-local" in hypervisor_list:
            local_modes.append("libvirt-local")
        if "vdsm" in hypervisor_list:
            local_modes.append("vdsm")
        return remote_modes, local_modes

    def ci_msg_parser(self):
        env = dict()
        ci_msg_content = self.get_exported_param("CI_MESSAGE")
        if ci_msg_content:
            msg = json.loads(ci_msg_content)
            if "info" in msg.keys():
                build_id = msg["info"]["build_id"]
                task_id = msg["info"]["task_id"]
                owner_name = msg["info"]["owner_name"]
                source = msg["info"]["source"]
            else:
                build_id = re.findall(r'"build_id":(.*?),', ci_msg_content)[-1].strip()
                task_id = re.findall(r'"task_id":(.*?),', ci_msg_content)[-1].strip()
                owner_name = re.findall(r'"owner_name":(.*?),', ci_msg_content)[
                    -1
                ].strip()
                source = re.findall(r'"source":(.*?),', ci_msg_content)[-1].strip()
            brew_build_url = "{0}/brew/buildinfo?buildID={1}".format(
                deploy.repo.brew, build_id
            )
        else:
            brew_build_url = self.get_exported_param("BREW_BUILD_URL")
            build_id = re.findall(r"buildID=(.*?)$", brew_build_url)[-1]
            task_id = build_id
            owner_name = "wpoteat"
            source = ""
        cmd = "curl -k -s -i {0}".format(brew_build_url)
        output = os.popen(cmd).read()
        pkg_url = re.findall(
            r'<a href="https://(.*?).noarch.rpm">download</a>', output
        )[-1]
        items = pkg_url.split("/")
        rhel_release = items[3]
        rhel_compose = self.get_exported_param("RHEL_COMPOSE")
        if not rhel_compose:
            base_url = deploy.repo.rhel_base
            if "rhel-9" in rhel_release:
                url = "{0}/rhel-9/nightly/RHEL-9/latest-RHEL-9/COMPOSE_ID".format(
                    base_url
                )
            if "rhel-8" in rhel_release:
                url = "{0}/rhel-8/nightly/RHEL-8/latest-RHEL-8/COMPOSE_ID".format(
                    base_url
                )
            if "rhel-7" in rhel_release:
                url = "{0}/rhel-7/rel-eng/RHEL-7/latest-RHEL-7/COMPOSE_ID".format(
                    base_url
                )
            if "rhel-6" in rhel_release:
                url = "{0}/rel-eng/latest-RHEL-6/COMPOSE_ID".format(base_url)
            cmd = "curl -s -k -L {0}".format(url)
            rhel_compose = os.popen(cmd).read().strip()
        if not pkg_url:
            raise FailException("no package url found")
        if not rhel_compose:
            raise FailException("no rhel compose found")
        env["build_id"] = build_id
        env["task_id"] = task_id
        env["owner_name"] = owner_name
        env["source"] = source
        env["pkg_url"] = "http://" + pkg_url + ".noarch.rpm"
        env["pkg_name"] = items[5]
        env["pkg_version"] = items[6]
        env["pkg_release"] = items[7]
        env["pkg_arch"] = items[8]
        env["pkg_nvr"] = items[9]
        env["rhel_release"] = rhel_release
        env["rhel_compose"] = rhel_compose
        return env

    def provision_start(self):
        self.provision_validation()
        if deploy.trigger.type == "trigger-gating":
            env = self.ci_msg_parser()
            rhel_compose = env["rhel_compose"]
            for key, value in env.items():
                logger.info("{0}: {1}".format(key, value))
        else:
            rhel_compose = deploy.trigger.rhel_compose
        remote_modes, local_modes = self.hypervisors_validation()
        q = queue.Queue()
        results = list()
        threads = list()
        threads.append(
            threading.Thread(target=self.provision_register_servers, args=(q,))
        )
        if len(remote_modes) > 0:
            threads.append(
                threading.Thread(
                    target=self.provision_remote_guests, args=(q, remote_modes)
                )
            )
        # if deploy.trigger.type == "trigger-rhev":
        #     threads.append(
        #         threading.Thread(
        #             target=self.provision_rhev_host,
        #             args=(q,)
        #         )
        #     )
        if deploy.trigger.type == "trigger-multiarch":
            threads.append(
                threading.Thread(
                    target=self.provision_arch_host, args=(q, rhel_compose)
                )
            )
        else:
            if len(remote_modes) > 0:
                threads.append(
                    threading.Thread(
                        target=self.provision_docker_hosts,
                        args=(q, rhel_compose, remote_modes),
                    )
                )
            if "libvirt-local" in local_modes:
                threads.append(
                    threading.Thread(
                        target=self.provision_libvirt_local_host, args=(q, rhel_compose)
                    )
                )
            # if "vdsm" in local_modes:
            #     threads.append(
            #         threading.Thread(
            #             target=self.provision_vdsm_host,
            #             args=(q, rhel_compose)
            #         )
            #     )
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        while not q.empty():
            results.append(q.get())
        for item in results:
            logger.info(item)
        register_servers, virtwho_hosts, guests = self.provision_report(results)
        self.jenkins_job_scheduler(register_servers, virtwho_hosts, guests)

    def provision_report(self, data):
        register_servers = dict()
        hosts = dict()
        guests = dict()
        for item in data:
            if item[0] == "provision_register_servers":
                register_servers.update(item[1])
            if item[0] == "provision_remote_guests":
                guests.update(item[1])
            if item[0] == "provision_docker_hosts":
                hosts.update(item[1])
            if item[0] == "provision_rhev_host":
                if "virtwho-host-ip" in item[1].keys():
                    hosts["virtwho-host-ip"] = item[1]["virtwho-host-ip"]
                if "vdsm-guest-ip" in item[2].keys():
                    guests["vdsm-guest-ip"] = item[2]["vdsm-guest-ip"]
            if item[0] == "provision_arch_host":
                if "virtwho-host-ip" in item[1].keys():
                    hosts["virtwho-host-ip"] = item[1]["virtwho-host-ip"]
            if item[0] == "provision_libvirt_local_host":
                if "libvirt-local-host-ip" in item[1].keys():
                    hosts["libvirt-local-host-ip"] = item[1]["libvirt-local-host-ip"]
                if "libvirt-local-guest-ip" in item[2].keys():
                    guests["libvirt-local-guest-ip"] = item[2]["libvirt-local-guest-ip"]
            if item[0] == "provision_vdsm_host":
                if "vdsm-host-ip" in item[1].keys():
                    hosts["vdsm-host-ip"] = item[1]["vdsm-host-ip"]
                if "vdsm-guest-ip" in item[2].keys():
                    guests["vdsm-guest-ip"] = item[2]["vdsm-guest-ip"]
        return register_servers, hosts, guests

    def provision_register_servers(self, q):
        logger.info("Start to provision register servers")
        func_name = sys._getframe().f_code.co_name
        register_list = deploy.trigger.register_list.lower()
        satellite_server = self.get_exported_param("SATELLITE_SERVER")
        servers_ip = dict()
        sat_list = list()
        for register_type in register_list.strip().split(","):
            if "stage" in register_type:
                servers_ip["stage"] = deploy.stage.server
            if "satellite" in register_type:
                sat_list.append(register_type)
                if satellite_server:
                    servers_ip[register_type] = satellite_server
        if not satellite_server:
            job_passed = self.satellite_machines(sat_list)
            if job_passed:
                sat_queue = queue.Queue()
                sat_results = []
                sat_threads = []
                for sat_type, sat_host in job_passed.items():
                    sat_threads.append(
                        threading.Thread(
                            target=self.satellite_setup,
                            args=(sat_queue, sat_type, sat_host),
                        )
                    )
                for t in sat_threads:
                    t.start()
                for t in sat_threads:
                    t.join()
                while not sat_queue.empty():
                    sat_results.append(sat_queue.get())
                for item in sat_results:
                    servers_ip[item[0]] = item[1]
        q.put((func_name, servers_ip))

    def provision_remote_guests(self, q, remote_modes):
        logger.info("Start to provision remote hypervisor and guests")
        func_name = sys._getframe().f_code.co_name
        conf_guests = dict()
        mode_queue = queue.Queue()
        mode_results = []
        mode_threads = []
        for mode_type in remote_modes:
            mode_type = "%s-guest-ip" % mode_type
            if "libvirt-remote" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_libvirt_remote_setup,
                        args=(mode_queue, mode_type),
                    )
                )
            if "rhevm" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_rhevm_setup, args=(mode_queue, mode_type)
                    )
                )
            if "xen" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_xen_setup, args=(mode_queue, mode_type)
                    )
                )
            if "hyperv" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_hyperv_setup, args=(mode_queue, mode_type)
                    )
                )
            if "ahv" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_ahv_setup, args=(mode_queue, mode_type)
                    )
                )
            if "esx" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_esx_setup, args=(mode_queue, mode_type)
                    )
                )
            if "kubevirt" in mode_type:
                mode_threads.append(
                    threading.Thread(
                        target=self.guest_kubevirt_setup, args=(mode_queue, mode_type)
                    )
                )
        for t in mode_threads:
            t.start()
        for t in mode_threads:
            t.join()
        while not mode_queue.empty():
            mode_results.append(mode_queue.get())
        for item in mode_results:
            conf_guests[item[0]] = item[1]
        q.put((func_name, conf_guests))

    # def provision_rhev_host(self, q):
    #     func_name = sys._getframe().f_code.co_name
    #     logger.info("Start to provision rhev host and guest")
    #     rhev_iso = deploy.trigger.rhev_iso
    #     rhev_host = deploy.vdsm.master
    #     rhev_user = deploy.vdsm.master_user
    #     rhev_passwd = deploy.vdsm.master_passwd
    #     conf_host = dict()
    #     conf_guest = dict()
    #     ssh_rhev = {
    #         "host": rhev_host,
    #         "username": rhev_user,
    #         "password": rhev_passwd
    #     }
    #     self.rhev_install_by_grub(ssh_rhev, rhev_iso)
    #     self.system_init("ci-host-rhev", ssh_rhev)
    #     self.ssh_no_passwd_access(ssh_rhev)
    #     self.install_epel_packages(ssh_rhev)
    #     guest_ip = self.guest_vdsm_setup(ssh_rhev)
    #     conf_host["virtwho-host-ip"] = rhev_host
    #     conf_guest["vdsm-guest-ip"] = guest_ip
    #     q.put((func_name, conf_host, conf_guest))

    def provision_arch_host(self, q, compose_id):
        func_name = sys._getframe().f_code.co_name
        logger.info("Start to provision multiarch host")
        conf_host = dict()
        arch_type = deploy.trigger.arch_type
        host_ip = self.beaker_compose_setup(compose_id, arch_type.strip())
        conf_host["virtwho-host-ip"] = host_ip
        username = deploy.beaker.default_user
        password = deploy.beaker.default_passwd
        ssh_host = {"host": host_ip, "username": username, "password": password}
        self.system_init("ci-host-arch", ssh_host)
        self.ssh_no_passwd_access(ssh_host)
        self.install_base_packages(ssh_host)
        q.put((func_name, conf_host))

    def provision_docker_hosts(self, q, compose_id, remote_modes):
        logger.info("Start to provision virt-who docker hosts")
        func_name = sys._getframe().f_code.co_name
        conf_hosts = self.docker_compose_setup(compose_id, remote_modes)
        q.put((func_name, conf_hosts))

    def provision_libvirt_local_host(self, q, compose_id):
        logger.info("Start to provision local libvirt host and its guest")
        func_name = sys._getframe().f_code.co_name
        conf_host = dict()
        conf_guest = dict()
        local_host = deploy.libvirt.local
        local_user = deploy.libvirt.local_user
        local_passwd = deploy.libvirt.local_passwd
        ssh_libvirt = {
            "host": local_host,
            "username": local_user,
            "password": local_passwd,
        }
        self.rhel_install_by_grub(ssh_libvirt, compose_id)
        self.system_init("ci-host-libvirt-local", ssh_libvirt)
        self.ssh_no_passwd_access(ssh_libvirt)
        guest_ip = self.guest_libvirt_local_setup(ssh_libvirt)
        conf_host["libvirt-local-host-ip"] = local_host
        conf_guest["libvirt-local-guest-ip"] = guest_ip
        q.put((func_name, conf_host, conf_guest))

    # def provision_vdsm_host(self, q, compose_id):
    #     logger.info("Start to provision vdsm host and its guest")
    #     func_name = sys._getframe().f_code.co_name
    #     conf_host = dict()
    #     conf_guest = dict()
    #     master = deploy.vdsm.master
    #     master_user = deploy.vdsm.master_user
    #     master_passwd = deploy.vdsm.master_passwd
    #     ssh_vdsm = {
    #         "host": master,
    #         "username": master_user,
    #         "password": master_passwd
    #     }
    #     self.rhel_install_by_grub(ssh_vdsm, compose_id)
    #     self.system_init("ci-host-vdsm", ssh_vdsm)
    #     self.ssh_no_passwd_access(ssh_vdsm)
    #     guest_ip = self.guest_vdsm_setup(ssh_vdsm)
    #     conf_host["vdsm-host-ip"] = master
    #     conf_guest["vdsm-guest-ip"] = guest_ip
    #     q.put((func_name, conf_host, conf_guest))

    # *************************************************
    # Jenkins Job Scheduler
    # *************************************************
    def jenkins_job_scheduler(self, register_servers, virtwho_hosts, guests):
        trigger_type = deploy.trigger.type
        if trigger_type == "trigger-rhev" or trigger_type == "trigger-multiarch":
            for key, value in guests.items():
                guest_ip = value
                job_name = ""
                if "esx" in key:
                    job_name = "runtest-esx"
                if "xen" in key:
                    job_name = "runtest-xen"
                if "hyperv" in key:
                    job_name = "runtest-hyperv"
                if "rhevm" in key:
                    job_name = "runtest-rhevm"
                if "kubevirt" in key:
                    job_name = "runtest-kubevirt"
                if "ahv" in key:
                    job_name = "runtest-ahv"
                if "libvirt-remote" in key:
                    job_name = "runtest-libvirt-remote"
                if "libvirt-local" in key:
                    job_name = "runtest-libvirt-local"
                if "vdsm" in key:
                    job_name = "runtest-vdsm"
                if (
                    len(register_servers) > 0
                    and "virtwho-host-ip" in virtwho_hosts.keys()
                    and guest_ip != ""
                    and job_name != ""
                ):
                    host_ip = virtwho_hosts["virtwho-host-ip"]
                    self.jenkins_job_start(
                        register_servers, host_ip, guest_ip, job_name
                    )
        else:
            results = list()
            threads = list()
            for key, value in virtwho_hosts.items():
                host_ip = value
                job_name = ""
                guest_ip = ""
                if "esx" in key and "esx-guest-ip" in guests.keys():
                    job_name = "runtest-esx"
                    guest_ip = guests["esx-guest-ip"]
                if "xen" in key and "xen-guest-ip" in guests.keys():
                    job_name = "runtest-xen"
                    guest_ip = guests["xen-guest-ip"]
                if "hyperv" in key and "hyperv-guest-ip" in guests.keys():
                    job_name = "runtest-hyperv"
                    guest_ip = guests["hyperv-guest-ip"]
                if "rhevm" in key and "rhevm-guest-ip" in guests.keys():
                    job_name = "runtest-rhevm"
                    guest_ip = guests["rhevm-guest-ip"]
                if "kubevirt" in key and "kubevirt-guest-ip" in guests.keys():
                    job_name = "runtest-kubevirt"
                    guest_ip = guests["kubevirt-guest-ip"]
                if "ahv" in key and "ahv-guest-ip" in guests.keys():
                    job_name = "runtest-ahv"
                    guest_ip = guests["ahv-guest-ip"]
                if (
                    "libvirt-remote" in key
                    and "libvirt-remote-guest-ip" in guests.keys()
                ):
                    job_name = "runtest-libvirt-remote"
                    guest_ip = guests["libvirt-remote-guest-ip"]
                if "libvirt-local" in key and "libvirt-local-guest-ip" in guests.keys():
                    job_name = "runtest-libvirt-local"
                    guest_ip = guests["libvirt-local-guest-ip"]
                if "vdsm" in key and "vdsm-guest-ip" in guests.keys():
                    job_name = "runtest-vdsm"
                    guest_ip = guests["vdsm-guest-ip"]
                if (
                    len(register_servers) > 0
                    and host_ip != ""
                    and guest_ip != ""
                    and job_name != ""
                ):
                    threads.append(
                        threading.Thread(
                            target=self.jenkins_job_start,
                            args=(register_servers, host_ip, guest_ip, job_name),
                        )
                    )
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    def jenkins_register_config(self, register_type, register_server, job_name):
        if "stage" in register_type:
            server = deploy.stage.server
            api = "https://{0}/subscription".format(server)
            if "esx" in job_name:
                username = deploy.stage.esx_user
                password = deploy.stage.esx_passwd
                owner = deploy.stage.esx_org
                env = deploy.stage.esx_org
            if "xen" in job_name:
                username = deploy.stage.xen_user
                password = deploy.stage.xen_passwd
                owner = deploy.stage.xen_org
                env = deploy.stage.xen_org
            if "hyperv" in job_name:
                username = deploy.stage.hyperv_user
                password = deploy.stage.hyperv_passwd
                owner = deploy.stage.hyperv_org
                env = deploy.stage.hyperv_org
            if "rhevm" in job_name:
                username = deploy.stage.rhevm_user
                password = deploy.stage.rhevm_passwd
                owner = deploy.stage.rhevm_org
                env = deploy.stage.rhevm_org
            if "kubevirt" in job_name:
                username = deploy.stage.kubevirt_user
                password = deploy.stage.kubevirt_passwd
                owner = deploy.stage.kubevirt_org
                env = deploy.stage.kubevirt_org
            # if "vdsm" in job_name:
            #     username = deploy.stage.vdsm_user
            #     password = deploy.stage.vdsm_passwd
            #     owner = deploy.stage.vdsm_org
            #     env = deploy.stage.vdsm_org
            if "libvirt-remote" in job_name:
                username = deploy.stage.libvirt_remote_user
                password = deploy.stage.libvirt_remote_passwd
                owner = deploy.stage.libvirt_remote_org
                env = deploy.stage.libvirt_remote_org
            if "libvirt-local" in job_name:
                username = deploy.stage.libvirt_local_user
                password = deploy.stage.libvirt_local_passwd
                owner = deploy.stage.libvirt_local_org
                env = deploy.stage.libvirt_local_org
            if "ahv" in job_name:
                username = deploy.stage.ahv_user
                password = deploy.stage.ahv_passwd
                owner = deploy.stage.ahv_org
                env = deploy.stage.ahv_org
            if deploy.trigger.type == "trigger-gating":
                username = deploy.stage.gate_user
                password = deploy.stage.gate_passwd
                owner = deploy.stage.gate_org
                env = deploy.stage.gate_org
            register_config = {
                "type": register_type,
                "server": server,
                "username": username,
                "password": password,
                "owner": owner,
                "env": env,
                "ssh_user": "",
                "ssh_passwd": "",
                "api": api,
            }
            return register_config
        if "satellite" in register_type:
            server = register_server
            api = "https://{0}".format(server)
            ssh_user = deploy.beaker.default_user
            ssh_passwd = deploy.beaker.default_passwd
            username = deploy.satellite.admin_user
            password = deploy.satellite.admin_passwd
            owner = deploy.satellite.default_org
            env = deploy.satellite.default_env
            ssh_sat = {"host": server, "username": ssh_user, "password": ssh_passwd}
            register_config = {
                "type": register_type,
                "server": server,
                "username": username,
                "password": password,
                "owner": owner,
                "env": env,
                "ssh_user": ssh_user,
                "ssh_passwd": ssh_passwd,
                "api": api,
                "ssh_sat": ssh_sat,
            }
            return register_config

    def jenkins_hypervisor_config(self, host_ip, guest_ip, job_name):
        trigger_type = deploy.trigger.type
        if trigger_type == "trigger-rhev":
            host_user = deploy.vdsm.master_user
            host_passwd = deploy.vdsm.master_passwd
        elif trigger_type == "trigger-multiarch":
            host_user = deploy.beaker.default_user
            host_passwd = deploy.beaker.default_user
        else:
            host_user = deploy.docker.container_user
            host_passwd = deploy.docker.container_passwd
        hypervisor_ssh_ip = ""
        hypervisor_ssh_user = ""
        hypervisor_ssh_passwd = ""
        hypervisor_config_file = ""
        if "esx" in job_name:
            hypervisor_type = "esx"
            hypervisor_server = deploy.vcenter.ip
            hypervisor_user = deploy.vcenter.admin_user
            hypervisor_passwd = deploy.vcenter.admin_passwd
            hypervisor_ssh_ip = deploy.vcenter.ssh_ip
            hypervisor_ssh_user = deploy.vcenter.ssh_user
            hypervisor_ssh_passwd = deploy.vcenter.ssh_passwd
            guest_name = deploy.vcenter.guest_name
            guest_user = deploy.vcenter.guest_user
            guest_passwd = deploy.vcenter.guest_passwd
        if "xen" in job_name:
            hypervisor_type = "xen"
            hypervisor_server = deploy.xen.master
            hypervisor_user = deploy.xen.master_user
            hypervisor_passwd = deploy.xen.master_passwd
            guest_name = deploy.xen.guest_name
            guest_user = deploy.xen.guest_user
            guest_passwd = deploy.xen.guest_passwd
        if "hyperv" in job_name:
            hypervisor_type = "hyperv"
            hypervisor_server = deploy.hyperv.master
            hypervisor_user = deploy.hyperv.master_user
            hypervisor_passwd = deploy.hyperv.master_passwd
            guest_name = deploy.hyperv.guest_name
            guest_user = deploy.hyperv.guest_user
            guest_passwd = deploy.hyperv.guest_passwd
        if "ahv" in job_name:
            hypervisor_type = "ahv"
            hypervisor_server = deploy.ahv.master
            hypervisor_user = deploy.ahv.master_user
            hypervisor_passwd = deploy.ahv.master_passwd
            guest_name = deploy.ahv.guest_name
            guest_user = deploy.ahv.guest_user
            guest_passwd = deploy.ahv.guest_passwd
        if "kubevirt" in job_name:
            hypervisor_type = "kubevirt"
            hypervisor_server = deploy.kubevirt.endpoint
            hypervisor_user = ""
            hypervisor_passwd = deploy.kubevirt.token
            guest_name = deploy.kubevirt.guest_name
            guest_user = deploy.kubevirt.guest_user
            guest_passwd = deploy.kubevirt.guest_passwd
            hypervisor_config_file = deploy.kubevirt.kube_config_file
        if "rhevm" in job_name:
            hypervisor_type = "rhevm"
            rhevm_ip = deploy.rhevm.rhevm_ip
            hypervisor_ssh_user = deploy.rhevm.rhevm_ssh_user
            hypervisor_ssh_passwd = deploy.rhevm.rhevm_ssh_passwd
            ssh_rhevm = {
                "host": rhevm_ip,
                "username": hypervisor_ssh_user,
                "password": hypervisor_ssh_passwd,
            }
            hypervisor_server = self.rhevm_admin_get(ssh_rhevm)
            hypervisor_user = deploy.rhevm.rhevm_admin_user
            hypervisor_passwd = deploy.rhevm.rhevm_admin_passwd
            guest_name = deploy.rhevm.guest_name
            guest_user = deploy.rhevm.guest_user
            guest_passwd = deploy.rhevm.guest_passwd
        # if "vdsm" in job_name:
        #     hypervisor_type = "vdsm"
        #     rhevm_ip =  deploy.vdsm.rhevm_ip
        #     hypervisor_ssh_user = deploy.vdsm.rhevm_ssh_user
        #     hypervisor_ssh_passwd = deploy.vdsm.rhevm_ssh_passwd
        #     ssh_rhevm = {'host':rhevm_ip,'username':hypervisor_ssh_user,'password':hypervisor_ssh_passwd}
        #     hypervisor_server = self.rhevm_admin_get(ssh_rhevm)
        #     hypervisor_user = deploy.vdsm.rhevm_admin_user
        #     hypervisor_passwd = deploy.vdsm.rhevm_admin_passwd
        #     host_user = deploy.vdsm.master_user
        #     host_passwd = deploy.vdsm.master_passwd
        #     guest_name = deploy.vdsm.guest_name
        #     guest_user = deploy.vdsm.guest_user
        #     guest_passwd = deploy.vdsm.guest_passwd
        if "libvirt-remote" in job_name:
            hypervisor_type = "libvirt-remote"
            hypervisor_server = deploy.libvirt.remote
            hypervisor_user = deploy.libvirt.remote_user
            hypervisor_passwd = deploy.libvirt.remote_passwd
            guest_name = deploy.libvirt.guest_name
            guest_user = deploy.libvirt.guest_user
            guest_passwd = deploy.libvirt.guest_passwd
        if "libvirt-local" in job_name:
            hypervisor_type = "libvirt-local"
            hypervisor_server = ""
            hypervisor_user = ""
            hypervisor_passwd = ""
            host_user = deploy.libvirt.local_user
            host_passwd = deploy.libvirt.local_passwd
            guest_name = deploy.libvirt.guest_name
            guest_user = deploy.libvirt.guest_user
            guest_passwd = deploy.libvirt.guest_passwd
        ssh_host = {"host": host_ip, "username": host_user, "password": host_passwd}
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        hypervisor_config = {
            "hypervisor_type": hypervisor_type,
            "hypervisor_server": hypervisor_server,
            "hypervisor_user": hypervisor_user,
            "hypervisor_passwd": hypervisor_passwd,
            "hypervisor_ssh_ip": hypervisor_ssh_ip,
            "hypervisor_ssh_user": hypervisor_ssh_user,
            "hypervisor_ssh_passwd": hypervisor_ssh_passwd,
            "hypervisor_config_file": hypervisor_config_file,
            "host_ip": host_ip,
            "host_user": host_user,
            "host_passwd": host_passwd,
            "guest_ip": guest_ip,
            "guest_name": guest_name,
            "guest_user": guest_user,
            "guest_passwd": guest_passwd,
            "ssh_host": ssh_host,
            "ssh_guest": ssh_guest,
        }
        return hypervisor_config

    def jenkins_virtwho_install(self, register_type, ssh_host):
        trigger_type = deploy.trigger.type
        rhel_ver = self.rhel_version(ssh_host)
        if rhel_ver == "6":
            cmd = "dbus-uuidgen > /var/lib/dbus/machine-id"
            ret, output = self.runcmd(cmd, ssh_host)
        if rhel_ver == "8":
            cmd = "localectl set-locale en_US.utf8; source /etc/profile.d/lang.sh"
            ret, output = self.runcmd(cmd, ssh_host)
        cmd = (
            "rm -rf /var/lib/rpm/__db*; mv /var/lib/rpm /var/lib/rpm.old; rpm --initdb;"
            "rm -rf /var/lib/rpm; mv /var/lib/rpm.old /var/lib/rpm;"
            "rm -rf /var/lib/yum/history/*.sqlite; rpm -v --rebuilddb"
        )
        ret, output = self.runcmd(cmd, ssh_host)
        if trigger_type == "trigger-brew":
            pkg_url = deploy.trigger.brew_package
            self.install_virtwho_by_url(ssh_host, pkg_url)
        elif trigger_type == "trigger-gating":
            env = self.ci_msg_parser()
            pkg_url = env["pkg_url"]
            self.install_virtwho_by_url(ssh_host, pkg_url)
        elif trigger_type == "trigger-upstream":
            self.install_virtwho_upstream(ssh_host)
        elif trigger_type == "trigger-satellite":
            self.install_virtwho_sattools(ssh_host, register_type)
        elif trigger_type == "trigger-rhev":
            logger.info("virt-who is installed by rhev default")
        else:
            cmd = "yum remove -y virt-who; yum install -y virt-who"
            ret, output = self.runcmd(cmd, ssh_host)
        ret, output = self.runcmd("rpm -qa virt-who", ssh_host)
        if "virt-who" not in output:
            raise FailException("virt-who package is not installed for testing")
        logger.info("virt-who package is installed: {0}".format(output.strip()))
        self.runcmd("sed -i '/^#.*;/d' /etc/virt-who.conf", ssh_host)
        self.system_unregister(ssh_host)

    def jenkins_job_init(self, register_type, register_config, ssh_host, ssh_guest):
        self.jenkins_virtwho_install(register_type, ssh_host)
        if "stage" in register_type:
            self.stage_consumer_clean(ssh_host, register_config)

    def jenkins_parameter(self, hypervisor_config, register_config, virtwho_build):
        parameter = list()
        parameter.append("-d TRIGGER_TYPE={0}".format(deploy.trigger.type))
        parameter.append("-d VIRTWHO_BUILD={0}".format(virtwho_build))
        parameter.append("-d VIRTWHO_HOST_IP={0}".format(hypervisor_config["host_ip"]))
        parameter.append(
            "-d VIRTWHO_HOST_USER={0}".format(hypervisor_config["host_user"])
        )
        parameter.append(
            "-d VIRTWHO_HOST_PASSWD={0}".format(hypervisor_config["host_passwd"])
        )
        parameter.append(
            "-d HYPERVISOR_TYPE={0}".format(hypervisor_config["hypervisor_type"])
        )
        parameter.append(
            "-d HYPERVISOR_SERVER={0}".format(hypervisor_config["hypervisor_server"])
        )
        parameter.append(
            "-d HYPERVISOR_USERNAME={0}".format(hypervisor_config["hypervisor_user"])
        )
        parameter.append(
            "-d HYPERVISOR_PASSWORD={0}".format(hypervisor_config["hypervisor_passwd"])
        )
        parameter.append(
            "-d HYPERVISOR_SSH_IP={0}".format(hypervisor_config["hypervisor_ssh_ip"])
        )
        parameter.append(
            "-d HYPERVISOR_SSH_USER={0}".format(
                hypervisor_config["hypervisor_ssh_user"]
            )
        )
        parameter.append(
            "-d HYPERVISOR_SSH_PASSWD={0}".format(
                hypervisor_config["hypervisor_ssh_passwd"]
            )
        )
        parameter.append(
            "-d HYPERVISOR_CONFIG_FILE={0}".format(
                hypervisor_config["hypervisor_config_file"]
            )
        )
        parameter.append("-d GUEST_IP={0}".format(hypervisor_config["guest_ip"]))
        parameter.append("-d GUEST_NAME={0}".format(hypervisor_config["guest_name"]))
        parameter.append("-d GUEST_USER={0}".format(hypervisor_config["guest_user"]))
        parameter.append(
            "-d GUEST_PASSWD={0}".format(hypervisor_config["guest_passwd"])
        )
        parameter.append("-d REGISTER_TYPE={0}".format(register_config["type"]))
        parameter.append("-d REGISTER_SERVER={0}".format(register_config["server"]))
        parameter.append("-d REGISTER_OWNER={0}".format(register_config["owner"]))
        parameter.append("-d REGISTER_ENV={0}".format(register_config["env"]))
        parameter.append(
            "-d REGISTER_ADMIN_USER={0}".format(register_config["username"])
        )
        parameter.append(
            "-d REGISTER_ADMIN_PASSWD={0}".format(register_config["password"])
        )
        parameter.append("-d REGISTER_SSH_USER={0}".format(register_config["ssh_user"]))
        parameter.append(
            "-d REGISTER_SSH_PASSWD={0}".format(register_config["ssh_passwd"])
        )
        if deploy.trigger.type == "trigger-gating":
            env = self.ci_msg_parser()
            rhel_compose = env["rhel_compose"]
            build_id = env["build_id"]
            task_id = env["task_id"]
            pkg_nvr = env["pkg_nvr"]
            owner_name = env["owner_name"]
            source = env["source"]
            parameter.append("-d RHEL_COMPOSE={0}".format(rhel_compose))
            parameter.append("-d BREW_BUILD_ID={0}".format(build_id))
            parameter.append("-d BREW_TASK_ID={0}".format(task_id))
            parameter.append("-d PACKAGE_NVR={0}".format(pkg_nvr))
            parameter.append("-d OWNER_NAME={0}".format(owner_name))
            parameter.append("-d SOURCE={0}".format(source))
        else:
            node_label = self.get_exported_param("NODE_LABEL")
            parameter.append("-d NODE_LABEL={0}".format(node_label))
            provision_ini = self.get_exported_param("PROVISION_INI")
            parameter.append("-d PROVISION_INI={0}".format(provision_ini))
            parameter.append("-d RHEL_COMPOSE={0}".format(deploy.trigger.rhel_compose))
            parameter.append(
                "-d RHEL_COMPOSE_PATH={0}".format(
                    self.get_exported_param("RHEL_COMPOSE_PATH")
                )
            )
            parameter.append("-d TRIGGER_LEVEL={0}".format(deploy.trigger.level))
            parameter.append(
                "-d POLARION_REPORT={0}".format(
                    self.get_exported_param("POLARION_REPORT")
                )
            )
            parameter.append(
                "-d PLANNED_IN={0}".format(self.get_exported_param("PLANNED_IN"))
            )
        data = " ".join(parameter)
        return data

    def jenkins_job_start(self, register_servers, host_ip, guest_ip, job_name):
        jenkins_url = deploy.jenkins.url
        jenkins_user = deploy.jenkins.username
        jenkins_passwd = deploy.jenkins.password
        for register_type, register_server in register_servers.items():
            hypervisor_config = self.jenkins_hypervisor_config(
                host_ip, guest_ip, job_name
            )
            register_config = self.jenkins_register_config(
                register_type, register_server, job_name
            )
            ssh_host = hypervisor_config["ssh_host"]
            ssh_guest = hypervisor_config["ssh_guest"]
            self.jenkins_job_init(register_type, register_config, ssh_host, ssh_guest)
            if (
                "kubevirt" in job_name
                and self.pkg_check(ssh_host, "virt-who")[9:15] < "0.24.4"
            ):
                logger.warning(
                    "skip kubevirt testing, it's not available for this virt-who version"
                )
                return False
            if (
                "kubevirt" in job_name
                and self.pkg_check(ssh_host, "virt-who")[9:15] >= "0.24.4"
            ):
                kube_config_file = deploy.kubevirt.kube_config_file
                kube_config_url = deploy.kubevirt.kube_config_url
                cmd = "rm -f {1}; curl -L {0} -o {1}; sync".format(
                    kube_config_url, kube_config_file
                )
                ret, output = self.runcmd(cmd, ssh_host)
            _, virtwho_build = self.runcmd("rpm -qa virt-who", ssh_host)
            virtwho_build = virtwho_build.split(".noarch")[0]
            data = self.jenkins_parameter(
                hypervisor_config, register_config, virtwho_build
            )
            if deploy.trigger.type == "trigger-gating":
                job_name = "runtest-gating"
            cmd = "curl -k -s -i -X POST {0}/job/{1}/buildWithParameters --user {2}:{3} {4}".format(
                deploy.jenkins.url,
                job_name,
                deploy.jenkins.username,
                deploy.jenkins.password,
                data,
            )
            job_tips = "{0}+{1}".format(job_name, register_type)
            is_created = ""
            for i in range(3):
                output = os.popen(cmd).readlines()
                if "Location:" in str(output) or "location:" in str(output):
                    is_created = "yes"
                    break
                logger.info(cmd)
                logger.warning(output)
                logger.warning(
                    "Failed to post data to create jenkinks job, try again..."
                )
                time.sleep(30)
            if is_created != "yes":
                raise FailException("Failed to get jenkins job url")
            job_url = self.jenkins_job_url(output)
            logger.info("JJB({0})-Job URL: {1}".format(job_tips, job_url))
            while self.jenkins_job_is_finished(job_url, job_tips) is False:
                time.sleep(60)

    def jenkins_job_url(self, data):
        for line in data:
            if "Location" in line or "location" in line:
                url = line.split("ocation:")[1].strip()
                break
        cmd = "curl -k -s -u {0}:{1} {2}/api/json".format(
            deploy.jenkins.username, deploy.jenkins.password, url
        )
        output = os.popen(cmd).read()
        while "executable" not in output:
            time.sleep(10)
            output = os.popen(cmd).read()
        data = json.loads(output)
        job_url = data["executable"]["url"]
        return job_url

    def jenkins_job_is_finished(self, job_url, job_tips):
        cmd = "curl -k -s -u {0}:{1} {2}/api/json".format(
            deploy.jenkins.username, deploy.jenkins.password, job_url
        )
        try:
            output = os.popen(cmd).read()
            data = json.loads(output)
            status = data["result"]
            if status == "" or status == "null" or status is None:
                return False
            else:
                logger.info("JJB({0})-Status: {1}".format(job_tips, status))
                return True
        except Exception as e:
            logger.warning("Failed to check job status by: {0}".format(cmd))
            logger.warning(str(e))
            return False

    # *************************************************
    # Re-install host by update grub for rhel and rhev
    # *************************************************
    def install_virtwho_by_url(self, ssh_host, pkg_url):
        if self.url_validation(pkg_url) is False:
            raise FailException("package url is not available")
        cmd = "rm -rf /var/cache/yum/; yum clean all; yum remove -y virt-who"
        ret, output = self.runcmd(cmd, ssh_host)
        cmd = "yum localinstall -y {0}".format(pkg_url)
        ret, output = self.runcmd(cmd, ssh_host)

    def install_virtwho_upstream(self, ssh_host):
        self.rhel_epel_repo(ssh_host)
        git_url = self.get_exported_param("VIRTWHO_UPSTREAM")
        if self.url_validation(git_url) is False:
            raise FailException("VIRTWHO_UPSTREAM is not available")
        git_path = "/tmp/virt-who.git"
        cmd = "rm -rf /tmp/virt-who*; git clone {0} {1}".format(git_url, git_path)
        ret, output = self.runcmd(cmd, ssh_host)
        cmd = "yum clean all; yum install -y tito"
        ret, output = self.runcmd(cmd, ssh_host)
        if ret != 0:
            raise FailException("Failed to install tito")
        cmd = "cd {0}; tito build --rpm --test -i".format(git_path)
        ret, output = self.runcmd(cmd, ssh_host)
        if ret != 0:
            raise FailException("Failed to create virt-who package")

    def install_virtwho_sattools(self, ssh_host, sat_type):
        sat_ver, rhel_ver = self.satellite_version(sat_type)
        self.satellite_qa_dogfood_enable(
            ssh_host, sat_ver, rhel_ver, repo_type="satellite-tools"
        )
        cmd = "rm -rf /var/cache/yum/; yum clean all; yum remove -y virt-who; yum install -y virt-who"
        ret, output = self.runcmd(cmd, ssh_host)

    def install_base_packages(self, ssh_host):
        compose_id = deploy.trigger.rhel_compose
        cmd = "rm -f /var/lib/rpm/__db*; rm -rf /var/lib/yum/history/*.sqlite; rm -rf /var/cache/yum/; rpm --rebuilddb"
        ret, output = self.runcmd(cmd, ssh_host)
        if "RHEL-7" in compose_id:
            cmd = "yum clean all; yum install -y @core @x11 net-tools virt-who wget git nmap \
                    hostname subscription-manager pexpect expect libvirt-python"
        else:
            cmd = "yum clean all; yum install -y @core @base-x net-tools virt-who wget git nmap expect \
                    hostname subscription-manager python3-pexpect python3-libvirt"
        status, output = self.run_loop(
            cmd, ssh_host, desc="install base required packages"
        )
        if status != "Yes":
            raise FailException("Failed to install base required packages")
        logger.info("Succeeded to install base required packages")
        # uninstall cockpit due to bug https://bugzilla.redhat.com/show_bug.cgi?id=1663812
        self.runcmd("rpm -e cockpit cockpit-ws subscription-manager-cockpit", ssh_host)

    def install_epel_packages(self, ssh_host):
        self.rhel_epel_repo(ssh_host)
        cmd = "yum clean all; yum install -y expect tcl wget nmap"
        status, output = self.run_loop(cmd, ssh_host)

    def rhel_epel_repo(self, ssh_host):
        rhel_ver = self.rhel_version(ssh_host)
        repo_epel = deploy.repo.epel
        if rhel_ver == "6":
            epel_url = "{0}/6/x86_64/".format(repo_epel)
        if rhel_ver == "7":
            epel_url = "{0}/7/x86_64/".format(repo_epel)
        if rhel_ver == "8":
            epel_url = "{0}/8/Everything/x86_64/".format(repo_epel)
        cmd = (
            "cat <<EOF > /etc/yum.repos.d/epel.repo\n"
            "[rhel-epel]\n"
            "name=rhel-epel\n"
            "baseurl={0}\n"
            "enabled=1\n"
            "gpgcheck=0\n"
            "EOF"
        ).format(epel_url)
        ret, output = self.runcmd(cmd, ssh_host, desc="enable epel repo")

    def rhel_compose_url(self, compose_id):
        base_url = deploy.repo.rhel_base
        repo_base = ""
        repo_extra = ""
        compose_path = self.get_exported_param("RHEL_COMPOSE_PATH")
        if compose_path:
            if "RHEL-7" in compose_id:
                repo_base = f"{compose_path}/{compose_id}/compose/Server/x86_64/os"
                repo_extra = (
                    f"{compose_path}/{compose_id}/compose/Server-optional/x86_64/os"
                )
            else:
                repo_base = f"{compose_path}/{compose_id}/compose/BaseOS/x86_64/os"
                repo_extra = f"{compose_path}/{compose_id}/compose/AppStream/x86_64/os"
        else:
            if "RHEL-7" in compose_id:
                if "updates" in compose_id:
                    repo_base = "{0}/rhel-7/rel-eng/updates/RHEL-7/{1}/compose/Server/x86_64/os".format(
                        base_url, compose_id
                    )
                    repo_extra = "{0}/rhel-7/rel-eng/updates/RHEL-7/{1}/compose/Server-optional/x86_64/os".format(
                        base_url, compose_id
                    )
                elif ".n" in compose_id:
                    repo_base = (
                        "{0}/rhel-7/nightly/RHEL-7/{1}/compose/Server/x86_64/os".format(
                            base_url, compose_id
                        )
                    )
                    repo_extra = "{0}/rhel-7/nightly/RHEL-7/{1}/compose/Server-optional/x86_64/os".format(
                        base_url, compose_id
                    )
                else:
                    repo_base = (
                        "{0}/rhel-7/rel-eng/RHEL-7/{1}/compose/Server/x86_64/os".format(
                            base_url, compose_id
                        )
                    )
                    repo_extra = "{0}/rhel-7/rel-eng/RHEL-7/{1}/compose/Server-optional/x86_64/os".format(
                        base_url, compose_id
                    )
            elif "RHEL-8" in compose_id:
                if "updates" in compose_id or "RHEL-8.4" in compose_id:
                    repo_base = "{0}/rhel-8/nightly/updates/RHEL-8/{1}/compose/BaseOS/x86_64/os".format(
                        base_url, compose_id
                    )
                    repo_extra = "{0}/rhel-8/nightly/updates/RHEL-8/{1}/compose/AppStream/x86_64/os".format(
                        base_url, compose_id
                    )
                elif ".d" in compose_id:
                    repo_base = "{0}/rhel-8/development/RHEL-8/{1}/compose/BaseOS/x86_64/os".format(
                        base_url, compose_id
                    )
                    repo_extra = "{0}/rhel-8/development/RHEL-8/{1}/compose/AppStream/x86_64/os".format(
                        base_url, compose_id
                    )
                else:
                    repo_base = (
                        "{0}/rhel-8/nightly/RHEL-8/{1}/compose/BaseOS/x86_64/os".format(
                            base_url, compose_id
                        )
                    )
                    repo_extra = "{0}/rhel-8/nightly/RHEL-8/{1}/compose/AppStream/x86_64/os".format(
                        base_url, compose_id
                    )
            elif "RHEL-9" in compose_id:
                if ".d" in compose_id:
                    repo_base = "{0}/rhel-9/development/RHEL-9/{1}/compose/BaseOS/x86_64/os".format(
                        base_url, compose_id
                    )
                    repo_extra = "{0}/rhel-9/development/RHEL-9/{1}/compose/AppStream/x86_64/os".format(
                        base_url, compose_id
                    )
                else:
                    repo_base = (
                        "{0}/rhel-9/nightly/RHEL-9/{1}/compose/BaseOS/x86_64/os".format(
                            base_url, compose_id
                        )
                    )
                    repo_extra = "{0}/rhel-9/nightly/RHEL-9/{1}/compose/AppStream/x86_64/os".format(
                        base_url, compose_id
                    )
        return repo_base, repo_extra

    def rhel_compose_repo(self, ssh_host, compose_id, repo_file):
        repo_base, repo_extra = self.rhel_compose_url(compose_id)
        cmd = (
            "cat <<EOF > {0}\n"
            "[{1}]\n"
            "name={1}\n"
            "baseurl={2}\n"
            "enabled=1\n"
            "gpgcheck=0\n\n"
            "[{1}-optional]\n"
            "name={1}-optional\n"
            "baseurl={3}\n"
            "enabled=1\n"
            "gpgcheck=0\n"
            "EOF"
        ).format(repo_file, compose_id, repo_base, repo_extra)
        ret, output = self.runcmd(cmd, ssh_host, desc="enable compose repo")

    def rhel_grub_update(
        self, ssh_host, ks_url, vmlinuz_url, initrd_url, repo_url, is_rhev=False
    ):
        if self.url_validation(vmlinuz_url) is False:
            raise FailException("vmlinuz_url is not available")
        if self.url_validation(initrd_url) is False:
            raise FailException("initrd_url is not available")
        if self.url_validation(repo_url) is False:
            raise FailException("repo_url is not available")
        menu_title = "rhel-reinstall"
        vmlinuz_name = "vmlinuz-reinstall"
        initrd_name = "initrd-reinstall.img"
        cmd = "rm -f /boot/%s; curl -L %s -o /boot/%s; sync" % (
            vmlinuz_name,
            vmlinuz_url,
            vmlinuz_name,
        )
        ret, output = self.runcmd(cmd, ssh_host, desc="download vmlinux file")
        cmd = "rm -f /boot/%s; curl -L %s -o /boot/%s; sync" % (
            initrd_name,
            initrd_url,
            initrd_name,
        )
        ret, output = self.runcmd(cmd, ssh_host, desc="download initrd file")
        if is_rhev == True:
            repo = "stage2=%s" % repo_url
        else:
            repo = "repo=%s" % repo_url
        rhel_ver = self.rhel_version(ssh_host)
        if rhel_ver == "6":
            cmd = (
                "cat <<EOF > /boot/grub/grub.conf\n"
                "default=0\n"
                "timeout=5\n"
                "splashimage=(hd0,0)/grub/splash.xpm.gz\n"
                "hiddenmenu\n"
                "title %s\n"
                "root (hd0,0)\n"
                "kernel /%s ksdevice=bootif ip=dhcp ks=%s %s quiet LANG=en_US.UTF-8 acpi=off\n"
                "initrd /%s\n"
                "EOF"
            ) % (menu_title, vmlinuz_name, ks_url, repo, initrd_name)
            ret, output = self.runcmd(cmd, ssh_host, desc="update grub menuentry")
        else:
            cmd = (
                "cat <<EOF > /etc/grub.d/40_custom\n"
                "#!/bin/sh\n"
                "exec tail -n +3 \$0\n"
                "menuentry '%s' --class red --class gnu-linux --class gnu --class os {\n"
                "load_video\n"
                "set gfxpayload=keep\n"
                "insmod gzio\n"
                "insmod part_msdos\n"
                "insmod xfs\n"
                'set root="hd0,msdos1"\n'
                "linux16 /%s ksdevice=bootif ip=dhcp ks=%s %s quiet LANG=en_US.UTF-8 acpi=off\n"
                "initrd16 /%s\n"
                "}\n"
                "EOF"
            ) % (menu_title, vmlinuz_name, ks_url, repo, initrd_name)
            ret, output = self.runcmd(cmd, ssh_host, desc="update grub menuentry")
            cmd = "grub2-mkconfig -o /boot/grub2/grub.cfg"
            ret, output = self.runcmd(cmd, ssh_host, desc="grub2-mkconfig")
            cmd = 'grub2-set-default "%s"; grub2-editenv list' % menu_title
            ret, output = self.runcmd(cmd, ssh_host, desc="grub2-set-default")
        time.sleep(60)
        cmd = "sync;sync;sync;sync;reboot -f && exit"
        ret, output = self.runcmd(
            cmd, ssh_host, desc="reboot for re-install", timeout=3
        )
        time.sleep(60)

    def rhel_install_by_grub(self, ssh_host, compose_id):
        random_str = "".join(random.sample(string.ascii_letters + string.digits, 8))
        nfs_server = deploy.nfs.server
        nfs_server_user = deploy.nfs.server_user
        nfs_server_passwd = deploy.nfs.server_passwd
        nfs_rhel_url = deploy.nfs.rhel_url
        nfs_rhel_mount = deploy.nfs.rhel_mount
        ssh_nfs = {
            "host": nfs_server,
            "username": nfs_server_user,
            "password": nfs_server_passwd,
        }
        ks_name = "{0}.cfg".format(random_str)
        ks_url = "{0}/{1}".format(nfs_rhel_url, ks_name)
        ks_path = "{0}/{1}".format(nfs_rhel_mount, ks_name)
        repo_base, repo_extra = self.rhel_compose_url(compose_id)
        cmd = (
            "cat <<EOF > {0}\n"
            "text\n"
            "bootloader --location=mbr\n"
            "lang en_US.UTF-8\n"
            "keyboard us\n"
            "network  --bootproto=dhcp --activate\n"
            "rootpw --plaintext {1}\n"
            "firewall --disabled\n"
            "selinux --disabled\n"
            "timezone Asia/Shanghai\n"
            "zerombr\n"
            "clearpart --all --initlabel\n"
            "autopart\n"
            "reboot\n"
            "repo --name=base --baseurl={2}\n"
            "repo --name=extra --baseurl={3}\n"
            "%packages --ignoremissing\n"
            "@base\n"
            "%end\n"
            "%post\n"
            'sed -i "s/#*PermitRootLogin.*/PermitRootLogin yes/g" /etc/ssh/sshd_config\n'
            'sed -i "s@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g" /etc/pam.d/sshd\n'
            "%end\n"
            "EOF"
        ).format(ks_path, ssh_host["password"], repo_base, repo_extra)
        ks_iscreated = ""
        for i in range(10):
            ret, output = self.runcmd(cmd, ssh_nfs, desc="create ks file")
            ret, output = self.runcmd(
                "ls {0}".format(ks_path), ssh_nfs, desc="check ks file created"
            )
            if ret == 0:
                logger.info("Succeeded to create ks file: {0}".format(ks_url))
                ks_iscreated = "Yes"
                break
            time.sleep(10)
        if ks_iscreated != "Yes":
            raise FailException("Failed to create ks file: {0}".format(ks_url))
        vmlinuz_url = "{0}/isolinux/vmlinuz".format(repo_base)
        initrd_url = "{0}/isolinux/initrd.img".format(repo_base)
        try:
            self.rhel_grub_update(
                ssh_host, ks_url, vmlinuz_url, initrd_url, repo_base, is_rhev=False
            )
            if self.ssh_is_connected(ssh_host):
                self.rhel_compose_repo(
                    ssh_host, compose_id, "/etc/yum.repos.d/compose.repo"
                )
                self.install_base_packages(ssh_host)
        except Exception as e:
            logger.error(e)
        finally:
            cmd = "rm -rf %s" % (ks_path)
            ret, output = self.runcmd(cmd, ssh_nfs, desc="clean ks file")

    def rhev_install_by_grub(self, ssh_host, iso_url):
        if self.url_validation(iso_url) is False:
            raise FailException("iso_url is not available")
        random_dir = "".join(random.sample(string.ascii_letters + string.digits, 8))
        nfs_server = deploy.nfs.server
        nfs_server_user = deploy.nfs.server_user
        nfs_server_passwd = deploy.nfs.server_passwd
        nfs_rhev_url = deploy.nfs.rhev_url
        nfs_rhev_mount = deploy.nfs.rhev_mount
        ssh_nfs = {
            "host": nfs_server,
            "username": nfs_server_user,
            "password": nfs_server_passwd,
        }
        ks_name = "rhev.ks"
        img_name = "squashfs.img"
        workspace = "{0}/{1}/".format(nfs_rhev_mount, random_dir)
        mnt_path = "{0}/mnt/".format(workspace)
        tmp_path = "{0}/tmp/".format(workspace)
        img_path = "{0}/{1}".format(workspace, img_name)
        ks_path = "{0}/{1}".format(workspace, ks_name)
        ks_url = "{0}/{1}/{2}".format(nfs_rhev_url, random_dir, ks_name)
        iso_path = "{0}/rhevh.iso".format(workspace)
        try:
            cmd = "rm -rf {0}; mkdir {0}; mkdir {1} {2}".format(
                workspace, tmp_path, mnt_path
            )
            ret, output = self.runcmd(cmd, ssh_nfs, desc="create dir for mount")
            cmd = "curl -L {0} -o {1}".format(iso_url, iso_path)
            ret, output = self.runcmd(cmd, ssh_nfs, desc="download iso to nfs server")
            cmd = "mount -o loop {0} {1}".format(iso_path, mnt_path)
            ret, output = self.runcmd(cmd, ssh_nfs, desc="mount iso")
            cmd = "cd {0}; rpm2cpio {1}/Packages/redhat-virtualization-host-image-update* |cpio -ivd".format(
                tmp_path, mnt_path
            )
            ret, output = self.runcmd(cmd, ssh_nfs, desc="rpm2cpio to get squashfs.img")
            cmd = "cd {0}; find|grep squashfs|grep -v meta | xargs -I {} cp {} {1}".format(
                tmp_path, img_path
            )
            ret, output = self.runcmd(cmd, ssh_nfs, desc="copy squashfs.img")
            img_url = "{0}/{1}/{2}".format(nfs_rhev_url, random_dir, img_name)
            cmd = (
                "cat <<EOF > {0}\n"
                "liveimg --url={1}\n"
                "clearpart --all\n"
                "autopart --type=thinp\n"
                "rootpw --plaintext {2}\n"
                "timezone --utc Asia/Harbin\n"
                "zerombr\n"
                "text\n"
                "reboot\n"
                "%post --erroronfail\n"
                "imgbase layout --init\n"
                "%end\n"
                "EOF"
            ).format(ks_path, img_url, ssh_host["password"])
            ks_iscreated = ""
            for i in range(10):
                ret, output = self.runcmd(cmd, ssh_nfs, desc="create ks file")
                ret, output = self.runcmd(
                    "ls {0}".format(ks_path), ssh_nfs, desc="check ks file created"
                )
                if ret == 0:
                    logger.info("Succeeded to create ks file: {0}".format(ks_url))
                    ks_iscreated = "Yes"
                    break
                time.sleep(10)
            if ks_iscreated != "Yes":
                raise FailException("Failed to create ks file: {0}".format(ks_url))
            repo_url = "{0}/{1}/mnt/".format(nfs_rhev_url, random_dir)
            vmlinuz_url = "{0}/{1}/mnt/isolinux/vmlinuz".format(
                nfs_rhev_url, random_dir
            )
            initrd_url = "{0}/{1}/mnt/isolinux/initrd.img".format(
                nfs_rhev_url, random_dir
            )
            self.rhel_grub_update(
                ssh_host, ks_url, vmlinuz_url, initrd_url, repo_url, is_rhev=True
            )
            self.ssh_is_connected(ssh_host)
        except Exception as e:
            logger.error(e)
        finally:
            cmd = "umount {0}; rm -rf {1}".format(mnt_path, workspace)
            ret, output = self.runcmd(cmd, ssh_nfs, desc="clean rhev iso and image")

    # *********************************************
    # Beaker Client Function for provision
    # *********************************************
    def runcmd_beaker(self, cmd, timeout=None, desc="run cmd on beaker"):
        ssh_bkr = {
            "host": deploy.beaker.client,
            "username": deploy.beaker.client_user,
            "password": deploy.beaker.client_passwd,
        }
        return self.runcmd(cmd, ssh_bkr, timeout, desc)

    def beaker_kinit(self):
        cmd = "kinit -k -t {0} {1}".format(
            deploy.beaker.keytab, deploy.beaker.principal
        )
        ret, output = self.runcmd_beaker(cmd, desc="beaker client kinit")
        if ret == 0:
            cmd = "bkr whoami"
            ret, output = self.runcmd_beaker(cmd, desc="bkr whoami test")
            return True
        else:
            return False

    def beaker_Jsubmit(self, os_type, variant, arch, distro, job_name):
        task = "--suppress-install-task --task /distribution/dummy --task /distribution/reservesys"
        whiteboard = '''--whiteboard="reserve host for {0}"'''.format(job_name)
        reserve = "--reserve --reserve-duration 259200 --priority Urgent"
        job_group = "--job-group=virt-who-ci-server-group"
        if os_type == "virtual":
            satellite_vm = f'''--hostrequire "<and><system><name op='like' value='{deploy.trigger.satellite_host}'/></system></and>"'''
            hostrequire = '''{0} --hostrequire "hypervisor!=" --hostrequire "memory > 7000"'''.format(
                satellite_vm
            )
        else:
            hostrequire = (
                '''--hostrequire "hypervisor=" --hostrequire "memory > 7000"'''
            )
        cmd = """bkr workflow-simple --prettyxml --variant={0} --arch={1} --distro={2} {3} {4} {5} {6} {7}""".format(
            variant, arch, distro, task, whiteboard, job_group, hostrequire, reserve
        )
        ret, output = self.runcmd_beaker(cmd, desc="provsion host from beaker")
        if ret == 0 and "Submitted" in output:
            logger.info("Succeeded to submit beaker job: {0}".format(job_name))
            job_id = re.findall(r"Submitted: \['(.*?)'", output)[0]
            return job_id
        else:
            raise FailException("Failed to submit beaker job {0}".format(job_name))

    def beaker_Jstatus(self, jobs):
        job_status = list()
        for job_name, job_id in jobs.items():
            cmd = "bkr job-results {0} --no-logs".format(job_id)
            ret, output = self.runcmd_beaker(cmd, desc="check beaker job status")
            if 'status="Aborted"' in output:
                job_status.append("Aborted")
            elif 'status="Completed"' in output:
                job_status.append("Completed")
            elif 'status="Cancelled"' in output:
                job_status.append("Cancelled")
            else:
                job_status.append("Pending")
        logger.info("Beaker Jobs: {0}, Jobs status: {1}".format(jobs, job_status))
        if "Pending" in job_status:
            return True
        else:
            return False

    def beaker_Jresult(self, jobs):
        job_passed = dict()
        for job_name, job_id in jobs.items():
            cmd = "bkr job-results {0} --no-logs".format(job_id)
            ret, output = self.runcmd_beaker(cmd, desc="check beaker job result")
            if ret == 0 and 'status="Completed"' in output:
                output = re.findall(r'system="(.*?)"', output)
                if len(output) > 0:
                    job_passed[job_name] = output[0]
            else:
                logger.error(
                    "No available machines found for job [{0}: {1}]".format(
                        job_name, job_id
                    )
                )
        return job_passed

    def beaker_compose_setup(self, compose_id, arch_type):
        jobs = dict()
        job_name = "virtwho-host-%s" % arch_type
        os_type = "physical"
        variant = arch_type.split("-")[0]
        arch = arch_type.split("-")[1]
        distro = compose_id
        job_id = self.beaker_Jsubmit(os_type, variant, arch, distro, job_name)
        jobs[job_name] = job_id
        while self.beaker_Jstatus(jobs):
            logger.info("Sleep 60s to check the beaker job status again")
            time.sleep(60)
        job_passed = self.beaker_Jresult(jobs)
        if job_passed:
            for job_name, host_ip in job_passed.items():
                return host_ip
        else:
            raise FailException(
                "Failed to provision beaker host for job: {0}".format(job_name)
            )

    # *********************************************
    # Provision Satellite
    # *********************************************
    def satellite_machines(self, sat_list):
        jobs = dict()
        for job_name in sat_list:
            os_type = "virtual"
            variant = "Server"
            arch = "x86_64"
            if "rhel6" in job_name or "rhel-6" in job_name:
                compose_id = deploy.satellite.rhel6_compose
            if "rhel7" in job_name or "rhel-7" in job_name:
                compose_id = deploy.satellite.rhel7_compose
            if "rhel8" in job_name or "rhel-8" in job_name:
                compose_id = deploy.satellite.rhel8_compose
                variant = "BaseOS"
            distro = compose_id
            job_id = self.beaker_Jsubmit(os_type, variant, arch, distro, job_name)
            jobs[job_name] = job_id
        logger.info(jobs)
        while self.beaker_Jstatus(jobs):
            time.sleep(60)
        job_passed = self.beaker_Jresult(jobs)
        return job_passed

    def satellite_version(self, sat_type):
        if "6.12" in sat_type or "612" in sat_type:
            sat_ver = "6.12"
        elif "6.11" in sat_type or "611" in sat_type:
            sat_ver = "6.11"
        elif "6.10" in sat_type or "610" in sat_type:
            sat_ver = "6.10"
        elif "6.9" in sat_type or "69" in sat_type:
            sat_ver = "6.9"
        elif "6.8" in sat_type or "68" in sat_type:
            sat_ver = "6.8"
        elif "6.7" in sat_type or "67" in sat_type:
            sat_ver = "6.7"
        elif "6.6" in sat_type or "66" in sat_type:
            sat_ver = "6.6"
        elif "6.5" in sat_type or "65" in sat_type:
            sat_ver = "6.5"
        elif "6.4" in sat_type or "64" in sat_type:
            sat_ver = "6.4"
        elif "6.3" in sat_type or "63" in sat_type:
            sat_ver = "6.3"
        elif "6.2" in sat_type or "62" in sat_type:
            sat_ver = "6.2"
        elif "7.0" in sat_type or "70" in sat_type:
            sat_ver = "7.0"
        elif "upstream" in sat_type:
            sat_ver = "upstream"
        else:
            raise FailException("Unknown satellite version")
        if "rhel6" in sat_type or "rhel-6" in sat_type:
            rhel_ver = "6"
        elif "rhel7" in sat_type or "rhel-7" in sat_type:
            rhel_ver = "7"
        elif "rhel8" in sat_type or "rhel-8" in sat_type:
            rhel_ver = "8"
        else:
            raise FailException("Unknown rhel version")
        logger.info(
            "Succeed to get the satellite version: {0}, RHEL version: {1}".format(
                sat_ver, rhel_ver
            )
        )
        return sat_ver, rhel_ver

    def satellite_cdn_pool_attach(self, ssh_sat):
        pool_id = deploy.register.satellite_sku
        sat_host = ssh_sat["host"]
        cmd = "subscription-manager subscribe --pool={0}".format(pool_id)
        for i in range(10):
            ret, output = self.runcmd(cmd, ssh_sat, desc="attach Satellite Pool")
            if ret == 0 or "has already had the subscription" in output:
                logger.info("Succeeded to attach Satellite Pool({0})".format(sat_host))
                return True
            logger.warning(
                "Failed to attach Satellite Pool({0}), try again after 30s...".format(
                    sat_host
                )
            )
            cmd = "subscription-manager remove --pool={0}".format(pool_id)
            ret, output = self.runcmd(cmd, ssh_sat, desc="remove Satellite Pool")
            time.sleep(30)
        raise FailException("Failed to attach Satellite Pool({0})".format(sat_host))

    def satellite_cdn_repo_enable(self, ssh_sat, sat_ver, rhel_ver):
        sat_host = ssh_sat["host"]
        cmd = "subscription-manager repos \
                --enable=rhel-{0}-server-satellite-maintenance-6-rpms \
                --enable=rhel-{0}-server-satellite-{1}-rpms \
                --enable=rhel-{0}-server-ansible-2.9-rpms".format(
            rhel_ver, sat_ver
        )
        if rhel_ver == "8":
            cmd = "subscription-manager repos \
                    --enable=satellite-{0}-for-rhel-8-x86_64-rpms \
                    --enable=satellite-maintenance-{0}-for-rhel-8-x86_64-rpms".format(
                sat_ver
            )
        status, output = self.run_loop(cmd, ssh_sat, desc="enable satellite repos")
        if status != "Yes":
            raise FailException(
                "Failed to enable satellite repos({0})".format(sat_host)
            )
        if rhel_ver == "8":
            cmd = "dnf -y module enable satellite:el8"
            _, _ = self.runcmd("dnf -y module enable satellite:el8", ssh_sat)
        logger.info("Succeeded to enable satellite repos({0})".format(sat_host))

    def satellite_cdn_repo_config(self, ssh_sat, sat_ver, rhel_ver):
        sat_host = ssh_sat["host"]
        cmd = "subscription-manager repos \
                --enable=rhel-{0}-for-x86_64-baseos-rpms \
                --enable=rhel-{0}-for-x86_64-appstream-rpms \
                --enable=satellite-{1}-for-rhel-{0}-x86_64-rpms \
                --enable=satellite-maintenance-{1}-for-rhel-{0}-x86_64-rpms".format(
            rhel_ver, sat_ver
        )
        status, output = self.run_loop(cmd, ssh_sat, desc="enable satellite repos")
        if status != "Yes":
            raise FailException(
                "Failed to enable satellite repos({0})".format(sat_host)
            )
        logger.info("Succeeded to enable satellite repos({0})".format(sat_host))
        if rhel_ver == "8":
            cmd = "dnf -y module enable satellite:el8"
            _, output = self.runcmd(cmd, ssh_sat, desc="enable satellite rhel8 module")

    def satellite_qa_dogfood_enable(
        self, ssh_sat, sat_ver, rhel_ver, repo_type="satellite"
    ):
        """repo_type should be one of them: satellite, capsule, satellite-tools"""
        repo = deploy.repo.rhel_sat
        for i in range(3):
            cmd = "subscription-manager unregister"
            ret, output = self.runcmd(cmd, ssh_sat, desc="sub-man unregister")
            cmd = "subscription-manager clean"
            ret, output = self.runcmd(cmd, ssh_sat, desc="sub-man clean")
            cmd = "rpm -qa | grep katello-ca-consumer | xargs rpm -e |sort"
            ret, output = self.runcmd(
                cmd, ssh_sat, desc="uninstall katello-ca-consumer"
            )
            cmd = "yum -y localinstall {0}".format(repo)
            ret, output = self.runcmd(cmd, ssh_sat, desc="install katello-ca")
            cmd = (
                "subscription-manager register --org Sat6-CI --activationkey '%s-%s-qa-rhel%s'"
                % (repo_type, sat_ver, rhel_ver)
            )
            ret, output = self.runcmd(cmd, ssh_sat, desc="register and enable repo")
            if rhel_ver == "8":
                cmd = "dnf -y module enable satellite:el8"
                _, output = self.runcmd(
                    cmd, ssh_sat, desc="enable satellite rhel8 module"
                )
            if ret == 0:
                cmd = "subscription-manager attach --pool 8a88800f5ca45116015cc807610319ed"
                ret, output = self.runcmd(
                    cmd, ssh_sat, desc="attach Satellite Maintenance Composes"
                )
                return True
            time.sleep(15)
        logger.error("Failed to enable satellite qa repo")
        return False

    def satellite_repo_enable(self, ssh_sat, sat_ver, rhel_ver):
        """enable satellite repo"""
        if rhel_ver == "7":
            cmd = "subscription-manager repos --disable=*; subscription-manager repos \
            --enable=rhel-{0}-server-rpms \
            --enable=rhel-server-rhscl-{0}-rpms \
            --enable=rhel-{0}-server-ansible-2.9-rpms".format(
                rhel_ver
            )
        elif rhel_ver == "8":
            cmd = "subscription-manager repos --disable=*; subscription-manager repos \
            --enable=rhel-{0}-for-x86_64-baseos-rpms \
            --enable=rhel-{0}-for-x86_64-appstream-rpms".format(
                rhel_ver
            )
        status, output = self.run_loop(cmd, ssh_sat, desc="enable satellite repos")
        if status != "Yes":
            raise FailException("Failed to enable satellite repos({0})".format(ssh_sat))
        logger.info("Succeeded to enable satellite repos".format(ssh_sat))
        cmd = "curl -o /etc/pki/ca-trust/source/anchors/satellite-sat-engineering-ca.crt http://satellite.sat.engineering.redhat.com/pub/katello-server-ca.crt; update-ca-trust"
        status, output = self.run_loop(cmd, ssh_sat, desc="update ca cert")
        if status != "Yes":
            raise FailException("Failed to update ca cert)".format(ssh_sat))
        logger.info("Succeeded to update ca cert".format(ssh_sat))
        cmd = "curl -o /etc/yum.repos.d/satellite.repo http://ohsnap.sat.engineering.redhat.com/api/releases/{0}.0/el{1}/satellite/repo_file".format(
            sat_ver, rhel_ver
        )
        status, output = self.run_loop(cmd, ssh_sat, desc="get satellite repo_file")
        if status != "Yes":
            raise FailException("Failed to get satellite repo_file)".format(ssh_sat))
        logger.info("Succeeded to get satellite repo_file".format(ssh_sat))
        if rhel_ver == "8":
            cmd = "dnf -y module enable satellite:el8"
            _, output = self.runcmd(cmd, ssh_sat, desc="enable satellite rhel8 module")

    def satellite_pkg_install(self, ssh_sat):
        sat_host = ssh_sat["host"]
        logger.info("Start to install satellite package({0})".format(sat_host))
        for i in range(3):
            cmd = "rm -f /var/lib/rpm/__db*; rpm --rebuilddb; rm -rf /var/lib/yum/history/*.sqlite; rm -fr /var/cache/yum/*; yum clean all"
            ret, output = self.runcmd(
                cmd, ssh_sat, desc="clean yum history and rebuilddb"
            )
            cmd = "yum install -y satellite"
            ret, output = self.runcmd(cmd, ssh_sat, desc="install satellite packages")
            if ret == 0:
                logger.info(
                    "Succeeded to install satellite package({0})".format(sat_host)
                )
                return True
        raise FailException("Failed to install satellite package({0})".format(sat_host))

    def satellite_deploy(
        self, ssh_sat, admin_user, admin_passwd, manifest_url, sat_ver
    ):
        sat_host = ssh_sat["host"]
        manifest_path = "/tmp/manifest"
        ret, output = self.runcmd(
            "rm -rf {0}; mkdir -p {0}".format(manifest_path), ssh_sat
        )
        ret, output = self.runcmd(
            "wget {0} -P {1}".format(manifest_url, manifest_path), ssh_sat
        )
        ret, output = self.runcmd("ls {0}".format(manifest_path), ssh_sat)
        if output is not None:
            manifest_filename = "{0}/{1}".format(manifest_path, output.strip())
        else:
            raise FailException("No manifest file found")
        options = "--disable-system-checks --foreman-initial-admin-password={0}".format(
            admin_passwd
        )
        cmd = "satellite-installer --scenario satellite {0}".format(options)
        ret, output = self.runcmd(cmd, ssh_sat)
        if ret != 0:
            cmd = "for i in pulp_resource_manager pulp_workers pulp_celerybeat; do service $i stop; done"
            ret, output = self.runcmd(cmd, ssh_sat)
            cmd = "sudo -u apache pulp-manage-db"
            ret, output = self.runcmd(cmd, ssh_sat)
            cmd = "echo y |satellite-installer --reset --scenario satellite {0}".format(
                options
            )
            ret, output = self.runcmd(cmd, ssh_sat)
            if ret != 0:
                raise FailException(
                    "Failed to satellite-installer --scenario satellite({0})".format(
                        sat_host
                    )
                )
        logger.info(
            "Succeeded to run satellite-installer --scenario satellite({0})".format(
                sat_host
            )
        )
        upload_manifest = "hammer -u {0} -p {1} subscription upload --organization-label Default_Organization --file {2}".format(
            admin_user, admin_passwd, manifest_filename
        )
        delete_manifest = "hammer -u {0} -p {1} subscription delete-manifest --organization-label Default_Organization".format(
            admin_user, admin_passwd
        )
        is_uploaded = ""
        for i in range(3):
            ret, output = self.runcmd(upload_manifest, ssh_sat)
            if ret == 0:
                is_uploaded = "yes"
                logger.info(
                    "Succeeded to upload manifest to satellite({0})".format(sat_host)
                )
                break
            time.sleep(15)
            self.runcmd(delete_manifest, ssh_sat)
        if is_uploaded != "yes":
            raise FailException("Failed to upload manifest")
        cmd = 'hammer -u {0} -p {1} subscription refresh-manifest --organization="Default Organization"'.format(
            admin_user, admin_passwd
        )
        status, output = self.run_loop(cmd, ssh_sat, desc="manifest refresh")
        if status != "Yes":
            raise FailException(
                "Failed to refresh satellite manifest({0})".format(sat_host)
            )
        logger.info("Succeeded to refresh satellite manifest({0})".format(sat_host))
        logger.info("Succeeded to deploy satellite({0})".format(sat_host))

    def satellite_nightly_deploy(self, ssh_sat, admin_user, admin_passwd, manifest_url):
        sat_host = ssh_sat["host"]
        manifest_path = "/tmp/manifest"
        self.runcmd("rm -rf {0}; mkdir -p {0}".format(manifest_path), ssh_sat)
        self.runcmd("wget {0} -P {1}".format(manifest_url, manifest_path), ssh_sat)
        ret, output = self.runcmd("ls {0}".format(manifest_path), ssh_sat)
        if output is not None:
            manifest_filename = "{0}/{1}".format(manifest_path, output.strip())
        else:
            raise FailException("No manifest file found")
        self.rhel_epel_repo(ssh_sat)
        self.runcmd(
            "yum install -y ntp;systemctl enable ntpd;systemctl start ntpd", ssh_sat
        )
        self.runcmd("yum install -y ansible git", ssh_sat)
        self.runcmd("git clone -q https://github.com/theforeman/forklift.git", ssh_sat)
        ansible_playbook = (
            "cd forklift; "
            "ansible-playbook -c local -i,$(hostname) "
            "-e katello_version=nightly "
            "-e foreman_installer_skip_installer=True playbooks/katello.yml"
        )
        plugin_install = (
            "yum install -y "
            "foreman-{ec2,gce,libvirt,openstack,ovirt,rackspace,vmware} "
            "tfm-rubygem-hammer_cli_{csv,foreman_admin,foreman_discovery,"
            "foreman_openscap,foreman_remote_execution} *virt_who_configure"
        )
        foreman_install = (
            "foreman-installer --scenario katello  -v "
            '--foreman-initial-admin-password="{0}" '
            "--disable-system-checks "
            '--foreman-proxy-dns="true" '
            '--foreman-proxy-dns-interface="eth0" '
            '--foreman-proxy-dns-zone="{1}" '
            '--foreman-proxy-dhcp="true" '
            '--foreman-proxy-dhcp-interface="eth0" '
            '--foreman-proxy-tftp="true" '
            '--foreman-proxy-tftp-servername="{2}" '
            '--foreman-proxy-register-in-foreman="true" '
            '--foreman-proxy-puppetca="true" '
            '--foreman-proxy-puppet="true"  '
            '--katello-proxy-url="{3}" '
            '--katello-proxy-port="3128" '
            '--katello-proxy-username="{4}" '
            '--katello-proxy-password="{5}" '
            "--enable-foreman-plugin-remote-execution "
            "--enable-foreman-proxy-plugin-remote-execution-ssh "
            "--enable-foreman-plugin-discovery "
            "--enable-foreman-proxy-plugin-discovery "
            "--enable-foreman-plugin-openscap "
            "--enable-foreman-proxy-plugin-openscap "
            "--enable-foreman-plugin-ansible "
            "--enable-foreman-proxy-plugin-ansible"
        ).format(
            admin_passwd,
            deploy.satellite.foreman_proxy_dns,
            deploy.satellite.foreman_proxy_tftp,
            deploy.satellite.katello_proxy_url,
            deploy.satellite.katello_proxy_username,
            deploy.satellite.katello_proxy_password,
        )
        upload_manifest = (
            "hammer -u {0} -p {1} subscription upload "
            "--organization-label Default_Organization "
            "--file {2}"
        ).format(admin_user, admin_passwd, manifest_filename)
        refresh_manifest = (
            "hammer -u {0} -p {1} subscription refresh-manifest "
            '--organization="Default Organization"'
        ).format(admin_user, admin_passwd)
        self.runcmd(ansible_playbook, ssh_sat)
        self.runcmd(plugin_install, ssh_sat)
        ret, output = self.runcmd(foreman_install, ssh_sat)
        if ret != 0:
            raise FailException("Failed to run: {}".format(foreman_install))
        self.run_loop(upload_manifest, ssh_sat)
        self.run_loop(refresh_manifest, ssh_sat)

    def satellite_setup(self, sat_queue, sat_type, sat_host):
        logger.info("Start to deploy %s:%s" % (sat_type, sat_host))
        func_name = sys._getframe().f_code.co_name
        api = "https://{0}".format(sat_host)
        admin_user = deploy.satellite.admin_user
        admin_passwd = deploy.satellite.admin_passwd
        ssh_user = deploy.beaker.default_user
        ssh_passwd = deploy.beaker.default_passwd
        default_org = deploy.satellite.default_org
        extra_org = deploy.satellite.extra_org
        env = deploy.satellite.default_env
        activation_key = deploy.satellite.activation_key
        manifest_url = deploy.satellite.manifest
        ssh_sat = {"host": sat_host, "username": ssh_user, "password": ssh_passwd}
        register_config = {
            "type": sat_type,
            "server": sat_host,
            "username": admin_user,
            "password": admin_passwd,
            "owner": default_org,
            "env": env,
            "ssh_user": ssh_user,
            "ssh_passwd": ssh_passwd,
            "api": api,
            "ssh_sat": ssh_sat,
        }
        self.system_init("ci-host-satellite", ssh_sat)
        sat_ver, rhel_ver = self.satellite_version(sat_type)
        logger.info(
            "Satellite version: {0}, RHEL version: {1}".format(sat_ver, rhel_ver)
        )
        if "dogfood" in sat_type:
            self.employee_sku_attach(ssh_sat)
            self.satellite_repo_enable(ssh_sat, sat_ver, rhel_ver)
        if "cdn" in sat_type:
            self.employee_sku_attach(ssh_sat)
            if rhel_ver == "8":
                self.satellite_cdn_repo_config(ssh_sat, sat_ver, rhel_ver)
            else:
                self.rhel_repo_enable(ssh_sat)
                self.satellite_cdn_pool_attach(ssh_sat)
                self.satellite_cdn_repo_enable(ssh_sat, sat_ver, rhel_ver)
        self.satellite_pkg_install(ssh_sat)
        self.satellite_deploy(ssh_sat, admin_user, admin_passwd, manifest_url, sat_ver)
        self.satellite_host_setting(ssh_sat, register_config)
        self.satellite_org_create(ssh_sat, register_config, extra_org)
        default_org_id = self.satellite_org_id_get(
            ssh_sat, register_config, default_org
        )
        self.satellite_active_key_create(
            ssh_sat, register_config, activation_key, default_org_id
        )
        sat_queue.put((sat_type, sat_host))

    # *********************************************
    # Virtwho compose host by docker and beaker
    # *********************************************
    def docker_image_exist(self, image_name, ssh_docker):
        host = ssh_docker["host"]
        cmd = "docker images | grep %s" % image_name
        ret, output = self.runcmd(cmd, ssh_docker, desc="docker image check")
        if ret != 0:
            logger.info("docker image %s is not exist(%s)" % (image_name, host))
            return False
        else:
            logger.info("docker image %s is ready on %s" % (image_name, host))
            return True

    def docker_image_delete(self, image_name, ssh_docker):
        host = ssh_docker["host"]
        if self.docker_image_exist(image_name, ssh_docker) is True:
            logger.info("Start to delete docker image %s(%s)" % (image_name, host))
            cmd = (
                "docker ps -a | grep '%s' | awk '{print $1 }'|xargs -I {} docker stop {}"
                % image_name
            )
            self.runcmd(cmd, ssh_docker, desc="docker container stop")
            cmd = (
                "docker ps -a | grep '%s' | awk '{print $1 }'|xargs -I {} docker rm -f {}"
                % image_name
            )
            self.runcmd(cmd, ssh_docker, desc="docker container delete")
            cmd = "docker images | grep none | awk '{print $3 }'|xargs -I {} docker rmi -f {}"
            self.runcmd(cmd, ssh_docker, desc="docker delete none tag image")
            cmd = (
                "docker images | grep '%s' | awk '{print $3 }' |xargs -I {} docker rmi -f {}"
                % image_name
            )
            self.runcmd(cmd, ssh_docker, desc="docker delete image")

    def docker_image_create(self, ssh_docker, compose_id):
        image_name = compose_id.lower()
        if self.docker_image_exist(image_name, ssh_docker) is False:
            logger.info("Start to create docker image {0}".format(image_name))
            compose_repo = "/tmp/docker/compose.repo"
            self.rhel_compose_repo(ssh_docker, compose_id, compose_repo)
            cmd = "sh /tmp/docker/mk_image.sh -y {0} {1}".format(
                compose_repo, image_name
            )
            logger.info("Command to create docker image: {0}".format(cmd))
            ret, output = self.runcmd(cmd, ssh_docker)
            if ret == 0:
                logger.info("Succeeded to create compose image {0}".format(image_name))
            else:
                raise FailException(
                    "Failed to create compose image {0}".format(image_name)
                )

    def docker_container_exist(self, ssh_docker, keyword):
        keyword = str(keyword)
        cmd = "docker ps -a | grep '{0}'".format(keyword)
        ret, output = self.runcmd(cmd, ssh_docker)
        if ret == 0 and keyword in output:
            return True
        else:
            return False

    def docker_container_clean(self, ssh_docker):
        ret, output = self.runcmd("sh /tmp/docker/rm_containers.sh -d 5", ssh_docker)
        logger.info("Delete all the containers which created above 5 days")
        ret, output = self.runcmd("docker ps -a |wc -l", ssh_docker)
        if int(output) > 10:
            cmd = "docker ps -a | awk '{print $1 }'|xargs -I {} docker stop {}"
            self.runcmd(cmd, ssh_docker, desc="Stop all containers")
            cmd = "docker ps -a | awk '{print $1 }'|xargs -I {} docker rm -f {}"
            self.runcmd(cmd, ssh_docker, desc="Delete all containers")

    def docker_container_port(self, ssh_docker):
        port = random.randint(53220, 60000)
        while self.docker_container_exist(ssh_docker, port):
            port = random.randint(53220, 60000)
        return str(port)

    def docker_container_create(
        self, ssh_docker, image_name, cont_name, cont_user, cont_passwd, cont_port
    ):
        host = ssh_docker["host"]
        cmd = (
            "sh /tmp/docker/mk_container.sh -i {0} -c {1} -o {2} -u {3} -p {4}".format(
                image_name, cont_name, cont_port, cont_user, cont_passwd
            )
        )
        self.runcmd(cmd, ssh_docker)
        is_created = ""
        if self.docker_container_exist(
            ssh_docker, cont_port
        ) and self.docker_container_exist(ssh_docker, cont_name):
            is_created = "Yes"
            logger.info(
                "Succeeded to create container: {0}:{1}".format(cont_name, cont_port)
            )
        else:
            logger.info("Command to create docker container: {0}".format(cmd))
            logger.error("Failed to create container: {0}".format(cont_name))
        if is_created == "Yes":
            return True
        else:
            return False

    def docker_compose_setup(self, compose_id, remote_modes):
        conf_hosts = dict()
        server = deploy.docker.server
        server_user = deploy.docker.server_user
        server_passwd = deploy.docker.server_passwd
        ssh_docker = {
            "host": server,
            "username": server_user,
            "password": server_passwd,
        }
        container_user = deploy.docker.container_user
        container_passwd = deploy.docker.container_passwd
        image_name = compose_id.lower()
        self.runcmd("docker system prune -f", ssh_docker, desc="clean docker cache")
        root_path = os.path.abspath(os.path.join(os.getcwd(), "../"))
        local_dir = os.path.join(root_path, "docker/")
        remote_dir = "/tmp/docker/"
        self.runcmd(
            "rm -rf /tmp/docker/; rm -rf /tmp/mkimage*; rm -f /etc/yum.repos.d/*.repo",
            ssh_docker,
        )
        self.runcmd("subscription-manager unregister", ssh_docker)
        self.runcmd("subscription-manager clean", ssh_docker)
        self.paramiko_putdir(ssh_docker, local_dir, remote_dir)
        self.docker_image_create(ssh_docker, compose_id)
        self.docker_container_clean(ssh_docker)
        for mode in remote_modes:
            container_port = self.docker_container_port(ssh_docker)
            container_name = (
                image_name.replace(".", "-")
                + "-"
                + mode.strip()
                + "-"
                + container_port
                + ".redhat.com"
            )
            if self.docker_container_create(
                ssh_docker,
                image_name,
                container_name,
                container_user,
                container_passwd,
                container_port,
            ):
                ip_value = "{0}:{1}".format(server, container_port)
                ip_name = "virtwho-host-{0}-ip".format(mode)
                conf_hosts[ip_name] = ip_value
                ssh_container = {
                    "host": ip_value,
                    "username": container_user,
                    "password": container_passwd,
                }
                self.rhsm_override_uuid(ssh_container)
                if mode == "libvirt-remote":
                    self.ssh_no_passwd_access(ssh_container)
            time.sleep(60)
        return conf_hosts

    # *********************************************
    # Hypervisor guests setup
    # *********************************************
    def guest_esx_setup(self, mode_queue, mode_type):
        # get deploy settings for esx mode
        vcenter_ip = deploy.vcenter.ip
        cli_ssh_ip = deploy.vcenter.ssh_ip
        cli_ssh_user = deploy.vcenter.ssh_user
        cli_ssh_passwd = deploy.vcenter.ssh_passwd
        vcenter_admin_user = deploy.vcenter.admin_user
        vcenter_admin_passwd = deploy.vcenter.admin_passwd
        master = deploy.vcenter.master
        master_user = deploy.vcenter.master_user
        master_passwd = deploy.vcenter.master_passwd
        guest_name = deploy.vcenter.guest_name
        guest_user = deploy.vcenter.guest_user
        guest_passwd = deploy.vcenter.guest_passwd
        image_path = deploy.vcenter.image_path
        # set ssh env for vcenter, master
        ssh_cli = {
            "host": cli_ssh_ip,
            "username": cli_ssh_user,
            "password": cli_ssh_passwd,
        }
        cert = self.vcenter_cert(vcenter_ip, vcenter_admin_user, vcenter_admin_passwd)
        guest_ip = self.vcenter_guest_ip(cert, ssh_cli, guest_name)
        if not guest_ip:
            ssh_master = {
                "host": master,
                "username": master_user,
                "password": master_passwd,
            }
            self.vcenter_host_ready(cert, ssh_cli, ssh_master)
            guest_ip = self.vcenter_guest_add(
                cert, ssh_cli, ssh_master, guest_name, image_path
            )
        logger.info("Succeeded to get vcenter guest ip: {0}".format(guest_ip))
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-esx", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_hyperv_setup(self, mode_queue, mode_type):
        # get deploy settings for hyperv mode
        master = deploy.hyperv.master
        master_user = deploy.hyperv.master_user
        master_passwd = deploy.hyperv.master_passwd
        guest_name = deploy.hyperv.guest_name
        guest_user = deploy.hyperv.guest_user
        guest_passwd = deploy.hyperv.guest_passwd
        image_path = deploy.hyperv.image_path
        # set ssh env for hyperv master
        ssh_hyperv = {
            "host": master,
            "username": master_user,
            "password": master_passwd,
        }
        guest_ip = self.hyperv_guest_ip(ssh_hyperv, guest_name)
        if not guest_ip:
            guest_ip = self.hyperv_guest_add(ssh_hyperv, guest_name, image_path)
        logger.info("Succeeded to get hyperv guest ip: {0}".format(guest_ip))
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-hyperv", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_ahv_setup(self, mode_queue, mode_type):
        guest_name = deploy.ahv.guest_name
        guest_user = deploy.ahv.guest_user
        guest_passwd = deploy.ahv.guest_passwd
        guest_ip = self.ahv_guest_ip()
        logger.info("Succeeded to get ahv guest ip: {0}".format(guest_ip))
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-ahv", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_xen_setup(self, mode_queue, mode_type):
        # get deploy settings for xen mode
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
        ssh_master = {
            "host": master,
            "username": master_user,
            "password": master_passwd,
        }
        guest_ip = self.xen_guest_ip(ssh_master, guest_name)
        if not guest_ip:
            self.xen_host_ready(ssh_master, sr_name, sr_server, sr_path)
            guest_ip = self.xen_guest_add(ssh_master, guest_name, sr_name, image_path)
        logger.info("Succeeded to get xen guest ip: {0}".format(guest_ip))
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-xen", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_kubevirt_setup(self, mode_queue, mode_type):
        guest_name = deploy.kubevirt.guest_name
        guest_user = deploy.kubevirt.guest_user
        guest_passwd = deploy.kubevirt.guest_passwd
        guest_ip = self.kubevirt_guest_ip(guest_name)
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-kubvirt", ssh_guest)
        logger.info("Succeeded to get kubevirt guest ip: {0}".format(guest_ip))
        mode_queue.put((mode_type, guest_ip))

    def guest_rhevm_setup(self, mode_queue, mode_type):
        # get deploy settings for rhevm mode
        rhevm_ip = deploy.rhevm.rhevm_ip
        rhevm_ssh_user = deploy.rhevm.rhevm_ssh_user
        rhevm_ssh_passwd = deploy.rhevm.rhevm_ssh_passwd
        guest_name = deploy.rhevm.guest_name
        guest_user = deploy.rhevm.guest_user
        guest_passwd = deploy.rhevm.guest_passwd
        # set ssh env for rhevm, master
        ssh_rhevm = {
            "host": rhevm_ip,
            "username": rhevm_ssh_user,
            "password": rhevm_ssh_passwd,
        }
        guest_ip = self.rhevm_guest_ip(ssh_rhevm, guest_name)
        logger.info(
            "Succeeded to get rhevm({0}) guest ip: {1} for rhevm mode".format(
                rhevm_ip, guest_ip
            )
        )
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-rhevm", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_libvirt_remote_setup(self, mode_queue, mode_type):
        remote_host = deploy.libvirt.remote
        remote_user = deploy.libvirt.remote_user
        remote_passwd = deploy.libvirt.remote_passwd
        guest_name = deploy.libvirt.guest_name
        guest_user = deploy.libvirt.guest_user
        guest_passwd = deploy.libvirt.guest_passwd
        ssh_libvirt = {
            "host": remote_host,
            "username": remote_user,
            "password": remote_passwd,
        }
        """remote libvirt is stable env"""
        # self.stop_firewall(ssh_libvirt)
        # self.employee_sku_attach(ssh_libvirt)
        # self.rhel_repo_enable(ssh_libvirt)
        # self.libvirt_pkg_install(ssh_libvirt)
        # self.bridge_setup("br0", ssh_libvirt)
        cmd = "service libvirtd restart"
        ret, output = self.runcmd(cmd, ssh_libvirt)
        guest_ip = self.libvirt_guest_ip(guest_name, ssh_libvirt)
        if not guest_ip:
            self.libvirt_guests_all_clean(ssh_libvirt)
            guest_ip = self.libvirt_guest_add(guest_name, ssh_libvirt)
        logger.info(
            "Succeeded to get remote libvirt({0})'s guest ip: ({1})".format(
                remote_host, guest_ip
            )
        )
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-libvirt-remote", ssh_guest)
        mode_queue.put((mode_type, guest_ip))

    def guest_libvirt_local_setup(self, ssh_libvirt):
        guest_name = deploy.libvirt.guest_name
        guest_user = deploy.libvirt.guest_user
        guest_passwd = deploy.libvirt.guest_passwd
        self.libvirt_pkg_install(ssh_libvirt)
        self.bridge_setup("br0", ssh_libvirt)
        self.libvirt_guests_all_clean(ssh_libvirt)
        guest_ip = self.libvirt_guest_add(guest_name, ssh_libvirt)
        logger.info(
            "Succeeded to get local libvirt({0})'s guest ip: ({1})".format(
                ssh_libvirt["host"], guest_ip
            )
        )
        ssh_guest = {"host": guest_ip, "username": guest_user, "password": guest_passwd}
        self.system_init("ci-guest-libvirt-local", ssh_guest)
        return guest_ip

    # def guest_vdsm_setup(self, ssh_vdsm):
    #     rhevm_ip = deploy.vdsm.rhevm_ip
    #     rhevm_ssh_user = deploy.vdsm.rhevm_ssh_user
    #     rhevm_ssh_passwd = deploy.vdsm.rhevm_ssh_passwd
    #     rhevm_admin_user = deploy.vdsm.rhevm_admin_user
    #     rhevm_admin_passwd = deploy.vdsm.rhevm_admin_passwd
    #     guest_name = deploy.vdsm.guest_name
    #     guest_user = deploy.vdsm.guest_user
    #     guest_passwd = deploy.vdsm.guest_passwd
    #     cluster = deploy.vdsm.cluster
    #     cputype = deploy.vdsm.cputype
    #     template = deploy.vdsm.template
    #     disk = deploy.vdsm.disk
    #     datacenter = deploy.vdsm.datacenter
    #     storage = deploy.vdsm.storage
    #     ssh_rhevm = {"host":rhevm_ip,"username":rhevm_ssh_user,"password":rhevm_ssh_passwd}
    #     rhevm_version = self.rhevm_version_get(ssh_rhevm)
    #     rhevm_admin_server = self.rhevm_admin_get(ssh_rhevm)
    #     rhevm_shell, rhevm_shellrc = self.rhevm_shell_get(ssh_rhevm)
    #     self.vdsm_host_init(ssh_vdsm, rhevm_version)
    #     self.rhevm_shell_config(ssh_rhevm, rhevm_admin_server, rhevm_admin_user, rhevm_admin_passwd)
    #     self.rhevm_cpu_set(ssh_rhevm, rhevm_shell, cluster, cputype)
    #     self.rhevm_template_ready(ssh_rhevm, rhevm_shell, template, disk)
    #     self.rhevm_hosts_all_clean(ssh_rhevm, rhevm_shell)
    #     self.rhevm_host_ready(ssh_rhevm, rhevm_shell, ssh_vdsm, datacenter, storage)
    #     guest_ip = self.rhevm_guest_add(ssh_rhevm, rhevm_shell, ssh_vdsm, guest_name, template, cluster, disk)
    #     logger.info("Succeeded to get rhevm({0}) guest ip: {1} for vdsm mode".format(rhevm_ip, guest_ip))
    #     ssh_guest = {"host":guest_ip, "username":guest_user, "password":guest_passwd}
    #     self.system_init("ci-guest-vdsm", ssh_guest)
    #     return guest_ip

    # *********************************************
    # Hypervisor ESXi Function
    # *********************************************
    def vcenter_cert(self, admin_server, admin_user, admin_passwd):
        cert = (
            "powershell Connect-VIServer -Server %s -Protocol https -User %s -Password %s;"
            % (admin_server, admin_user, admin_passwd)
        )
        return cert

    def vcenter_host_get(self, cert, ssh_cli, guest_name):
        cmd = "%s Get-VM %s | select *" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            for line in output.splitlines():
                if re.match(r"^VMHost .*:", line):
                    host = line.split(":")[1].strip()
                    return host
        else:
            raise FailException("Failed to get vcenter host")

    def vcenter_fqdn_set(self, cert, ssh_cli, esx_host, fqdn):
        cmd = "%s (Get-EsxCli -VMhost %s).system.hostname.set($null, '%s', $null)" % (
            cert,
            esx_host,
            fqdn,
        )
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            return self.vcenter_fqdn_get(cert, ssh_cli, esx_host)
        else:
            raise FailException("Failed to set vcenter host fqdn")

    def vcenter_fqdn_get(self, cert, ssh_cli, esx_host):
        cmd = (
            "%s (Get-EsxCli -VMhost %s).system.hostname.get()|select FullyQualifiedDomainName"
            % (cert, esx_host)
        )
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            for line in output.splitlines():
                if re.match(r"^FullyQualifiedDomainName .*:", line):
                    fqdn = line.split(":")[1].strip()
                    return fqdn
        else:
            raise FailException("Failed to get vcenter host fqdn")

    def vcenter_host_exist(self, cert, ssh_cli, esx_host):
        cmd = "%s Get-VMHost -Name %s" % (cert, esx_host)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            return True
        else:
            return False

    def vcenter_host_ready(self, cert, ssh_cli, ssh_esx):
        if self.vcenter_host_exist(cert, ssh_cli, ssh_esx["host"]):
            return "ready"
        else:
            self.vcenter_host_add(cert, ssh_cli, ssh_esx)

    def vcenter_host_uuid(self, cert, ssh_cli, esx_host):
        cmd = "%s Get-VMHost -Name %s | %%{(Get-View $_.Id).Hardware.SystemInfo}" % (
            cert,
            esx_host,
        )
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            for line in output.splitlines():
                if re.match(r"^Uuid.*:", line):
                    uuid = line.split(":")[1].strip()
                    logger.info("Succeeded to get esxi host uuid: {0}".format(uuid))
                    return uuid
        else:
            raise FailException("Failed to get esx host uuid")

    def vcenter_host_hwuuid(self, cert, ssh_cli, esx_host):
        cmd = "%s Get-VMHost -Name %s | %%{(Get-View $_.Id).MoRef}" % (cert, esx_host)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0 and "HostSystem" in output:
            for line in output.splitlines():
                if re.match(r"^Value.*:", line):
                    hwuuid = line.split(":")[1].strip()
                    logger.info("Succeeded to get esxi host hwuuid: {0}".format(hwuuid))
                    return hwuuid
        else:
            raise FailException("Failed to get esx host hwuuid")

    def vcenter_host_datastore(self, cert, ssh_cli, esx_host):
        cmd = "%s Get-Datastore -VMHost %s | %%{(Get-View $_.Id)}" % (cert, esx_host)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            for line in output.splitlines():
                if re.match(r"^Name.*:", line):
                    datastore = line.split(":")[1].strip()
                    return datastore
        else:
            raise FailException("Failed to get esx host datastore")

    def vcenter_host_add(self, cert, ssh_cli, ssh_esx):
        esx_host = ssh_esx["host"]
        esx_host_user = ssh_esx["username"]
        esx_host_passwd = ssh_esx["password"]
        cmd = (
            "%s Add-VMHost %s -Location Datacenter -User %s -Password %s -confirm:$false"
            % (cert, esx_host, esx_host_user, esx_host_passwd)
        )
        ret, output = self.runcmd(cmd, ssh_cli)
        if self.vcenter_host_exist(cert, ssh_cli, esx_host) is False:
            raise FailException("Failed to add esx host {0}".format(esx_host))

    def vcenter_host_delete(self, cert, ssh_cli, esx_host):
        cmd = "%s Remove-VMHost %s -confirm:$false" % (cert, esx_host)
        ret, output = self.runcmd(cmd, ssh_cli)
        if self.vcenter_host_exist(cert, ssh_cli, esx_host):
            raise FailException("Failed to delete esx host")

    def vcenter_guest_images(self, ssh_esx, guest_name, image_path):
        cmd = "rm -rf /vmfs/volumes/datastore*/{0}*; wget -P /vmfs/volumes/datastore* {1}".format(
            guest_name, image_path
        )
        ret, output = self.runcmd(cmd, ssh_esx)
        if ret != 0:
            raise FailException("Failed to download guest image")
        cmd = "tar -zxvf /vmfs/volumes/datastore*/{0}.tar.gz -C /vmfs/volumes/datastore*/".format(
            guest_name
        )
        ret, output = self.runcmd(cmd, ssh_esx)
        if ret != 0:
            raise FailException("Failed to uncompress guest image")
        cmd = "rm -f /vmfs/volumes/datastore*/*.tar.gz"
        ret, output = self.runcmd(cmd, ssh_esx)

    def vcenter_guest_exist(self, cert, ssh_cli, guest_name):
        cmd = "%s Get-VM -Name %s" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            return True
        else:
            return False

    def vcenter_guest_uuid(self, cert, ssh_cli, guest_name):
        cmd = "%s Get-VM %s | %%{(Get-View $_.Id).config}" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            version = ""
            uuid = ""
            for line in output.splitlines():
                if re.match(r"^Version.*:", line):
                    version = line.split(":")[1].strip()
                if re.match(r"^Uuid.*:", line):
                    uuid = line.split(":")[1].strip()
            if uuid:
                if version > "vmx-13":
                    uuid = (
                        uuid[6:8]
                        + uuid[4:6]
                        + uuid[2:4]
                        + uuid[0:2]
                        + "-"
                        + uuid[11:13]
                        + uuid[9:11]
                        + "-"
                        + uuid[16:18]
                        + uuid[14:16]
                        + "-"
                        + uuid[19:]
                    )
                logger.info("Succeeded to get vcenter guest uuid: {0}".format(uuid))
                return uuid
            else:
                raise FailException("Failed to get vcenter guest uuid")
        else:
            raise FailException("Failed to get vcenter guest uuid")

    def vcenter_guest_status(self, cert, ssh_cli, guest_name):
        cmd = "%s Get-VM -Name %s" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            for line in output.splitlines():
                if re.match(r"^PowerState.*:", line):
                    status = line.split(":")[1].strip()
                    return status
        else:
            raise FailException("Failed to get esx guest status")

    def vcenter_guest_ip(self, cert, ssh_cli, guest_name):
        cmd = "%s Get-VM %s | %%{(Get-View $_.Id).Guest}" % (cert, guest_name)
        for i in range(10):
            ret, output = self.runcmd(cmd, ssh_cli)
            if ret == 0 and "IpAddress" in output:
                datalines = output.splitlines()
                for line in datalines:
                    if re.match(r"^IpAddress.*:", line):
                        guest_ip = line.split(":")[1].strip()
                        if (
                            guest_ip != ""
                            and guest_ip is not None
                            and self.ping_is_connected(guest_ip)
                        ):
                            return guest_ip
            logger.info("No guest ip found for vcenter, try again after 30s...")
            time.sleep(30)

    def vcenter_guest_add(self, cert, ssh_cli, ssh_esx, guest_name, image_path):
        esx_host = ssh_esx["host"]
        if self.vcenter_guest_exist(cert, ssh_cli, guest_name):
            self.vcenter_guest_delete(cert, ssh_cli, guest_name)
        self.vcenter_guest_images(ssh_esx, guest_name, image_path)
        datastore = self.vcenter_host_datastore(cert, ssh_cli, esx_host)
        vmxFile = "'[{0}] {1}/{1}.vmx'".format(datastore, guest_name)
        cmd = "%s New-VM -VMFilePath %s -VMHost %s" % (cert, vmxFile, esx_host)
        ret, output = self.runcmd(cmd, ssh_cli)
        if self.vcenter_guest_exist(cert, ssh_cli, guest_name):
            logger.info("Succeeded to add vcenter guest")
        else:
            raise FailException("Failed to add vcenter guest")
        return self.vcenter_guest_start(cert, ssh_cli, guest_name)

    def vcenter_guest_delete(self, cert, ssh_cli, guest_name):
        if self.vcenter_guest_status(cert, ssh_cli, guest_name) == "PoweredOn":
            self.vcenter_guest_stop(cert, ssh_cli, guest_name)
        for i in range(5):
            cmd = "%s Remove-VM -VM %s -DeletePermanently -Confirm:$false" % (
                cert,
                guest_name,
            )
            ret, output = self.runcmd(cmd, ssh_cli)
            if ret != 0 and "Powered on" in output:
                logger.info("guest still power on, try again")
                self.vcenter_guest_stop(cert, ssh_cli, guest_name)
            elif self.vcenter_guest_exist(cert, ssh_cli, guest_name):
                logger.info("guest still exist, try again")
            else:
                logger.info("Succeeded to delete vcenter guest")
                return True
            time.sleep(10)
        raise FailException("Failed to delete vcenter guest")

    def vcenter_guest_start(self, cert, ssh_cli, guest_name):
        cmd = "%s Start-VM -VM %s -Confirm:$false" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        for i in range(10):
            cmd = (
                '%s Get-VM %s | Get-VMQuestion | Set-VMQuestion -Option "button.uuid.copiedTheVM" -Confirm:$false'
                % (cert, guest_name)
            )
            ret, output = self.runcmd(cmd, ssh_cli, desc="vcenter guest question check")
            time.sleep(30)
            if self.vcenter_guest_status(cert, ssh_cli, guest_name) == "PoweredOn":
                logger.info("Succeeded to start vcenter guest")
                guest_ip = self.vcenter_guest_ip(cert, ssh_cli, guest_name)
                return guest_ip
            logger.warning(
                "vcenter guest status is not PoweredOn, check again after 15s..."
            )
        raise FailException("Failed to start vcenter guest")

    def vcenter_guest_stop(self, cert, ssh_cli, guest_name):
        cmd = "%s Stop-VM -VM %s -Kill -Confirm:$false" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        for i in range(10):
            if self.vcenter_guest_status(cert, ssh_cli, guest_name) == "PoweredOff":
                logger.info("Succeeded to stop vcenter guest")
                return True
            logger.warning(
                "vcenter guest status is not PoweredOff, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to stop vcenter guest")

    def vcenter_guest_suspend(self, cert, ssh_cli, guest_name):
        cmd = "%s Suspend-VM -VM %s -Confirm:$false" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        for i in range(10):
            if self.vcenter_guest_status(cert, ssh_cli, guest_name) == "Suspended":
                logger.info("Succeeded to suspend vcenter guest")
                return True
            logger.warning(
                "vcenter guest status is not Suspended, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to suspend vcenter guest")

    def vcenter_guest_resume(self, cert, ssh_cli, guest_name):
        cmd = "%s Start-VM -VM %s -Confirm:$false" % (cert, guest_name)
        ret, output = self.runcmd(cmd, ssh_cli)
        for i in range(10):
            if self.vcenter_guest_status(cert, ssh_cli, guest_name) == "PoweredOn":
                logger.info("Succeeded to resume vcenter guest")
                return True
            logger.warning(
                "vcenter guest status is not PoweredOn, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to resume vcenter guest")

    def vcenter_cluster_get(self, cert, ssh_cli, option="Name"):
        cmd = "%s Get-Cluster | select *" % (cert)
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0:
            name_list = []
            for line in output.splitlines():
                if re.match(r"^{} .*:".format(option), line):
                    cluster_name = line.split(":")[1].strip()
                    name_list.append(cluster_name)
            return name_list
        else:
            raise FailException("Failed to get cluster {}".format(option))

    def vcenter_cluster_name_set(self, cert, ssh_cli, old_name, new_name):
        if new_name in self.vcenter_cluster_get(cert, ssh_cli):
            logger.info(
                "The cluster name {} is already exist, no need to reset".format(
                    new_name
                )
            )
            return
        cmd = "{0} Set-Cluster -Cluster {1} -Name {2} -Confirm:$false".format(
            cert, old_name, new_name
        )
        ret, output = self.runcmd(cmd, ssh_cli)
        if ret == 0 and new_name in self.vcenter_cluster_get(cert, ssh_cli):
            logger.info(
                "Succeeded to set the cluster name {0} to {1}".format(
                    old_name, new_name
                )
            )
            return
        else:
            raise FailException("Failed to set the cluster name")

    # *********************************************
    # Hypervisor Hyper-V Function
    # *********************************************
    # *********************************************
    def hyperv_host_uuid(self, ssh_hyperv):
        # Windows UUID needs to be decoded
        cmd = '''powershell "gwmi -namespace 'root/cimv2' Win32_ComputerSystemProduct | select *"'''
        ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv host uuid check")
        if ret == 0 and "UUID" in output:
            for line in output.splitlines():
                if re.match(r"^UUID.*:", line):
                    s = line.split(":")[1].strip()
                    uuid = (
                        s[6:8]
                        + s[4:6]
                        + s[2:4]
                        + s[0:2]
                        + "-"
                        + s[11:13]
                        + s[9:11]
                        + "-"
                        + s[16:18]
                        + s[14:16]
                        + s[18:]
                    )
                    logger.info("Succeeded to get hyperv host uuid: %s" % uuid)
                    return uuid
        else:
            raise FailException("Failed to get hyperv host uuid")

    def hyperv_host_name(self, ssh_hyperv):
        cmd = "powershell (Get-WMIObject  Win32_ComputerSystem).DNSHostName"
        ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv host name check")
        if ret == 0 and output.strip() is not None:
            hostname = output.strip()
            logger.info("Succeeded to get hyperv hostname: {0}".format(hostname))
            return hostname
        else:
            raise FailException("Failed to get hyperv hostname")

    def hyperv_image_ready(self, ssh_hyperv, guest_name, image_path):
        cmd = "powershell New-Item -path C:\ -Name hyperv_img -Type Directory"
        ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv image dir create")
        cmd = "powershell Get-ChildItem C:\hyperv_img"
        ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv image list")
        if ret == 0 and guest_name in output:
            logger.info("hyperv image is exist")
        else:
            cmd = (
                "powershell (New-Object System.Net.WebClient).DownloadFile('%s', 'C:\hyperv_img\%s.vhdx')"
                % (image_path, guest_name)
            )
            ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv image download")
            if ret == 0:
                logger.info("succeeded to download hyperv image")
            else:
                raise FailException("Failed to download hyperv image")

    def hyperv_guest_exist(self, ssh_hyperv, guest_name):
        cmd = "powershell Get-VM"
        ret, output = self.runcmd(cmd, ssh_hyperv)
        if ret == 0 and guest_name in output:
            return True
        else:
            return False

    def hyperv_guest_uuid(self, ssh_hyperv, guest_name):
        cmd = "powershell (gwmi -Namespace Root\Virtualization\V2 -ClassName Msvm_VirtualSystemSettingData).BiosGUID"
        ret, output = self.runcmd(cmd, ssh_hyperv)
        if ret == 0 and output.strip() is not None:
            s = output.strip()
            if s.startswith("{") and s.endswith("}"):
                s = s[1:-1]
            uuid = (
                s[6:8]
                + s[4:6]
                + s[2:4]
                + s[0:2]
                + "-"
                + s[11:13]
                + s[9:11]
                + "-"
                + s[16:18]
                + s[14:16]
                + s[18:]
            )
            logger.info("Succeeded to get hyperv guest uuid: {0}".format(uuid))
            return uuid
        else:
            raise FailException("Failed to get hyperv guest uuid")

    def hyperv_guest_status(self, ssh_hyperv, guest_name):
        cmd = '''powershell "Get-VM %s | select *"''' % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        if ret == 0 and output != "":
            for line in output.splitlines():
                if re.match(r"^State", line):
                    status = line.split(":")[1].strip()
                    return status
        else:
            raise FailException("Failed to check hyperv guest status")

    def hyperv_guest_ip(self, ssh_hyperv, guest_name):
        cmd = "powershell (Get-VMNetworkAdapter -VMName %s).IpAddresses" % (guest_name)
        for i in range(20):
            time.sleep(30)
            ret, output = self.runcmd(cmd, ssh_hyperv)
            if ret == 0 and output != "":
                datalines = output.splitlines()
                for line in datalines:
                    if ":" not in line and re.match(r"^10", line):
                        guest_ip = line.strip()
                        if self.ping_is_connected(guest_ip):
                            return guest_ip
            logger.info("No guest ip found for hyperv, try again after 30s...")

    def hyperv_guest_add(self, ssh_hyperv, guest_name, image_path):
        if self.hyperv_guest_exist(ssh_hyperv, guest_name):
            self.hyperv_guest_delete(ssh_hyperv, guest_name)
        self.hyperv_image_ready(ssh_hyperv, guest_name, image_path)
        if "8." in guest_name:
            options = "-MemoryStartupBytes 2GB -SwitchName virtual_switch -Generation 2"
        else:
            options = "-MemoryStartupBytes 1GB -SwitchName virtual_switch -Generation 1"
        cmd = 'powershell New-VM -Name %s -VHDPath "C:\hyperv_img\%s.vhdx" %s' % (
            guest_name,
            guest_name,
            options,
        )
        ret, output = self.runcmd(cmd, ssh_hyperv, desc="hyperv guest add")
        if self.hyperv_guest_exist(ssh_hyperv, guest_name):
            logger.info("Succeeded to add hyperv guest")
        else:
            raise FailException("Failed to add hyperv guest")
        if "8." in guest_name:
            cmd = (
                "powershell Set-VMFirmware -VMName %s -EnableSecureBoot off"
                % guest_name
            )
            ret, output = self.runcmd(cmd, ssh_hyperv, desc="disable secure boot")
        return self.hyperv_guest_start(ssh_hyperv, guest_name)

    def hyperv_guest_delete(self, ssh_hyperv, guest_name):
        if self.hyperv_guest_status(ssh_hyperv, guest_name) != "Off":
            self.hyperv_guest_stop(ssh_hyperv, guest_name)
        cmd = "powershell Remove-VM %s -force" % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        if self.hyperv_guest_exist(ssh_hyperv, guest_name):
            raise FailException("Failed to delete hyperv guest")
        else:
            logger.info("Succeeded to delete hyperv guest")

    def hyperv_guest_start(self, ssh_hyperv, guest_name):
        cmd = "powershell Start-VM -Name %s" % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        for i in range(10):
            if self.hyperv_guest_status(ssh_hyperv, guest_name) == "Running":
                logger.info("Succeeded to start hyperv guest")
                guest_ip = self.hyperv_guest_ip(ssh_hyperv, guest_name)
                return guest_ip
            logger.warning(
                "hyperv guest status is not Running, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to start hyper guest")

    def hyperv_guest_stop(self, ssh_hyperv, guest_name):
        cmd = "powershell Stop-VM -Name %s" % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        for i in range(10):
            if self.hyperv_guest_status(ssh_hyperv, guest_name) == "Off":
                logger.info("Succeeded to stop hyperv guest")
                return True
            logger.warning("hyperv guest status is not Off, check again after 15s...")
            time.sleep(15)
        raise FailException("Failed to stop hyperv guest")

    def hyperv_guest_suspend(self, ssh_hyperv, guest_name):
        cmd = "powershell Suspend-VM -Name %s" % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        for i in range(10):
            if self.hyperv_guest_status(ssh_hyperv, guest_name) == "Paused":
                logger.info("Succeeded to suspend hyperv guest")
                return True
            logger.warning(
                "hyperv guest status is not Paused, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to suspend hyperv guest")

    def hyperv_guest_resume(self, ssh_hyperv, guest_name):
        cmd = "powershell Resume-VM -Name %s" % (guest_name)
        ret, output = self.runcmd(cmd, ssh_hyperv)
        for i in range(10):
            if self.hyperv_guest_status(ssh_hyperv, guest_name) == "Running":
                logger.info("Succeeded to resume hyperv guest")
                return True
            logger.warning(
                "hyperv guest status is not Running, check again after 15s..."
            )
            time.sleep(15)
        raise FailException("Failed to resume hyperv guest")

    # *********************************************
    # Hypervisor XEN Function
    # *********************************************
    def xen_host_ready(self, ssh_xen, sr_name, sr_server, sr_path):
        hostname = self.get_hostname(ssh_xen)
        ret, output = self.runcmd("xe host-list", ssh_xen)
        if ret == 0 and hostname in output:
            ret, output = self.runcmd(
                "xe sr-list name-label={0}".format(sr_name), ssh_xen
            )
            if ret == 0 and sr_name in output:
                logger.info("xen sr is ready")
            else:
                nfs_options = (
                    "type=nfs name-label={0} content-type=user shared=true".format(
                        sr_name
                    )
                )
                nfs_server = (
                    "device-config:nfsversion=4 device-config:server={0}".format(
                        sr_server
                    )
                )
                nfs_path = "device-config:serverpath={0}".format(sr_path)
                cmd = "xe sr-create {0} {1} {2}".format(
                    nfs_options, nfs_server, nfs_path
                )
                ret, output = self.runcmd(cmd, ssh_xen)
        else:
            raise FailException("xen host is not ready")

    def xen_host_uuid(self, ssh_xen):
        cmd = "xe host-list address={0} | grep '^uuid'".format(ssh_xen["host"])
        ret, output = self.runcmd(cmd, ssh_xen)
        if ret == 0 and "uuid" in output:
            uuid = output.strip().split(":")[1].strip()
            return uuid
        else:
            raise FailException("Failed to get xen host uuid")

    def xen_sr_uuid(self, ssh_xen, sr_name):
        cmd = "xe sr-list name-label={0} |grep '^uuid'".format(sr_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        if ret == 0 and "uuid" in output:
            uuid = output.strip().split(":")[1].strip()
            return uuid
        else:
            raise FailException("Failed to check xen sr uuid")

    def xen_guest_exist(self, ssh_xen, guest_name):
        cmd = "xe vm-list name-label={0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        if guest_name in output:
            return True
        else:
            return False

    def xen_guest_status(self, ssh_xen, guest_name):
        cmd = "xe vm-list name-label={0} | grep 'power-state'".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        if ret == 0 and "power-state" in output:
            status = output.strip().split(":")[1].strip()
            return status
        else:
            raise FailException("Failed to check xen guest status")

    def xen_guest_uuid(self, ssh_xen, guest_name):
        cmd = "xe vm-list name-label={0} | grep '^uuid'".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        if ret == 0 and "uuid" in output:
            uuid = output.strip().split(":")[1].strip()
            return uuid
        else:
            raise FailException("Failed to check xen guest uuid")

    def xen_guest_mac(self, ssh_xen, guest_name):
        cmd = "xe vm-vif-list vm={0} |grep 'MAC'".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        if ret == 0 and "MAC" in output:
            mac_addr = output.strip().split("MAC ( RO):")[1].strip()
            return mac_addr
        else:
            raise FailException("Failed to check xen guest mac addr")

    def xen_guest_ip(self, ssh_xen, guest_name):
        for i in range(3):
            if self.xen_guest_exist(ssh_xen, guest_name) is False:
                break
            if self.xen_guest_status(ssh_xen, guest_name) != "running":
                break
            mac_addr = self.xen_guest_mac(ssh_xen, guest_name)
            guest_ip = self.get_ipaddr_bymac(mac_addr, ssh_xen)
            if (
                guest_ip is not False
                and guest_ip is not None
                and guest_ip != ""
                and self.ping_is_connected(guest_ip)
            ):
                return guest_ip
            logger.info("No guest ip found for xen, try again after 15s...")
            time.sleep(15)

    def xen_guest_add(self, ssh_xen, guest_name, sr_name, image_path):
        if self.xen_guest_exist(ssh_xen, guest_name):
            self.xen_guest_delete(ssh_xen, guest_name)
        sr_uuid = self.xen_sr_uuid(ssh_xen, sr_name)
        cmd = "xe vm-import url={0} sr-uuid={1}".format(image_path, sr_uuid)
        ret, output = self.runcmd(cmd, ssh_xen, desc="xen image import")
        if ret == 0 and self.xen_guest_exist(ssh_xen, guest_name):
            logger.info("Succeeded to import xen guest")
        else:
            raise FailException("Failed to import xen guest")
        host_uuid = self.xen_host_uuid(ssh_xen)
        guest_uuid = self.xen_guest_uuid(ssh_xen, guest_name)
        cmd = "xe vm-param-set uuid={0} affinity={1}".format(guest_uuid, host_uuid)
        self.runcmd(cmd, ssh_xen, desc="xen vm assign to host")
        return self.xen_guest_start(ssh_xen, guest_name)

    def xen_guest_delete(self, ssh_xen, guest_name):
        if self.xen_guest_status(ssh_xen, guest_name) != "halted":
            self.xen_guest_stop(ssh_xen, guest_name)
        guest_uuid = self.xen_guest_uuid(ssh_xen, guest_name)
        cmd = "xe vm-destroy uuid={0}".format(guest_uuid)
        ret, output = self.runcmd(cmd, ssh_xen)
        time.sleep(30)
        if self.xen_guest_exist(ssh_xen, guest_name):
            raise FailException("Failed to delete xen guest")
        else:
            logger.info("Succeeded to delete xen guest")

    def xen_guest_start(self, ssh_xen, guest_name):
        for i in range(3):
            cmd = "xe vm-start vm={0}".format(guest_name)
            ret, output = self.runcmd(cmd, ssh_xen, desc="xen guest start")
            if self.xen_guest_status(ssh_xen, guest_name) == "running":
                guest_ip = self.xen_guest_ip(ssh_xen, guest_name)
                if guest_ip is not False and guest_ip is not None and guest_ip != "":
                    return guest_ip
            logger.warning("Failed to start xen guest, try again after 15s...")
            self.xen_guest_stop(ssh_xen, guest_name)
            time.sleep(15)
        raise FailException("Failed to start xen guest")

    def xen_guest_stop(self, ssh_xen, guest_name):
        cmd = "xe vm-shutdown vm={0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        for i in range(10):
            if self.xen_guest_status(ssh_xen, guest_name) == "halted":
                logger.info("Succeeded to stop xen guest")
                return True
            logger.warning("xen guest status is not halted, check again after 15s... ")
            time.sleep(15)
        raise FailException("Failed to stop xen guest")

    def xen_guest_suspend(self, ssh_xen, guest_name):
        cmd = "xe vm-suspend vm={0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        for i in range(10):
            if self.xen_guest_status(ssh_xen, guest_name) == "suspended":
                logger.info("Succeeded to suspend xen guest")
                return True
            logger.warning(
                "xen guest status is not suspended, check again after 15s... "
            )
            time.sleep(15)
        raise FailException("Failed to suspend guest")

    def xen_guest_resume(self, ssh_xen, guest_name):
        cmd = "xe vm-resume vm={0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_xen)
        for i in range(10):
            if self.xen_guest_status(ssh_xen, guest_name) == "running":
                logger.info("Succeeded to resume xen guest")
                return True
            logger.warning("xen guest status is not running, check again after 15s... ")
            time.sleep(15)
        raise FailException("Failed to resume xen guest")

    # *********************************************
    # Hypervisor Kubvirt Function
    # *********************************************

    def kubevirt_request(self, path):
        header_params = {}
        header_params["Accept"] = "application/json"
        header_params["Content-Type"] = "application/json"
        header_params["Authorization"] = "Bearer {0}".format(deploy.kubevirt.token)
        url = deploy.kubevirt.endpoint + path
        http = urllib3.PoolManager(
            cert_reqs="CERT_NONE",
            num_pools=4,
            maxsize=4,
        )
        r = http.request("GET", url, headers=header_params, retries=5)
        if PY3:
            data = r.data.decode("utf8")
        else:
            data = r.data

        try:
            data = json.loads(data)
        except ValueError:
            data = r.data
        return data

    def kubevirt_version(self):
        versions = self.kubevirt_request("/apis/kubevirt.io")
        return versions["preferredVersion"]["version"]

    def kubevirt_guest_attrs(self, guest_name):
        version = self.kubevirt_version()
        vms = self.kubevirt_request(
            "/apis/kubevirt.io/" + version + "/virtualmachineinstances"
        )
        guest_attrs = {}
        for vm in vms["items"]:
            if vm["metadata"]["name"] == guest_name:
                guest_attrs["guest_id"] = vm["spec"]["domain"]["firmware"]["uuid"]
                guest_attrs["guest_node"] = vm["status"]["nodeName"]
                guest_attrs["guest_status"] = vm["status"]["phase"]
        return guest_attrs

    def kubevirt_host_attrs(self, node_name):
        nodes = self.kubevirt_request("/api/v1/nodes")
        host_attrs = {}
        for node in nodes["items"]:
            if node["metadata"]["name"] == node_name:
                host_attrs["host_uuid"] = node["status"]["nodeInfo"]["machineID"]
                for addr in node["status"]["addresses"]:
                    if addr["type"] == "Hostname":
                        host_attrs["host_name"] = addr["address"]
        return host_attrs

    def kubevirt_guest_ip(self, guest_name):
        guest_attrs = self.kubevirt_guest_attrs(guest_name)
        guest_port = deploy.kubevirt.guest_port
        guest_ip = "{0}:{1}".format(guest_attrs["guest_node"], guest_port)
        return guest_ip

    # *********************************************
    # Hypervisor Nutanix Function
    # *********************************************

    def ahv_guest_ip(self):
        return deploy.ahv.guest_ip

    def ahv_guest_uuid(self):
        return deploy.ahv.guest_uuid

    def ahv_host_uuid(self):
        return deploy.ahv.host_uuid

    def ahv_host_name(self):
        return deploy.ahv.host_name

    # *********************************************
    # Hypervisor Libvirt Function
    # *********************************************
    def libvirt_host_uuid(self, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh capabilities |grep '<uuid>'"
        ret, output = self.runcmd(cmd, ssh_libvirt)
        if ret == 0 and "uuid" in output:
            uuid = re.findall(r"<uuid>(.*?)</uuid>", output)[-1].strip()
            logger.info(
                "Succeeded to get libvirt host({0}) uuid is: {1}".format(host, uuid)
            )
            return uuid
        else:
            raise FailException("Failed to check libvirt host({0}) uuid".format(host))

    def libvirt_pkg_install(self, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "yum clean all; yum install -y \
                @virtualization-client @virtualization-hypervisor @virtualization-platform @virtualization-tools \
                nmap libguestfs-tools net-tools iproute rpcbind libvirt virt-manager"
        status, output = self.run_loop(
            cmd, ssh_libvirt, desc="install libvirt and related packages"
        )
        if status != "Yes":
            raise FailException(
                "Failed to install libvirt packages in {0}".format(host)
            )
        logger.info("Succeeded to install libvirt packages in {0}".format(host))
        cmd = "service libvirtd start"
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="restart libvirtd service")
        if ret == 0:
            logger.info("Succeeded to start libvirtd service in {0}".format(host))
        else:
            raise FailException("Failed to start libvirtd service in {0}".format(host))

    def libvirt_image_exist(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        image_path = deploy.libvirt.image_path
        xml_path = deploy.libvirt.xml_path
        guest_image = "{0}/{1}.qcow2".format(image_path, guest_name)
        guest_xml = "{0}/{1}.xml".format(xml_path, guest_name)
        cmd = "ls {0}; ls {1}".format(guest_image, guest_xml)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt image and xml check")
        if ret == 0 and "No such file or directory" not in output:
            logger.info("libvirt image and xml exist in {0}".format(host))
            return True
        else:
            logger.info("libvirt image and xml not exist in {0}".format(host))
            return False

    def libvirt_image_download(self, guest_name, ssh_libvirt):
        image_url = deploy.libvirt.image_url
        xml_url = deploy.libvirt.xml_url
        image_path = deploy.libvirt.image_path
        xml_path = deploy.libvirt.xml_path
        guest_image = "{0}/{1}.qcow2".format(image_path, guest_name)
        guest_xml = "{0}/{1}.xml".format(xml_path, guest_name)
        if self.url_validation(image_url) is False:
            raise FailException("image_url is not available")
        if self.url_validation(xml_url) is False:
            raise FailException("xml_url is not available")
        if self.libvirt_image_exist(guest_name, ssh_libvirt) is False:
            cmd = "rm -f {0}; rm -rf {1}; mkdir -p {1}; chmod a+rwx {1}".format(
                guest_xml, image_path
            )
            self.runcmd(cmd, ssh_libvirt, desc="libvirt image path clean and create")
            for i in range(5):
                cmd = "curl -L {0} -o {1}".format(image_url, guest_image)
                ret, output = self.runcmd(
                    cmd, ssh_libvirt, desc="libvirt image download"
                )
                if ret == 0:
                    break
                logger.warning("Failed to download libvirt image, try again...")
            for i in range(5):
                cmd = "curl -L {0} -o {1}".format(xml_url, guest_xml)
                ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt xml download")
                if ret == 0:
                    break
                logger.warning("Failed to download libvirt xml file, try again...")
            cmd = "sed -i -e 's|<name>.*</name>|<name>{0}</name>|g' {1}".format(
                guest_name, guest_xml
            )
            self.runcmd(cmd, ssh_libvirt, desc="libvirt xml guest_name update")
            cmd = "sed -i -e 's|<source file=.*/>|<source file=\"{0}\"/>|g' {1}".format(
                guest_image, guest_xml
            )
            self.runcmd(cmd, ssh_libvirt, desc="libvirt xml source file update")
            guest_mac = self.randomMAC()
            cmd = "sed -i -e 's|<mac address=.*/>|<mac address=\"{0}\"/>|g' {1}".format(
                guest_mac, guest_xml
            )
            self.runcmd(cmd, ssh_libvirt, desc="libvirt xml mac address update")
            if self.rhel_version(ssh_libvirt) == "9":
                cmd = "sed -i -e 's|<graphics type=.* |<graphics type=\"vnc\" |g' {0}".format(
                    guest_xml
                )
                self.runcmd(cmd, ssh_libvirt, desc="libvirt graphics type update")
        cmd = "virsh define {0}".format(guest_xml)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt define guest")
        logger.info(
            "Succeeded to download libvirt image to {0}".format(ssh_libvirt["host"])
        )

    def libvirt_guest_exist(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh  dominfo {0} | grep '^Name'".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt guest exist check")
        if ret == 0 and guest_name in output:
            logger.info("libvirt({0}) guest {1} is exist".format(host, guest_name))
            return True
        else:
            logger.info("libvirt({0}) guest {1} is not exist".format(host, guest_name))
            return False

    def libvirt_guest_uuid(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh domuuid {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt guest uuid check")
        if ret == 0 and output is not None:
            uuid = output.strip()
            logger.info(
                "Succeeded to get libvirt({0}) guest uuid: {1}".format(host, uuid)
            )
            return uuid
        else:
            raise FailException("Failed to check libvirt({0}) guest uuid".format(host))

    def libvirt_guest_status(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh  domstate {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt guest status check")
        if ret == 0 and output.strip() is not None and output.strip() != "":
            status = output.strip()
            logger.info("libvirt({0}) guest status is: {1}".format(host, status))
            return status
        else:
            logger.info("Failed to check libvirt({0}) guest status".format(host))
            return "false"

    def libvirt_guests_all_clean(self, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh list --name  --all"
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt all guests list")
        if ret == 0 and output is not None and output != "":
            vms = output.strip().split("\n")
            if len(vms) > 0:
                for guest_name in vms:
                    self.libvirt_guest_delete(guest_name, ssh_libvirt)
        cmd = "sync;sync;sync;echo 1 > /proc/sys/vm/drop_caches"
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="clean memory cache")
        logger.info("Finished to clean all the libvirt({0}) guests".format(host))

    def libvirt_guest_mac(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh dumpxml {0} | grep 'mac address'".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="virsh dumpxml for mac")
        if ret == 0:
            mac_addr = re.findall(r"mac address='(.*?)'", output)[0]
            if mac_addr is not None or mac_addr != "":
                logger.info(
                    "Succeeded to get libvirt({0}) guest mac: {1}".format(
                        host, mac_addr
                    )
                )
                return mac_addr
        raise FailException("Failed to get libvirt({0}) guest mac address".format(host))

    def libvirt_guest_ip(self, guest_name, ssh_libvirt):
        for i in range(3):
            if self.libvirt_guest_exist(guest_name, ssh_libvirt) is False:
                break
            if self.libvirt_guest_status(guest_name, ssh_libvirt) != "running":
                break
            mac_addr = self.libvirt_guest_mac(guest_name, ssh_libvirt)
            guest_ip = self.get_ipaddr_bymac(mac_addr, ssh_libvirt)
            if guest_ip is not False and guest_ip is not None and guest_ip != "":
                return guest_ip
            logger.info("No guest ip found for libvirt, try again after 15s...")
            time.sleep(15)

    def libvirt_guest_add(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        if self.libvirt_guest_exist(guest_name, ssh_libvirt):
            self.libvirt_guest_delete(guest_name, ssh_libvirt)
        self.libvirt_image_download(guest_name, ssh_libvirt)
        for i in range(5):
            if self.libvirt_guest_exist(guest_name, ssh_libvirt):
                logger.info("Succeeded to add libvirt({0}) guest".format(host))
                return self.libvirt_guest_start(guest_name, ssh_libvirt)
            logger.warning("no libvirt guest found, try to search again...")
            time.sleep(15)
        raise FailException("Failed to create libvirt guest")

    def libvirt_guest_delete(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        logger.info("Start to delete libvirt({0}) guest".format(host))
        cmd = "virsh destroy {0}; virsh undefine {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt guest delete")
        if self.libvirt_guest_exist(guest_name, ssh_libvirt):
            raise FailException("Failed to delete libvirt({0}) guest".format(host))
        else:
            logger.info("Succeeded to delete libvirt({0}) guest".format(host))

    def libvirt_guest_start(self, guest_name, ssh_libvirt):
        for i in range(3):
            cmd = "virsh --connect qemu:///system start {0}".format(guest_name)
            ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt start guest ")
            if "Failed to connect socket to '/var/run/libvirt/virtlogd-sock'" in output:
                cmd = "systemctl start virtlogd.socket"
                ret, output = self.runcmd(
                    cmd, ssh_libvirt, desc="start virtlogd.socket"
                )
                cmd = "virsh --connect qemu:///system start {0}".format(guest_name)
                ret, output = self.runcmd(
                    cmd, ssh_libvirt, desc="libvirt start guest again"
                )
            elif "already active" in output:
                cmd = "virsh resume {0}".format(guest_name)
                ret, output = self.runcmd(cmd, ssh_libvirt, desc="libvirt resume guest")
            for i in range(10):
                time.sleep(30)
                if self.libvirt_guest_status(guest_name, ssh_libvirt) == "running":
                    break
            guest_ip = self.libvirt_guest_ip(guest_name, ssh_libvirt)
            if guest_ip is not False and guest_ip is not None and guest_ip != "":
                return guest_ip
            logger.warning("Failed to start libirt guest and try again after 15s...")
            self.libvirt_guest_stop(guest_name, ssh_libvirt)
            time.sleep(15)
        raise FailException(
            "Failed to start libvirt({0}) guest".format(ssh_libvirt["host"])
        )

    def libvirt_guest_stop(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh shutdown {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="virsh shutdown")
        for i in range(10):
            if self.libvirt_guest_status(guest_name, ssh_libvirt) == "shut off":
                logger.info("Succeeded to shutdown libvirt({0}) guest".format(host))
                return True
            logger.warning("libvirt guest is not shut off, check again after 15s...")
            time.sleep(15)
        raise FailException("Failed to shutdown libvirt({0}) guest".format(host))

    def libvirt_guest_suspend(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh suspend {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="virsh suspend")
        for i in range(10):
            if self.libvirt_guest_status(guest_name, ssh_libvirt) == "paused":
                logger.info("Succeeded to pause libvirt({0}) guest".format(host))
                return True
            logger.warning("libvirt guest is not paused, check again after 15s...")
            time.sleep(15)
        raise FailException("Failed to pause libvirt({0}) guest".format(host))

    def libvirt_guest_resume(self, guest_name, ssh_libvirt):
        host = ssh_libvirt["host"]
        cmd = "virsh resume {0}".format(guest_name)
        ret, output = self.runcmd(cmd, ssh_libvirt, desc="virsh resume")
        for i in range(10):
            if self.libvirt_guest_status(guest_name, ssh_libvirt) == "running":
                logger.info("Succeeded to resume libvirt({0}) guest".format(host))
                return True
            logger.warning("libvirt guest is not running, check again after 15s...")
            time.sleep(15)
        raise FailException("Failed to resume libvirt({0}) guest".format(host))

    # *********************************************
    # Hypervisor VDSM and RHEVM function
    # *********************************************
    def rhevm_admin_get(self, ssh_rhevm):
        hostname = self.get_hostname(ssh_rhevm)
        admin_server = "https://{0}:443/ovirt-engine".format(hostname)
        return admin_server

    def rhevm_config_get(self):
        config = dict()
        config["admin_user"] = deploy.rhevm.rhevm_admin_user
        config["admin_passwd"] = deploy.rhevm.rhevm_admin_passwd
        config["master"] = deploy.rhevm.master
        config["master_user"] = deploy.rhevm.master_user
        config["master_passwd"] = deploy.rhevm.master_passwd
        config["slave"] = deploy.rhevm.slave
        config["slave_user"] = deploy.rhevm.slave_user
        config["slave_passwd"] = deploy.rhevm.slave_passwd
        config["datacenter"] = deploy.rhevm.datacenter
        config["cluster"] = deploy.rhevm.cluster
        config["cputype"] = deploy.rhevm.cputype
        config["storage"] = deploy.rhevm.storage
        config["guest_name"] = deploy.rhevm.guest_name
        config["guest_user"] = deploy.rhevm.guest_user
        config["guest_passwd"] = deploy.rhevm.guest_passwd
        config["template"] = deploy.rhevm.template
        config["disk"] = deploy.rhevm.disk
        config["nfs_path"] = deploy.rhevm.nfs_path
        return config

    def rhevm_api_data(self, ssh_rhevm):
        rhevm_config = self.rhevm_config_get()
        rhevm_url = self.rhevm_admin_get(ssh_rhevm)
        api_url = f"{rhevm_url}/api"
        curl_header = (
            f'-H "Accept: application/xml" '
            f'-H "Content-Type: application/xml" '
            f'-H "Version: 4" '
            f'-s -k -u {rhevm_config["admin_user"]}:{rhevm_config["admin_passwd"]}'
        )
        return api_url, curl_header

    def rhevm_host_info_by_guest(self, ssh_rhevm, guest):
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        guest_info = self.rhevm_guest_info(ssh_rhevm, guest)
        host = re.findall(r"<address>(.+?)</address>", guest_info)[0]
        if not host:
            raise FailException(f"Failed to get the host address of {guest}.")
        for i in range(3):
            ret, output = self.runcmd(
                f"curl -X GET {curl_header} {api_url}/hosts?search={host}", ssh_rhevm
            )
            if output and "/ovirt-engine/api/hosts/" in output:
                return output
            logger.warning(f"no results found for {host}, try again after 15s...")
            time.sleep(15)
        raise FailException(f"Failed to get host info of {host}.")

    def rhevm_host_uuid_by_guest(self, ssh_rhevm, guest):
        host_info = self.rhevm_host_info_by_guest(ssh_rhevm, guest)
        host_uuid = re.findall(r"id=\"(.+?)\"", host_info)[0]
        if host_uuid:
            return host_uuid
        raise FailException(f"Failed to get the host uuid of {guest}.")

    def rhevm_host_name_by_guest(self, ssh_rhevm, guest):
        host_info = self.rhevm_host_info_by_guest(ssh_rhevm, guest)
        host_name = re.findall(r"<address>(.+?)</address>", host_info)[0]
        if host_name:
            return host_name
        raise FailException(f"Failed to get the host name of {host_name}")

    def rhevm_host_hwuuid_by_guest(self, ssh_rhevm, guest):
        host_info = self.rhevm_host_info_by_guest(ssh_rhevm, guest)
        host_hwuuid = re.findall(r"<uuid>(.+?)</uuid>", host_info)[0]
        if host_hwuuid:
            return host_hwuuid
        raise FailException(f"Failed to get the host hwuuid of {guest}")

    def rhevm_guest_info(self, ssh_rhevm, guest):
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        cmd = f"curl -X GET {curl_header} {api_url}/vms?search={guest}"
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh_rhevm)
            if output and "/ovirt-engine/api/vms/" in output:
                return output
            logger.warning(f"no results found for {guest}, try again after 15s...")
            time.sleep(15)
        raise FailException(f"Failed to get guest info of {guest}")

    def rhevm_guest_uuid(self, ssh_rhevm, guest):
        guest_info = self.rhevm_guest_info(ssh_rhevm, guest)
        guest_uuid = re.findall(r"id=\"(.+?)\"", guest_info)[0]
        if guest_uuid:
            return guest_uuid
        raise FailException(f"Failed to get the guest uuid for {guest}")

    def rhevm_guest_nic_info(self, ssh_rhevm, guest):
        guest_uuid = self.rhevm_guest_uuid(ssh_rhevm, guest)
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        cmd = f"curl -X GET {curl_header} {api_url}/vms/{guest_uuid}/nics"
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh_rhevm)
            if output and "/ovirt-engine/api/vms/" in output:
                return output
            logger.warning(
                f"no results found for nics of {guest}, try again after 15s..."
            )
            time.sleep(15)
        raise FailException(f"Failed to get nics info of {guest}")

    def rhevm_guest_mac(self, ssh_rhevm, guest):
        nic_info = self.rhevm_guest_nic_info(ssh_rhevm, guest)
        mac = re.findall(r"<address>(.+?)</address>", nic_info)[0]
        if mac:
            return mac
        raise FailException(f"Failed to get the guest mac of {guest}.")

    def rhevm_guest_ip(self, ssh_rhevm, guest):
        mac_addr = self.rhevm_guest_mac(ssh_rhevm, guest)
        guest_ip = self.get_ipaddr_bymac(mac_addr, ssh_rhevm)
        if guest_ip:
            return guest_ip
        raise FailException(f"Failed to get the guest ip of {guest}.")

    def rhevm_guest_status(self, ssh_rhevm, guest):
        guest_info = self.rhevm_guest_info(ssh_rhevm, guest)
        guest_status = re.findall(r"<status>(.+?)</status>", guest_info)[0]
        if guest_status:
            logger.info(
                f"Succeeded to get the guest status({guest_status}) of {guest}."
            )
            return guest_status
        raise FailException(f"Failed to get the guest status of {guest}.")

    def rhevm_guest_start(self, ssh_rhevm, guest):
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        guest_uuid = self.rhevm_guest_uuid(ssh_rhevm, guest)
        post_data = '"<action/>"'
        cmd = f"curl -X POST -d {post_data} {curl_header} {api_url}/vms/{guest_uuid}/start"
        for i in range(3):
            self.runcmd(cmd, ssh_rhevm)
            time.sleep(30)
            guest_status = self.rhevm_guest_status(ssh_rhevm, guest)
            if guest_status == "up" and self.rhevm_guest_ip(ssh_rhevm, guest):
                logger.info(f"Succeeded to start {guest}.")
                return True
            logger.warning(f"Failed to start {guest}, try again.")
        raise FailException(f"Failed to start {guest}.")

    def rhevm_guest_stop(self, ssh_rhevm, guest):
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        guest_uuid = self.rhevm_guest_uuid(ssh_rhevm, guest)
        post_data = '"<action><force>true</force></action>"'
        cmd = (
            f"curl -X POST -d {post_data} {curl_header} {api_url}/vms/{guest_uuid}/stop"
        )
        for i in range(3):
            self.runcmd(cmd, ssh_rhevm)
            time.sleep(30)
            guest_status = self.rhevm_guest_status(ssh_rhevm, guest)
            if guest_status == "down":
                logger.info(f"Succeeded to stop {guest}.")
                return True
            logger.warning(f"Failed to stop {guest}, try again.")
        raise FailException(f"Failed to stop {guest}.")

    def rhevm_guest_suspend(self, ssh_rhevm, guest):
        api_url, curl_header = self.rhevm_api_data(ssh_rhevm)
        guest_uuid = self.rhevm_guest_uuid(ssh_rhevm, guest)
        post_data = '"<action/>"'
        cmd = f"curl -X POST -d {post_data} {curl_header} {api_url}/vms/{guest_uuid}/suspend"
        for i in range(3):
            self.runcmd(cmd, ssh_rhevm)
            time.sleep(30)
            guest_status = self.rhevm_guest_status(ssh_rhevm, guest)
            if guest_status == "suspended":
                logger.info(f"Succeeded to suspend {guest}.")
                return True
            logger.warning(f"Failed to suspend {guest}, try again.")
        raise FailException(f"Failed to suspend {guest}.")
