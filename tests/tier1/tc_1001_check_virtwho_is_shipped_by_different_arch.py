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
        rhel_url = deploy.repo.rhel
        rhel_release = compose_id.split('.')[0]
        if "updates" in compose_id:
            baseurl = "{0}/{1}/rel-eng/updates/{2}".format(
                rhel_url, rhel_release.lower(), rhel_release)
        elif ".n" in compose_id:
            rhel_nightly_url = deploy.repo.rhel_nightly
            baseurl = "{0}/{1}/nightly/{2}".format(
                rhel_nightly_url, rhel_release.lower(), rhel_release)
        else:
            baseurl = "{0}/{1}/rel-eng/{2}".format(
                rhel_url, rhel_release.lower(), rhel_release)
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
                pkg_url = "{0}/{1}/compose/AppStream/{2}/os/Packages/{3}".format(
                    baseurl, compose_id, arch, pkg)
            else:
                pkg_url = "{0}/{1}/compose/{2}/os/Packages/{3}".format(
                    baseurl, compose_id, arch, pkg)
            if self.url_validation(pkg_url):
                results.setdefault('step1', []).append(True)
                logger.info("{0} is exist in arch: {1}".format(pkg, arch))
            else:
                results.setdefault('step1', []).append(False)
                logger.info("{0} is not exist in arch: {1}".format(pkg, arch))

        # case results
        self.vw_case_result(results)
