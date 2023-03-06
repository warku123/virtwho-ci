# coding:utf-8
import os, sys, getopt, fcntl
from polarion_caseid_mapping import *
sys.path.append('../')
from virt_who import *
from datetime import datetime
from xml.dom import minidom
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def parser_args(options):
    if len(options) == 0:
        logger.info('Usage: polarion_impoerter.py 1.xml 2.xml')
        sys.exit()
    files = []
    for arg in options:
        try:
            '''check arg is a xml file or not'''
            ET.parse(arg)
            files.append(arg)
        except Exception as e:
            logger.warning('%s is not a xml file' % arg)
    if len(files) > 0:
        return files
    raise FailException("no valid xml files provided")


def get_exported_param(param_name):
    param_value = os.getenv(param_name)
    if param_value is None or param_value == "":
        param_value = ""
    return param_value


def write_file(filename, content):
    try:
        fd = open(filename, 'wb')
        fcntl.flock(fd, fcntl.LOCK_EX)
        fd.write(content.encode("UTF-8"))
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()
    except IOError:
        logger.error('IOError to write file')
        pass


def read_file(filename):
    try:
        content = open(filename,'r').read()
        return content
    except IOError:
        logger.error('IOError to read file')
        pass


def update_file(filename, location, data):
    content = read_file(filename)
    pos = content.find(location)
    if pos != -1:
        content = content[:pos] + data + content[pos:]
        write_file(filename, content)


def fomatTree(elem):
    root_str = ET.tostring(elem, 'UTF-8')
    reparse = minidom.parseString(root_str)
    return reparse.toprettyxml(
        ).replace("\t\t\n", "").replace("\t\n", "").replace("\n\n", "\n")


def xml_init(xmlFile, root_node):
    if os.path.exists(xmlFile):
        os.remove(xmlFile)
    node = ET.Element(root_node)
    tree = ET.ElementTree(node)
    write_file(xmlFile, fomatTree(node))
    return fomatTree(node)


def xml_read(xmlFile):
    try:
        tree=ET.parse(xmlFile)
        return tree
    except:
        logger.error("failed to read xml file")


def xml_createNode(parent_node, child_node, attr, text):
    element = ET.Element(child_node)
    if attr:
        for key, value in attr.items():
            element.attrib[key]=value
    if text:
        element.text=text
    parent_node.append(element)
    return element


# def polarion_testrun_id():
#     job_name = get_exported_param("JOB_NAME")
#     trigger_name = get_exported_param("TRIGGER_TYPE")
#     server_type = get_exported_param("HYPERVISOR_TYPE")
#     create_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     if job_name != "" and trigger_name !="" and server_type !="":
#         testrun_id = "virtwho_%s_%s_%s" % (job_name, trigger_name, create_time)
#     else:
#         testrun_id = "virtwho_testrun_by_ci_%s" % create_time
#     testrun_url = '{0}/testrun?id={1}'.format(deploy.polarion.testrun_url, testrun_id)
#     logger.info(testrun_url)
#     fd = open(runtest_info, 'a')
#     fd.write("TESTRUN_URL=%s\n" % testrun_url)
#     fd.close()
#     return testrun_id


def polarion_testrun_id():
    create_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    testrun_id = "RHSS_%s" % create_time
    testrun_url = '{0}/testrun?id={1}'.format(deploy.polarion.testrun_url, testrun_id)
    logger.info(testrun_url)
    fd = open(runtest_info, 'a')
    fd.write("TESTRUN_URL=%s\n" % testrun_url)
    fd.close()
    return testrun_id


def polarion_testrun_title():
    rhel_compose = get_exported_param("RHEL_COMPOSE")
    trigger_level = get_exported_param("TRIGGER_LEVEL")
    hypervisor_type = get_exported_param("HYPERVISOR_TYPE")
    register_type = get_exported_param("REGISTER_TYPE")
    if "satellite" in register_type:
        register_type = "satellite"
    if "full" in trigger_level:
        trigger_level = "Tier1/Tier2"
    hypervisor_type = hypervisor_type.upper()
    register_type = register_type.title()
    if 'sca' in trigger_level:
        trigger_level = trigger_level.upper()
    else:
        trigger_level = trigger_level.title()
    testrun_title = f"VIRT-WHO {hypervisor_type}+{register_type} {trigger_level} {rhel_compose}"
    return testrun_title


