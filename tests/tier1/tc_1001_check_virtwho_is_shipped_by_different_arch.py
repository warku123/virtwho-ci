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
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')
        if pkg is False:
            raise FailException("virt-who pkg is not found")
        if compose_id is None or compose_id == "":
            raise FailException("compose_id is not defined")
        repo_base, repo_extra = self.rhel_compose_url(compose_id)

        baseurl = repo_extra.split("/x86_64/")[0]
        arch_list = [
                'x86_64',
                'ppc64le',
                'aarch64',
                's390x']
        if "RHEL-7" in compose_id:
            baseurl = repo_base.split("/Server/x86_64/")[0]
            arch_list = [
                    'Client/x86_64',
                    'Server/x86_64',
                    'Server/ppc64',
                    'Server/ppc64le', 
                    'Server/s390x', 
                    'Workstation/x86_64']

        # case steps
        for arch in arch_list:
            pkg_url = f"{baseurl}/{arch}/os/Packages/{pkg}"
            if self.url_validation(pkg_url):
                results.setdefault('step1', []).append(True)
                logger.info("{0} is exist in arch: {1}".format(pkg, arch))
            else:
                results.setdefault('step1', []).append(False)
                logger.info("{0} is not exist in arch: {1}".format(pkg, arch))

        # case results
        self.vw_case_result(results)
