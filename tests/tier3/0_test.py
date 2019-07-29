type = 'https_proxy'
hypervisor_type = 'libvirt'
if (type == 'http_proxy' and 'hyperv' not in hypervisor_type) \
        or (type == 'https_proxy' and hypervisor_type in ('kubevirt', 'libvirt', 'hyperv')):
# if type == 'http_proxy':
    print('true')
else:
    print('false')