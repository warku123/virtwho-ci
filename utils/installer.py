#!/usr/bin/python

import os
import sys
import argparse
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from virt_who import *
from virt_who.provision import Provision

def update_section(section, option=None, value=None):
    if not os.path.exists(json_file):
        with open(json_file, 'w') as fd:
            fd.write('{}')
    with open(json_file) as fd:
        data = json.load(fd)
    if section in data:
        data[section][option] = value
    else:
        data[section]={option:value}
    with open(json_file, 'w') as fd:
        json.dump(data, fd, indent=4, sort_keys=True)

def install_rhel_by_beaker(args):
    ssh_username = deploy.beaker.default_user
    ssh_password = deploy.beaker.default_passwd
    job_name = 'virtwho-ci-{}'.format(args.rhel_compose)
    job_id = provision.beaker_Jsubmit(
        args.os_type,
        args.variant,
        args.arch,
        args.rhel_compose,
        job_name,
    )
    while(provision.beaker_Jstatus({job_name:job_id})):
        time.sleep(60)
    results = provision.beaker_Jresult({job_name:job_id})
    if results[job_name]:
        update_section('host', 'hostname', results[job_name])
        update_section('host', 'ssh_username', ssh_username)
        update_section('host', 'ssh_password', ssh_password)

def install_rhel_by_grub(args):
    host = args.host
    username = args.username
    password = args.password
    ssh_host = {'host':host, 'username':username, 'password':password}
    provision.rhel_install_by_grub(ssh_host, args.rhel_compose)
    update_section('host', 'hostname', host)
    update_section('host', 'ssh_username', username)
    update_section('host', 'ssh_password', password)

def install_satellite(args):
    host = args.host
    username = args.username
    password = args.password
    sat_type = "satellite{}-{}-{}".format(
        args.sat_release,
        args.sat_repo,
        args.sat_os,
        ).lower()
    admin_username = deploy.satellite.admin_user
    admin_password = deploy.satellite.admin_passwd
    manifest_url = deploy.satellite.manifest
    ssh_sat = {'host':host, 'username':username, 'password':password}
    provision.system_init("satellite-host-virtwho", ssh_sat)
    sat_ver, rhel_ver = provision.satellite_version(sat_type)
    if "dogfood" in sat_type:
        provision.satellite_qa_dogfood_enable(
            ssh_sat, sat_ver, rhel_ver, repo_type="satellite")
    if "cdn" in sat_type:
        provision.employee_sku_attach(ssh_sat)
        provision.rhel_repo_enable(ssh_sat)
        provision.satellite_cdn_pool_attach(ssh_sat)
        provision.satellite_cdn_repo_enable(ssh_sat, sat_ver, rhel_ver)
    provision.satellite_pkg_install(ssh_sat)
    provision.satellite_deploy(
        ssh_sat, admin_username, admin_password, manifest_url, sat_ver)
    cmd = "rm -f {1}; curl -L {0} -o {1}; sync".format(
        deploy.kubevirt.kube_config_url,
        deploy.kubevirt.kube_config_file)
    provision.runcmd(cmd, ssh_sat)
    update_section('satellite', 'hostname', host)
    update_section('satellite', 'ssh_username', username)
    update_section('satellite', 'ssh_password', password)
    update_section('satellite', 'admin_username', admin_username)
    update_section('satellite', 'admin_password', admin_username)

