# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        """
        :Verify: virt-who package is exist in different arch repo
        :Polarion_Id: RHEL-133652
        :Automated: Yes
        """
        logger.info(os.path.basename(__file__))
        trigger_type = config.virtwho.trigger_type
        compose_id = config.virtwho.rhel_compose
        if "trigger-rhel" not in trigger_type:
            self.vw_case_skip("skipped - this case is not avaialbe for {0}".format(trigger_type))

        # Case Config
        results = dict()
        arch_list = list()
        pkg = self.pkg_check(self.ssh_host(), 'virt-who')
        if pkg is False:
            raise FailException("Failed to run this case, due to virt-who pkg is not found")
        if compose_id is None or compose_id == "":
            raise FailException("Failed to run this case, due to compose_id is not defined")
        if "updates" in compose_id:
            rhel_release = compose_id.split('-')[0] + '-' + compose_id.split('-')[1]
            baseurl = "http://download.eng.pek2.redhat.com/rel-eng/updates/%s" % rhel_release
        else:
            baseurl = "http://download.eng.pek2.redhat.com/pub/rhel/rel-eng"
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
        # Case Steps
        for arch in arch_list:
            if "RHEL-8" in compose_id:
                baseurl = "http://download.eng.pek2.redhat.com/rhel-8/rel-eng/RHEL-8"
                pkg_url = "%s/%s/compose/AppStream/%s/os/Packages/%s" %(baseurl, compose_id, arch, pkg)
            else:
                pkg_url = "%s/%s/compose/%s/os/Packages/%s" %(baseurl, compose_id, arch, pkg)
            if self.url_validation(pkg_url):
                results.setdefault('step1', []).append(True)
                logger.info("virt-who pkg is exist in arch: %s" % arch)
            else:
                results.setdefault('step1', []).append(False)
                logger.error("virt-who pkg is not exist in arch: %s" % arch)

        # Case Results
        self.vw_case_result(results)
