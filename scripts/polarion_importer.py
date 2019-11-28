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

def polarion_testrun_id():
    job_name = get_exported_param("JOB_NAME")
    trigger_name = get_exported_param("TRIGGER_TYPE")
    server_type = get_exported_param("HYPERVISOR_TYPE")
    create_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if job_name != "" and trigger_name !="" and server_type !="":
        testrun_id = "virtwho_%s_%s_%s" % (job_name, trigger_name, create_time)
    else:
        testrun_id = "virtwho_testrun_by_ci_%s" % create_time
    testrun_url = '{0}/testrun?id={1}'.format(deploy.polarion.testrun_url, testrun_id)
    logger.info(testrun_url)
    fd = open(runtest_info, 'a')
    fd.write("TESTRUN_URL=%s\n" % testrun_url)
    fd.close()
    return testrun_id

def polarion_xml_init():
    testrun_id = polarion_testrun_id()
    xml_file = os.path.join(
        os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir)),
        "polarion.xml"
    )
    xml_init(xml_file, "testsuites")
    tree = xml_read(xml_file)
    rootNode = tree.getroot()
    properties_node = xml_createNode(rootNode, "properties", '', '')
    attrs = {
            'polarion-project-id': 'RedHatEnterpriseLinux7',
            'polarion-testrun-id': testrun_id,
            'polarion_custom_assignee': 'hsun',
            'polarion_custom_isautomated': 'true'}
    for name, value in attrs.items():
        attrs = {'name': name,'value': value}
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
            ts_skip = ts_skip + int(re.findall(r'skip="(.*?)"', line)[0])
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
    data = '<testsuite name="nosetests" tests="%s" errors="%s" failures="%s" skip="%s">\n</testsuite>' \
            %(ts_tests, ts_errors, ts_failures, ts_skip)
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
    username =  deploy.polarion.username
    password =  deploy.polarion.password
    import_url =  deploy.polarion.import_url
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
    # polarion_xml_import(xml_file, testrun_id)

