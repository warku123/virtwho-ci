# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-195889')
        trigger_type = self.get_config('trigger_type')
        hypervisor_type = self.get_config('hypervisor_type')
        if trigger_type != 'trigger-rhel':
            self.vw_case_skip(trigger_type)
        if hypervisor_type != 'esx':
            self.vw_case_skip(hypervisor_type)

        results = dict()
        options = [
                '#[config name]',
                '#type=',
                '#server=',
                '#username=',
                '#password=',
                '#encrypted_password=',
                '#owner=',
                '#hypervisor_id=',
                '#rhsm_hostname=',
                '#rhsm_port=',
                '#rhsm_username=',
                '#rhsm_password=',
                '#rhsm_encrypted_password=',
                '#rhsm_prefix=/rhsm',
                '#kubeconfig=',
                '#kubeversion=',]    
        self.pkg_uninstall(self.ssh_host(), 'virt-who')
        self.pkg_install(self.ssh_host(), 'virt-who')
        _, output = self.runcmd('cat /etc/virt-who.d/template.conf', self.ssh_host())
        for option in options:
            if len(re.findall(option, output)) < 0:
                logger.warning('{0} is not defined in the template.conf'.format(option))
                results.setdefault(option, []).append(False)
            else:
                logger.info('{0} is defined'.format(option))
                results.setdefault(option, []).append(True)
        self.vw_case_result(results)