def setup_esx():
    vcenter_ip = deploy.vcenter.ip
    vcenter_admin_user = deploy.vcenter.admin_user
    vcenter_admin_passwd = deploy.vcenter.admin_passwd
    guest_name = deploy.vcenter.guest_name
    guest_username = deploy.vcenter.guest_user
    guest_password = deploy.vcenter.guest_passwd
    image_path = deploy.vcenter.image_path
    ssh_vcenter = {
        'host':vcenter_ip,
        'username': deploy.vcenter.ssh_user,
        'password': deploy.vcenter.ssh_passwd}
    ssh_master = {
        'host': deploy.vcenter.master,
        'username': deploy.vcenter.master_user,
        'password': deploy.vcenter.master_passwd}
    cert = provision.vcenter_cert(
        vcenter_ip, vcenter_admin_user, vcenter_admin_passwd)
    guest_ip = provision.vcenter_guest_ip(cert, ssh_vcenter, guest_name)
    if not guest_ip:
        provision.vcenter_host_ready(cert, ssh_vcenter, ssh_master)
        guest_ip = provision.vcenter_guest_add(
            cert, ssh_vcenter, ssh_master, guest_name, image_path)
    ssh_guest = {
        'host': guest_ip, 
        'username': guest_username, 
        'password': guest_password}
    provision.system_init("ci-guest-esx", ssh_guest)
    update_hypervisor_section(
        'esx', vcenter_ip, vcenter_admin_user, vcenter_admin_passwd,
        guest_ip, guest_username, guest_password)

def setup_xen():
    master = deploy.xen.master
    master_username = deploy.xen.master_user
    master_password = deploy.xen.master_passwd
    guest_name = deploy.xen.guest_name
    guest_username = deploy.xen.guest_user
    guest_password = deploy.xen.guest_passwd
    sr_name = deploy.xen.sr_name
    sr_server = deploy.xen.sr_server
    sr_path = deploy.xen.sr_path
    image_path = deploy.xen.image_path
    ssh_master ={
        'host': master,
        'username': master_username,
        'password': master_password}
    guest_ip = provision.xen_guest_ip(ssh_master, guest_name)
    if not guest_ip:
        provision.xen_host_ready(ssh_master, sr_name, sr_server, sr_path)
        guest_ip = provision.xen_guest_add(
            ssh_master, guest_name, sr_name, image_path)
    ssh_guest = {
        'host': guest_ip,
        'username': guest_username,
        'password': guest_password}
    provision.system_init("ci-guest-xen", ssh_guest)
    update_hypervisor_section(
        'xen', master, master_username, master_password,
        guest_ip, guest_username, guest_password)

def setup_hyperv():
    master = deploy.hyperv.master
    master_username = deploy.hyperv.master_user
    master_password = deploy.hyperv.master_passwd
    guest_name = deploy.hyperv.guest_name
    guest_username = deploy.hyperv.guest_user
    guest_password = deploy.hyperv.guest_passwd
    image_path = deploy.hyperv.image_path
    ssh_hyperv ={
        'host': master,
        'username': master_username,
        'password': master_password}
    guest_ip = provision.hyperv_guest_ip(ssh_hyperv, guest_name)
    if not guest_ip:
        guest_ip = provision.hyperv_guest_add(
            ssh_hyperv, guest_name, image_path)
    ssh_guest = {
        'host': guest_ip,
        'username': guest_username,
        'password': guest_password}
    provision.system_init("ci-guest-hyperv", ssh_guest)
    update_hypervisor_section(
        'hyperv', master, master_username, master_password,
        guest_ip, guest_username, guest_password)
   