def polarion_planned_in():
    # keyword = get_exported_param("PLANNED_IN")
    # rhel_compose = get_exported_param("RHEL_COMPOSE")
    # plan = ''
    # plans_dict = {
    #     'RHEL-9.1': {
    #         'MAIN': 'RHEL_9_1',
    #         'CTC1': '9_1_CTC_1',
    #         'CTC2': '9_1_CTC_2',
    #         'Beta': '9_1_Beta',
    #         'RC': '9_1_RC'
    #     },
    #     'RHEL-9.2': {
    #         'MAIN': '9_2_0',
    #         'CTC1': '9_2_0_CTC_1',
    #         'CTC2': '9_2_0_CTC_2',
    #         'Beta': '9_2_0_Beta',
    #         'RC': '9_2_0_RC'
    #     },
    #     'RHEL-8.7': {
    #         'MAIN': 'RHEL_8_7',
    #         'CTC1': '8_7_CTC_1',
    #         'CTC2': '8_7_CTC_2',
    #         'Beta': '8_7_Beta',
    #         'RC': '8_7_RC'
    #     },
    #     'RHEL-8.8': {
    #         'MAIN': '8_8_0',
    #         'CTC1': '8_8_0_CTC_1',
    #         'CTC2': '8_8_0_CTC_2',
    #         'Beta': '8_8_0_Beta',
    #         'RC': '8_8_0_RC'
    #     }
    # }
    # if 'Legacy' in keyword:
    #     plan = 'RHEL_Legacy_Release'
    # else:
    #     for (rhel, plans) in plans_dict.items():
    #         if rhel in rhel_compose:
    #             plan = plans[keyword]

    # Get planned in id from http://10.73.131.83/ci/polarion/plannedIn
    plan = get_exported_param("PLANNED_IN")
    return plan


def polarion_xml_init():
    testrun_id = polarion_testrun_id()
    testrun_title = polarion_testrun_title()
    xml_file = os.path.join(
        os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir)),
        "polarion.xml"
    )
    xml_init(xml_file, "testsuites")
    tree = xml_read(xml_file)
    rootNode = tree.getroot()
    properties_node = xml_createNode(rootNode, "properties", '', '')
    attrs = {
            'polarion-project-id': 'RHELSS',
            'polarion-testrun-id': testrun_id,
            'polarion-testrun-title': testrun_title,
            'polarion-set-testrun-finished': 'true',
            'polarion-custom-assignee': 'yuefliu',
            'polarion-custom-isautomated': 'true',
            'polarion-custom-component': 'virt-who',
            'polarion-custom-arch': 'x86_64',
            'polarion-custom-subsystemteam': 'sst_subscription_virtwho',
            'polarion-custom-composeid': get_exported_param("RHEL_COMPOSE"),
            'polarion-custom-build': get_exported_param('VIRTWHO_BUILD'),
            'polarion-custom-jenkinsjobs': get_exported_param("BUILD_URL"),
            'polarion-custom-plannedin': polarion_planned_in(),
            'polarion-custom-notes': f"{get_exported_param('TRIGGER_TYPE')}"
    }
    logger.info(f'---{attrs}---')
    for name, value in attrs.items():
        attrs = {'name': name, 'value': value}
        propertie_node = xml_createNode(properties_node, "property", attrs, '')
    write_file(xml_file, fomatTree(rootNode))
    return xml_file, testrun_id


