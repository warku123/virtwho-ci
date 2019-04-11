# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-133652')
        trigger_type = self.get_config('trigger_type')
        compose_id = self.get_config('rhel_compose')
        if "trigger-rhel" not in trigger_type:
            self.vw_case_skip(trigger_type)

        # case config
        results = dict()
        arch_list = list()
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')
        if pkg is False:
            raise FailException("virt-who pkg is not found")
        if compose_id is None or compose_id == "":
            raise FailException("compose_id is not defined")
        if "updates" in compose_id:
            rhel_release = compose_id.split('-')[0] + '-' + compose_id.split('-')[1]
            baseurl = "http://download.eng.pek2.redhat.com/rel-eng/updates/{0}".format(rhel_release)
        else:
            baseurl = "http://download.eng.bos.redhat.com/rhel-7/rel-eng/RHEL-7"
        if "RHEL-8" in compose_id:
            arch_list = ['x86_64', 'ppc64le', 'aarch64', 's390x']
        if "RHEL-7" in compose_id:
            arch_list = [
                    'Client/x86_64',
                    'Server/x86_64',
                    'Server/ppc64',
                    'Server/ppc64le', 
                    'Server/s390x', 
                    'Workstation/x86_64']
        if "RHEL-6" in compose_id:
            arch_list = [
                    'Client/x86_64',
                    'Client/i386', 
                    'ComputeNode/x86_64', 
                    'Server/i386', 
                    'Server/x86_64', 
                    'Server/ppc64', 
                    'Server/s390x', 
                    'Workstation/i386', 
                    'Workstation/x86_64',]
        # case steps
        for arch in arch_list:
            if "RHEL-8" in compose_id:
                baseurl = "http://download.eng.bos.redhat.com/rhel-8/rel-eng/RHEL-8"
                pkg_url = "{0}/{1}/compose/AppStream/{2}/os/Packages/{3}".format(baseurl, compose_id, arch, pkg)
            else:
                pkg_url = "{0}/{1}/compose/{2}/os/Packages/{3}".format(baseurl, compose_id, arch, pkg)
            if self.url_validation(pkg_url):
                results.setdefault('step1', []).append(True)
                logger.info("{0} is exist in arch: {1}".format(pkg, arch))
            else:
                results.setdefault('step1', []).append(False)
                logger.info("{0} is not exist in arch: {1}".format(pkg, arch))

        # case results
        self.vw_case_result(results)