def setup_rhevm():
    rhevm_admin_username = deploy.rhevm.rhevm_admin_user
    rhevm_admin_password = deploy.rhevm.rhevm_admin_passwd
    guest_name = deploy.rhevm.guest_name
    guest_username = deploy.rhevm.guest_user
    guest_password = deploy.rhevm.guest_passwd
    cluster = deploy.rhevm.cluster
    cputype = deploy.rhevm.cputype
    template = deploy.rhevm.template
    disk = deploy.rhevm.disk
    datacenter = deploy.rhevm.datacenter
    storage = deploy.rhevm.storage
    ssh_rhevm = {
        'host': deploy.rhevm.rhevm_ip,
        'username': deploy.rhevm.rhevm_ssh_user,
        'password': deploy.rhevm.rhevm_ssh_passwd}
    ssh_master = {
        'host': deploy.rhevm.master,
        'username': deploy.rhevm.master_user,
        'password': deploy.rhevm.master_passwd}
    rhevm_version = provision.rhevm_version_get(ssh_rhevm)
    rhevm_url = provision.rhevm_admin_get(ssh_rhevm)
    rhevm_shell, rhevm_shellrc = provision.rhevm_shell_get(ssh_rhevm)
    provision.rhevm_shell_config(ssh_rhevm, rhevm_url,
        rhevm_admin_username, rhevm_admin_password)
    provision.rhevm_cpu_set(ssh_rhevm, rhevm_shell, cluster, cputype)
    guest_ip = provision.rhevm_guest_ip(
        ssh_rhevm, rhevm_shell, ssh_master, guest_name)
    if not guest_ip:
        provision.rhevm_template_ready(
            ssh_rhevm, rhevm_shell, template, disk)
        provision.rhevm_host_ready(
            ssh_rhevm, rhevm_shell, ssh_master, datacenter, storage)
        guest_ip = provision.rhevm_guest_add(
            ssh_rhevm, rhevm_shell, ssh_master, guest_name,
            template, cluster, disk)
    ssh_guest = {
        'host': guest_ip,
        'username': guest_username,
        'password': guest_password}
    provision.system_init("ci-guest-rhevm", ssh_guest)
    update_hypervisor_section(
        'rhevm', rhevm_url, rhevm_admin_username, rhevm_admin_password,
        guest_ip, guest_username, guest_password)

def setup_libvirt():
    host = deploy.libvirt.remote
    username = deploy.libvirt.remote_user
    password = deploy.libvirt.remote_passwd
    guest_name = deploy.libvirt.guest_name
    guest_username = deploy.libvirt.guest_user
    guest_password = deploy.libvirt.guest_passwd
    ssh_libvirt = {
        'host': host,
        'username': username,
        'password': password}
    provision.runcmd('service libvirtd restart', ssh_libvirt)
    guest_ip = provision.libvirt_guest_ip(guest_name, ssh_libvirt)
    if not guest_ip:
        provision.libvirt_guests_all_clean(ssh_libvirt)
        guest_ip = provision.libvirt_guest_add(guest_name, ssh_libvirt)
    ssh_guest = {
        'host':guest_ip,
        'username': guest_username,
        'password': guest_password}
    provision.system_init("ci-guest-libvirt-remote", ssh_guest)
    update_hypervisor_section(
        'libvirt', host, username, password,
        guest_ip, guest_username, guest_password)


def setup_kubevirt():
    master = deploy.kubevirt.master
    master_username = deploy.kubevirt.master_user
    master_password = deploy.kubevirt.master_passwd
    guest_name = deploy.kubevirt.guest_name
    guest_username = deploy.kubevirt.guest_user
    guest_password = deploy.kubevirt.guest_passwd
    ssh_master ={
        'host': master,
        'username': master_username,
        'password': master_password}
    guest = provision.kubevirt_guest_ip(ssh_master, guest_name)
    if guest:
        ssh_guest = {
            'host': guest,
            'username': guest_username,
            'password' :guest_password}
        provision.system_init("ci-guest-kubvirt", ssh_guest)
        if ':' in guest:
            guest_ip = guest.split(':')[0]
            guest_port = guest.split(':')[1]
        update_hypervisor_section(
            'kubevirt', master, master_username, master_password,
            guest_ip, guest_username, guest_password, guest_port,
            deploy.kubevirt.kube_config_file)

def update_hypervisor_section(
        mode, server, username, password,
        guest, guest_username, guest_password, guest_port=22,
        kubeconfig=None):
    update_section(mode, 'hypervisor_type', mode)
    update_section(mode, 'hypervisor_server', server)
    update_section(mode, 'hypervisor_username', username)
    update_section(mode, 'hypervisor_password', password) 
    if kubeconfig:
        update_section(mode, 'hypervisor_config_file', kubeconfig)
    update_section(mode, 'guest', guest)
    update_section(mode, 'guest_port', str(guest_port))
    update_section(mode, 'guest_username', guest_username)
    update_section(mode, 'guest_password', guest_password)

