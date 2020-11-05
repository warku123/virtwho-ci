from virt_who import *

class Base(unittest.TestCase):
    def paramiko_run(self, cmd, host, username, password, timeout=1800, port=22):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port, username, password, banner_timeout=300)
            ssh._transport.window_size = 2147483647
            chan = ssh.get_transport().open_session()
            chan.settimeout(timeout)
            try:
                chan.exec_command(cmd)
                contents = BytesIO()
                error = BytesIO()
                data = chan.recv(1024)
                while data:
                    contents.write(data)
                    data = chan.recv(1024)
                error_buff = chan.recv_stderr(1024)
                while error_buff:
                    error.write(error_buff)
                    error_buff = chan.recv_stderr(1024)
                exit_status = chan.recv_exit_status()
                output = contents.getvalue()+error.getvalue()
                if type(output) is bytes:
                    output = output.decode("utf-8")
                ssh.close()
                return exit_status, output
            except socket.timeout:
                msg = "timeout exceeded ...({0})".format(host)
                logger.info(msg)
                return -1, msg
        except Exception as e:
            return -1, str(e)
        finally:
            ssh.close()

    def paramiko_getfile(self, host, username, password, from_path, to_path, port=22):
        scp = paramiko.Transport((host, port))
        scp.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        sftp.get(from_path, to_path)
        scp.close()

    def paramiko_putfile(self, ssh, from_path, to_path, port=22):
        host = ssh['host']
        if ":" in host:
            var = host.split(':')
            host = var[0]
            port = int(var[1])
        username = ssh['username']
        password = ssh['password']
        scp = paramiko.Transport((host, port))
        scp.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        sftp.put(from_path, to_path)
        scp.close()

    def paramiko_putdir(self, ssh, local_dir, remote_dir, port=22):
        host = ssh['host']
        username = ssh['username']
        password = ssh['password']
        try:
            t=paramiko.Transport((host, port))
            t.connect(username=username, password=password)
            sftp=paramiko.SFTPClient.from_transport(t)
            for root,dirs,files in os.walk(local_dir):
                for filespath in files:
                    local_file = os.path.join(root,filespath)
                    a = local_file.replace(local_dir,'')
                    remote_file = os.path.join(remote_dir,a)
                    try:
                        sftp.put(local_file,remote_file)
                    except Exception as e:
                        sftp.mkdir(os.path.split(remote_file)[0])
                        sftp.put(local_file,remote_file)
                for name in dirs:
                    local_path = os.path.join(root,name)
                    a = local_path.replace(local_dir,'')
                    remote_path = os.path.join(remote_dir,a)
                    try:
                        sftp.mkdir(remote_path)
                    except Exception as e:
                        logger.info(e)
            t.close()
        except Exception as e:
            logger.info(e)

    def runcmd(self, cmd, ssh, timeout=None, desc=None, debug=True, port=22):
        host = ssh['host']
        if ":" in host:
            var = host.split(':')
            host = var[0]
            port = int(var[1])
        username = ssh['username']
        password = ssh['password']
        retcode, stdout = self.paramiko_run(cmd, host, username, password, timeout, port)
        fd = open(DEBUG_FILE, 'a')
        fd.write(">>> Running in: {0}:{1}, Desc: {2}\n".format(host, port, desc))
        fd.write("Command: {0}\n".format(str(cmd)))
        fd.write("Retcode: {0}\n".format(retcode))
        if debug or retcode != 0:
            try:
                fd.write("Output:\n{0}\n".format(str(stdout)))
            except:
                fd.write("Output:\n{0}\n".format(str(stdout.encode("utf-8"))))
                pass
        fd.close()
        return retcode, stdout.strip()

    def run_loop(self, cmd, ssh, desc=None, loop_num=10, wait_time=30, wait_msg=None):
        status = ""
        for i in range(loop_num):
            ret, output = self.runcmd(cmd, ssh, desc=desc)
            if ret == 0:
                status = "Yes"
                break
            if wait_msg is not None:
                logger.info(wait_msg)
            time.sleep(wait_time)
        return status, output

    def run_service(self, ssh, name, action):
        cmd = "service {0} {1}".format(name, action)
        ret, output = self.runcmd(cmd, ssh, desc="run service")
        time.sleep(10)
        return ret, output

    def run_expect(self, ssh, cmd, attrs):
        options = list()
        filename = "/tmp/exp.sh"
        for attr in attrs:
            expect = r'expect "%s"' % attr.split('|')[0]
            send = r'send "%s\r"' % attr.split('|')[1]
            options.append(expect+'\n'+send)
        cmd = ('cat <<EOF > %s\n'
                '#!/usr/bin/expect\n'
                'spawn %s\n'
                '%s\n'
                'expect eof\n'
                'exit\n'
                'EOF'
              ) % (filename, cmd, '\n'.join(options))
        ret, output = self.runcmd(cmd, ssh, desc="create expect script")
        cmd = "chmod +x {0}; {1}".format(filename, filename)
        ret, output = self.runcmd(cmd, ssh, desc="run expect script")
        self.runcmd("rm -f {0}".format(filename), ssh, desc="rm expect script")
        return ret, output

    def get_exported_param(self, name):
        value = os.getenv(name)
        if value is None or value == '':
            value = None
        return value

    def set_exported_param(self, name, value):
        os.putenv(name, value)
        return os.getenv(name)

    def shell_escape_char(self, char):
        char = char.replace('[', '\[').replace(']', '\]').replace('/', '\/')
        return char

    def randomMAC(self):
        mac = [ 0x06,
                random.randint(0x00, 0x2f),
                random.randint(0x00, 0x3f),
                random.randint(0x00, 0x4f),
                random.randint(0x00, 0x8f),
                random.randint(0x00, 0xff) ]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def get_url_domain(self, url):
        reobj = re.compile(r"""(?xi)\A
        [a-z][a-z0-9+\-.]*://               # Scheme
        ([a-z0-9\-._~%!$&'()*+,;=]+@)?      # User
        ([a-z0-9\-._~%]+                    # Named or IPv4 host
        |\[[a-z0-9\-._~%!$&'()*+,;=:]+\])   # IPv6+ host
        """)
        match = reobj.search(url)
        if match:
            return match.group(2)

    def is_json(self, data):
        try:
            json_object = json.loads(data)
        except ValueError as e:
            logger.warning("No JSON object could be decoded")
            return False
        return json_object

    def url_validation(self, url):
        cmd = "if ( curl -o/dev/null -sfI '{0}' ); then echo 'true'; else echo 'false'; fi".format(url)
        output = os.popen(cmd).read()
        if output.strip() == "true":
            return True
        else:
            return False

    def fd_delete(self, ssh, file_path):
        rex = ["", " ", "/", "/root", "/root/"]
        if any(key == file_path for key in rex):
            logger.warning("Unsupport to delete %s" % rex)
        else:
            cmd = "rm -rf %s" % file_path
            ret, output = self.runcmd(cmd, ssh, desc="delete files/dir")
            if ret == 0:
                logger.info("Succeeded to delete {0}".format(file_path))
            else:
                logger.warning("Failed to delete {0}".format(file_path))

    def ssh_no_passwd_access(self, ssh_local, ssh_remote=None):
        if ssh_remote is None:
            ssh_remote = {
                    "host":deploy.libvirt.remote,
                    "username":deploy.libvirt.remote_user,
                    "password":deploy.libvirt.remote_passwd}
        cmd = 'echo -e "\n" | ssh-keygen -N "" &> /dev/null'
        ret, output = self.runcmd(cmd, ssh_local, desc="create ssh key")
        cmd = "cat ~/.ssh/id_rsa.pub"
        ret, output = self.runcmd(cmd, ssh_local, desc="check id_rsa.pub exist")
        if ret != 0 or output is None:
            raise FailException("Failed to create ssh key")
        cmd = "mkdir ~/.ssh/; echo '{0}' >> ~/.ssh/authorized_keys".format(output)
        ret, output = self.runcmd(cmd, ssh_remote, desc="copy id_rsa.pub to remote")
        host = ssh_remote['host']
        port = 22
        if ":" in host:
            var = host.split(':')
            host = var[0]
            port = int(var[1])
        cmd = "ssh-keyscan -p {0} {1} >> ~/.ssh/known_hosts".format(port, host) 
        ret, output = self.runcmd(cmd, ssh_local, desc="create ~/.ssh/known_hosts")
        logger.info("Succeeded to copy sshkey from {0} to {1}".format(ssh_local['host'], ssh_remote['host']))

    def kill_pid_by_name(self, ssh, process_name):
        cmd = "ps -ef | grep %s -i | grep -v grep | awk '{print $2}' | xargs -I {} kill -9 {}" % process_name
        ret, output = self.runcmd(cmd, ssh, desc="kill pid by pid_name")
        cmd = "rm -f /var/run/%s.pid" % process_name
        ret, output = self.runcmd(cmd, ssh, desc="remove pid file")
        cmd = "ps -ef | grep %s -i | grep -v grep |sort" % process_name
        ret, output = self.runcmd(cmd, ssh, desc="check pid exist")
        if output.strip() == "" or output.strip() is None:
            return True
        else:
            return False

    def system_reboot(self, ssh):
        host = ssh['host']
        is_container = "no"
        if ":" in host:
            var = host.split(':')
            host = var[0]
            port = int(var[1])
            if port != 22:
                is_container = "yes"
        if is_container == "no":
            cmd = "sync;sync;sync;sync;reboot -f && exit"
            ret, output = self.runcmd(cmd, ssh, desc="reboot os", timeout=3)
            time.sleep(60)
        else:
            container_name = self.get_hostname(ssh)
            ssh_docker ={
                "host" : deploy.docker.server,
                "username" : deploy.docker.server_user,
                "password" : deploy.docker.server_passwd,
            }
            logger.info("system({0}) is a container, will restart it by docker".format(host))
            cmd = "docker restart %s" % container_name
            ret, output = self.runcmd(cmd, ssh_docker, desc="restart container")
            cmd = "docker exec -i %s /usr/sbin/sshd" % container_name
            ret, output = self.runcmd(cmd, ssh_docker, desc="start container ssh")
            time.sleep(180)
        if self.ssh_is_connected(ssh):
            logger.info('Succeeded to reboot system({0})'.format(host))
        else:
            raise FailException('Failed to reboot system({0})'.format(host))

    def ssh_is_connected(self, ssh):
        host = ssh['host']
        cmd ="rpm -qa filesystem"
        for i in range(60):
            ret, output = self.runcmd(cmd, ssh)
            if ret == 0 and "filesystem" in output:
                logger.info("Succeeded to connect host {0} by ssh".format(host))
                return True
            logger.info("Trying to connect host %s after 60s..." % host)
            time.sleep(60)
        return False

    def ping_is_connected(self, ipaddr):
        cmd = "ping -c 5 %s |grep -q 'ttl=' && echo 'ok' || echo 'failed'" % ipaddr
        output = os.popen(cmd).read().strip()
        if output == "ok":
            return True
        else:
            return False

    def rhel_version(self, ssh):
        cmd = "cat /etc/redhat-release"
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0 and output is not None:
            m = re.search(r'(?<=release )\d', output)
            rhel_ver = m.group(0)
            return str(rhel_ver)
        else:
            raise FailException("Unknown rhel release: %s (%s)" % (output.strip(), ssh['host']))

    def stop_firewall(self, ssh):
        rhel_ver = self.rhel_version(ssh)
        if rhel_ver == "6":
            cmd = "service iptables stop; chkconfig iptables off"
            self.runcmd(cmd, ssh)
        else:
            cmd = "systemctl stop firewalld.service; systemctl disable firewalld.service"
            self.runcmd(cmd, ssh)
        cmd = "setenforce 0; sed -i -e 's/SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config"
        self.runcmd(cmd, ssh, desc="disable selinux")

    def bridge_setup(self, bridge_name, ssh):
        host = ssh['host']
        cmd = "ip route get 8.8.8.8 | awk 'NR==2 {print $1}' RS='dev'"
        ret, output = self.runcmd(cmd, ssh, desc="get network device")
        if ret == 0:
            network_dev = output.strip()
            if bridge_name not in output:
                cmd_1 = "sed -i '/^BOOTPROTO/d' /etc/sysconfig/network-scripts/ifcfg-%s;" % network_dev
                cmd_2 = "echo 'BRIDGE=%s' >> /etc/sysconfig/network-scripts/ifcfg-%s;" % (bridge_name, network_dev)
                cmd_3 = "echo 'DEVICE=%s\nBOOTPROTO=dhcp\nONBOOT=yes\nTYPE=Bridge' > /etc/sysconfig/network-scripts/ifcfg-%s" % (bridge_name, bridge_name)
                cmd = "%s %s %s" % (cmd_1, cmd_2, cmd_3)
                ret, output = self.runcmd(cmd, ssh, desc="setup bridge")
                if ret == 0:
                    logger.info("Succeeded to create bridge:%s (%s)" % (bridge_name, host))
                else:
                    raise FailException("Failed to create bridge(%s)" % host)
                cmd = "service NetworkManager stop; service network restart"
                ret, output = self.runcmd(cmd, ssh, desc="restart network")
            else:
                logger.info("Bridge(%s) is ready(%s)" %(bridge_name, host))
        else:
            raise FailException("Failed to create bridge(%s)" % host)

    def get_hostname(self, ssh):
        ret, output = self.runcmd('hostname', ssh)
        if ret == 0 and output is not None and output != "":
            hostname = output.strip()
            return hostname
        else:
            raise FailException("Failed to get hostname(%s)" % ssh['host'])

    def get_ipaddr(self, ssh):
        #cmd = "ip route get 8.8.8.8 | awk 'NR==1 {print $NF}'"
        cmd = "ip route get 8.8.8.8 | awk '/src/ { print $7 }'"
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0 and output is not None:
                return output.strip()
        else:
            raise FailException("Failed to get ip address(%s)" % ssh['host'])

    def get_gateway(self, ssh):
        ipaddr = self.get_ipaddr(ssh)
        cmd = "ip route | grep %s" % ipaddr
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0 and output is not None and output != "":
            output = output.strip().split(" ")
            if len(output) > 0:
                gateway = output[0]
                return gateway
        raise FailException("Failed to get gateway(%s)" % ssh['host'])

    def set_etc_hosts(self, etc_hosts_value, ssh):
        cmd = "sed -i '/localhost/!d' /etc/hosts; echo '%s' >> /etc/hosts" % (etc_hosts_value)
        ret, output = self.runcmd(cmd, ssh)
        if ret != 0:
            raise FailException("Failed to set /etc/hosts (%s)" % ssh['host'])

    def set_hostname(self, hostname, ssh):
        try:
            cmd = "hostnamectl set-hostname {0}".format(hostname)
            self.runcmd(cmd, ssh)
            rhel_ver = self.rhel_version(ssh)
            if rhel_ver == "6":
                cmd = "sed -i '/HOSTNAME=/d' /etc/sysconfig/network; echo 'HOSTNAME={0}' >> /etc/sysconfig/network".format(hostname)
                self.runcmd(cmd, ssh)
            else:
                cmd = "if [ -f /etc/hostname ]; then sed -i -e '/localhost/d' -e '/{0}/d' /etc/hostname; echo {0} >> /etc/hostname; fi".format(hostname)
                self.runcmd(cmd, ssh)
        except:
            raise FailException("Failed to set hostname ({0})".format(ssh['host']))

    def system_init(self, key, ssh):
        if self.ssh_is_connected(ssh):
            self.rhsm_backup(ssh)
            host_ip = self.get_ipaddr(ssh)
            host_name = self.get_hostname(ssh)
            if "localhost" in host_name or "unused" in host_name or "openshift" in host_name or host_name is None:
                random_str = ''.join(random.sample(string.ascii_letters + string.digits, 8))
                host_name = "%s-%s.redhat.com" % (key, random_str)
            etc_hosts_value = "%s %s" % (host_ip, host_name)
            self.set_hostname(host_name, ssh)
            self.set_etc_hosts(etc_hosts_value, ssh)
            self.stop_firewall(ssh)
            logger.info("Finished to init system {0}".format(host_name))
        else:
            raise FailException("Failed to ssh login {0}".format(ssh['host']))

    def pkg_check(self, ssh, package):
        cmd = "rpm -qa {0}".format(package)
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0 and output is not None and output != "":
            pkg = output.strip()+".rpm"
            return pkg
        else:
            return False

    def pkg_install(self, ssh, package):
        cmd = "yum install -y {0}".format(package)
        ret, output = self.runcmd(cmd, ssh)
        if self.pkg_check(ssh, package) is False:
            logger.warning("Failed to install {0}".format(package))
            return False
        else:
            logger.info("Succeeded to install {0}".format(package))
            return True

    def pkg_uninstall(self, ssh, package):
        cmd = "rpm -e {0} --nodeps".format(package)
        ret, output = self.runcmd(cmd, ssh)
        if self.pkg_check(ssh, package) is False:
            logger.info("Succeeded to uninstall {0}".format(package))
            return True
        else:
            logger.warning("Failed to uninstall {0}".format(package))
            return False

    def pkg_info(self, ssh, package):
        cmd = "rpm -qi {0}".format(package)
        ret,output = self.runcmd(cmd, ssh)
        dic = output.split("\n")
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

    def nmap_pkg_ready(self, ssh):
        if self.pkg_check(ssh, "nmap") is False:
            self.nmap_pkg_install(ssh)
        else:
            logger.info("nmap is ready on {0} to scan ip".format(ssh['host']))

    def nmap_pkg_install(self, ssh):
        rhel_ver = self.rhel_version(ssh)
        mirror = "http://mirror.centos.org/centos/{0}/os/x86_64/Packages".format(rhel_ver)
        ftp = deploy.repo.rhel8_ftp
        ret, output = self.runcmd("yum install nmap nmap-ncat", ssh)
        if self.pkg_check(ssh, "nmap") is False:
            if rhel_ver == "8":
                nmap = "{0}/nmap-7.70-4.el8.x86_64.rpm".format(ftp)
                ncat = "{0}/nmap-ncat-7.70-4.el8.x86_64.rpm".format(ftp)
            if rhel_ver == "7":
                nmap = "{0}/nmap-6.40-19.el7.x86_64.rpm".format(mirror)
                ncat = "{0}/nmap-ncat-6.40-19.el7.x86_64.rpm".format(mirror)
            if rhel_ver == "6":
                nmap = "{0}/nmap-5.51-6.el6.x86_64.rpm".format(mirror)
                ncat = ""
            if nmap != "" and self.url_validation(nmap):
                ret, output = self.runcmd("cd /tmp/; curl -O -L {0}".format(nmap), ssh)
            if ncat != "" and self.url_validation(ncat):
                ret, output = self.runcmd("cd /tmp/; curl -O -L {0}".format(ncat), ssh)
            ret, output = self.runcmd("rpm -Uvh /tmp/nmap* --force", ssh)
            ret, output = self.runcmd("rm -f /tmp/nmap*", ssh)
        if self.pkg_check(ssh, "nmap") is False:
            raise FailException("Failed to install nmap package")
        else:
            logger.info("nmap package is installed")

    def get_ipaddr_bymac(self, mac_addr, ssh):
        self.nmap_pkg_ready(ssh)
        gateway = self.get_gateway(ssh)
        cmd = "nmap -sP -n %s | grep -i -B 2 %s |grep 'Nmap scan report for' | grep -Eo '([0-9]{1,3}[\.]){3}[0-9]{1,3}'| tail -1" % (gateway, mac_addr)
        for i in range(40):
            time.sleep(60)
            ret, output = self.runcmd(cmd, ssh, desc="check ip addr by mac")
            if ret == 0 and output is not None and output != "":
                ipaddr = output.strip()
                if self.ping_is_connected(ipaddr):
                    return ipaddr
            logger.info("Try to scan ip by nmap in %s after 30s ..." % ssh['host'])
        logger.error("Failed to get ip addr by mac(%s)" % ssh['host'])
        return False