def polarion_xml_update(xml_file, files):
    ts_tests = 0
    ts_errors = 0
    ts_failures = 0
    ts_skip = 0
    ts_cases = list()
    for fd in files:
        data = read_file(fd)
        ts_lines = re.findall(r"<testsuite (.*?)>", data)
        logger.info(ts_lines)
        for line in ts_lines:
            ts_tests = ts_tests + int(re.findall(r'tests="(.*?)"', line)[0])
            ts_errors = ts_errors + int(re.findall(r'errors="(.*?)"', line)[0])
            ts_failures = ts_failures + int(re.findall(r'failures="(.*?)"', line)[0])
            ts_skip = ts_skip + int(re.findall(r'skipped="(.*?)"', line)[0])
        res = r'<testsuite .*?>(.*?)</testsuite>'
        cs_lines = re.findall(res, data, re.S|re.M)
        for line in cs_lines:
            ts_cases.append(line)
    # write env to runtest_info.txt
    total_fail = ts_errors+ts_failures
    total_executed = ts_tests-ts_skip
    total_passed = total_executed-total_fail
    fd = open(runtest_info, 'a')
    fd.write("TOTAL_CASE=%s\n" % ts_tests)
    fd.write("TOTAL_EXEC=%s\n" % total_executed)
    fd.write("TOTAL_PASS=%s\n" % total_passed)
    fd.write("TOTAL_FAIL=%s\n" % total_fail)
    fd.write("TOTAL_SKIP=%s\n" % ts_skip)
    if total_fail < 30:
        fd.write("TEST_STATUS=passed\n")
        fd.close()
    else:
        fd.write("TEST_STATUS=failed\n")
        fd.close()
        logger.warning("failed cases is > 30, cancel to polarion import!")
        sys.exit()
    data = '<testsuite name="nosetests" tests="%s" errors="%s" failures="0" skip="%s">\n</testsuite>' \
            %(ts_tests, total_fail, ts_skip)
    update_file(xml_file, "</testsuites>", data)
    for case in ts_cases:
        update_file(xml_file, "</testsuite>", case)
    tree = xml_read(xml_file)
    rootNode = tree.getroot()
    write_file(xml_file, fomatTree(rootNode))


def polarion_caseid_mapping(xml_file):
    tree = xml_read(xml_file)
    rootNode = tree.getroot()
    ts_nodes = rootNode.find("testsuite")
    cs_nodes = ts_nodes.findall("testcase")
    for node in cs_nodes:
        classname = node.attrib['classname']
        req = re.findall(r".tc_(.*?)_", classname)
        if len(req) > 0:
            tc_id = "tc_" + req[0]
            if tc_id in mapping.keys():
                polarion_case_id = mapping[tc_id]
                properties_node = xml_createNode(node, "properties", '', '')
                attrs = {'name': 'polarion-testcase-id', 'value': polarion_case_id}
                propertie_node = xml_createNode(properties_node, "property", attrs, '')
    write_file(xml_file, fomatTree(rootNode))


def polarion_xml_import(xml_file, testrun_id):
    username = deploy.polarion.username
    password = deploy.polarion.password
    import_url = deploy.polarion.import_url
    testrun_url = deploy.polarion.testrun_url
    cmd = "curl -k -u %s:%s -X POST -F file=@%s %s" % (username, password, xml_file, import_url) 
    output = os.popen(cmd).read()
    logger.info(cmd)
    logger.info(output)
    if "error-message" not in output:
        testrun = '{0}/testrun?id={1}'.format(testrun_url, testrun_id)
        fd = open(runtest_info, 'a')
        fd.write("TESTRUN_URL=%s\n" % testrun)
        fd.close()
        logger.info("Successed to import xml to polarion")
        logger.info(testrun)
    else:
        logger.error("Failed to import xml to polarion")


if __name__ == "__main__":
    files = parser_args(sys.argv[1:])
    xml_file, testrun_id = polarion_xml_init()
    polarion_xml_update(xml_file, files)
    polarion_caseid_mapping(xml_file)
    polarion_xml_import(xml_file, testrun_id)

# Please export below parms if you want to upload result manually.
# export RHEL_COMPOSE=RHEL-9.1.0-20220718.0
# export TRIGGER_LEVEL=tier1
# export HYPERVISOR_TYPE=esx
# export REGISTER_TYPE=satellite611
# export PLANNED_IN=
# export BUILD_URL=Jenkins_job_link_demo
# export VIRTWHO_BUILD=virt-who-1.30.5-2.el8_4
# export TRIGGER_TYPE=trigger-rhel
