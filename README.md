VIRTWHO-QE - Testing virt-who package for differernt hypervisors and register servers.  

Before running our test cases, you have to config the environment variables for hypervisors and register server.   
There are two ways to configure the env, take esx environment as an example:  
1. Export Environment  
```
export RHEL_COMPOSE=RHEL-7.7-20190403.0
export TRIGGER_TYPE=trigger-rhel
export TRIGGER_LEVEL=tier1
export VIRTWHO_HOST_IP=
export VIRTWHO_HOST_USER=
export VIRTWHO_HOST_PASSWD=
export HYPERVISOR_TYPE=esx
export HYPERVISOR_SERVER=
export HYPERVISOR_USERNAME=
export HYPERVISOR_PASSWORD=
export HYPERVISOR_SSH_USER=
export HYPERVISOR_SSH_PASSWD=
export GUEST_IP=
export GUEST_NAME=
export GUEST_USER=
export GUEST_PASSWD=
export REGISTER_TYPE=satellite65
export REGISTER_SERVER=
export REGISTER_OWNER=
export REGISTER_ENV=
export REGISTER_ADMIN_USER=
export REGISTER_ADMIN_PASSWD=
export REGISTER_SSH_USER=
export REGISTER_SSH_PASSWD=
```

2. Configure Environment in config.in  
```
# cd virtwho-qe
# vi config.in
[virtwho]
trigger_type=trigger-rhel
rhel_compose=RHEL-7.7-20190403.0
host_ip=
host_user=
host_passwd=

[hypervisor]
type=esx
server=
server_username=
server_password=
server_ssh_user=
server_ssh_passwd=
guest_ip=
guest_name=
guest_user=
guest_passwd=

[register]
type=satellite65
server=
owner=
env=
admin_user=
admin_passwd=
ssh_user=
ssh_passwd=
```

After configured the env, you can run the case as:  
```
# nosetests tests/virtwho/tier1/tc_1001_check_virtwho_is_shipped_by_different_arch.py
```
