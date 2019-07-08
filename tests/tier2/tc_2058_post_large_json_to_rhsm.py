# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing

class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id="RHEL-171258")
        hypervisor_type = self.get_config('hypervisor_type')
        register_type = self.get_config('register_type')
        if 'esx' not in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        if 'satellite' not in register_type:
            self.vw_case_skip(register_type)
        self.vw_case_init()

        # case config
        results = dict()
        register_config = self.get_register_config()
        register_server = register_config['server']
        register_username = register_config['username']
        register_password = register_config['password']

        # case steps
        logger.info(">>>step1: create json data")
        json_file = "/root/test.json"
        json_data = self.vw_gen_json(hypervisors=100, guests=30)
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        self.paramiko_putfile(self.ssh_host(), json_file, json_file)

        logger.info(">>>step2: post json data")
        curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
        curl_cert = '--cert /etc/pki/consumer/cert.pem --key /etc/pki/consumer/key.pem'
        curl_json = '-d @"{0}"'.format(json_file)
        curl_host = 'https://{0}/rhsm/hypervisors'.format(register_server)
        cmd = "curl -X POST -s -k {0} {1} {2} {3}".format(curl_header, curl_cert, curl_json, curl_host)
        ret, output = self.runcmd(cmd, self.ssh_host())
        if ret == 0 and "error" not in output:
            logger.info("Succeeded to 600 hypervisors and 18000 guests to satellite")
            results.setdefault('step2', []).append(True)
        elif "foreman_tasks_sync_task_timeout" in output:
            task_id = re.findall(r'waiting for task (.*?) to finish exceeded', output)[-1]
            logger.info('task id: {}'.format(task_id))
            if task_id:
                cmd = "curl -X GET -s -k -u {0}:{1} https://{2}/foreman_tasks/api/tasks/{3}".format(
                        register_username, register_password, register_server, task_id) 
                start=time.time()
                while True:
                    ret, output = self.runcmd(cmd, self.ssh_host())
                    time.sleep(30)
                    end=time.time()
                    spend_time = int(end-start)
                    data = self.is_json(output.strip())
                    logger.info('task state: {}'.format(data['state']))
                    logger.info('task result: {}'.format(data['result']))
                    if spend_time >= 900:
                        results.setdefault('step2', []).append(False)
                        logger.info("Post timeout(900s)")
                        break
                    if data['state'] == 'stopped':
                        logger.info('task started_at: {}'.format(data['started_at']))
                        logger.info('task ended_at: {}'.format(data['ended_at']))
                        logger.info("Succeeded to 600 hypervisors and 18000 guests to satellite")
                        results.setdefault('step2', []).append(True)
                        break
        else:
            logger.warning("Failed to post json to satellite")
            logger.warning(output)
            results.setdefault('step2', []).append(False)

        # case result
        self.vw_case_result(results)