def parser_arguments():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    # Install RHEL OS by Beaker
    beaker_parser = subparsers.add_parser(
        'install-rhel-bkr',
        help='Install rhel os by beaker')
    beaker_parser.add_argument(
        '--os-type',
        required=True,
        help='One of [physical, virtual]')
    beaker_parser.add_argument(
        '--variant',
        required=True,
        help='One of [Server, Client, Workstation, BaseOS]')
    beaker_parser.add_argument(
        '--arch',
        required=True,
        help='One of [x86_64, s390x, ppc64, ppc64le, aarch64]')
    beaker_parser.add_argument(
        '--rhel-compose',
        required=True,
        help='Such as: RHEL-7.6-20181010.0, RHEL-8.0-20181005.1')
    # Install RHEL OS by updating grub
    grub_parser = subparsers.add_parser(
        'install-rhel-grub',
        help='Install rhel os by updating grub')
    grub_parser.add_argument(
        '--host',
        required=True,
        help="The IP or Hostname where host's grub will be updated")
    grub_parser.add_argument(
        '--username',
        required=True,
        help="The ssh username of this host")
    grub_parser.add_argument(
        '--password',
        required=True,
        help="The ssh password of this host")
    grub_parser.add_argument(
        '--rhel-compose',
        required=True,
        help='such as: RHEL-7.6-20181010.0, RHEL-8.0-20181005.1')
    # Install Satellite
    sat_parser = subparsers.add_parser(
        'install-satellite',
        help='install satellite')
    sat_parser.add_argument(
        '--host',
        required=True,
        help="The IP or Hostname where satellite will be deployed")
    sat_parser.add_argument(
        '--username',
        required=True,
        help="The ssh username of this host")
    sat_parser.add_argument(
        '--password',
        required=True,
        help="The ssh password of this host")
    sat_parser.add_argument(
        '--sat-release',
        required=True,
        help="One of ['6.5', '6.6']")
    sat_parser.add_argument(
        '--sat-repo',
        required=True,
        help="One of ['cdn', 'dogfood']")
    sat_parser.add_argument(
        '--sat-os',
        required=True,
        help='such as: RHEL-7.6-20181010.0, RHEL-8.0-20181005.1')
    # Hypervisor Provision
    hypervisor_parser = subparsers.add_parser(
        'install-hypervisor',
        help='setup hypervisor based on the provision.in')
    hypervisor_parser.add_argument(
        '--hypervisor-type',
        required=True,
        help="One of ['esx', 'xen', 'hyperv', 'rhevm', 'libvirt', 'kubevirt']")
    return parser.parse_args()

if __name__ == "__main__":
    json_file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'report.json')
    provision_ini = os.path.join(
        os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir)),
        'provision.ini')
    if not os.path.exists(provision_ini):
        logger.error('{} is not existing.'.format(provision_ini))
        sys.exit(1)
    args = parser_arguments()
    provision = Provision()
    if args.command == 'install-rhel-bkr':
        install_rhel_by_beaker(args)
    if args.command == 'install-rhel-grub':
        install_rhel_by_grub(args)
    if args.command == 'install-satellite':
        install_satellite(args)
    if args.command == 'install-hypervisor':
        if args.hypervisor_type == "esx":
            setup_esx()
        if args.hypervisor_type == "xen":
            setup_xen()
        if args.hypervisor_type == "hyperv":
            setup_hyperv()
        if args.hypervisor_type == "rhevm":
            setup_rhevm()
        if args.hypervisor_type == "libvirt":
            setup_libvirt()
        if args.hypervisor_type == "kubevirt":
            setup_kubevirt()
