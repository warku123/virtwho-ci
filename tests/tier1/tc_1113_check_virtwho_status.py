# coding:utf-8
from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.testing import Testing


class Testcase(Testing):
    def test_run(self):
        self.vw_case_info(os.path.basename(__file__), case_id='RHEL-196077')
        compose_id = self.get_config('rhel_compose')
        if 'RHEL-9' not in compose_id:
            self.vw_case_skip(compose_id)
        configs = self.get_hypervisor_config()
        hypervisor_type = configs['type']
        if 'libvirt-local' in hypervisor_type:
            self.vw_case_skip(hypervisor_type)
        hypervisor_server = configs['server']
        register = self.get_register_config()
        register_server = register['server']
        self.vw_case_init()

        # case config
        results = dict()
        config_name = 'virtwho-config'
        config_file = f'/etc/virt-who.d/{config_name}.conf'
        self.vw_etc_d_mode_create(config_name, config_file)

        # case steps
        logger.info(">>>step1: Run virt-who to report the mapping")
        data, tty_output, rhsm_output = self.vw_start(cli='virt-who -do')
        res1 = self.op_normal_value(data, exp_error=0, exp_thread=0, exp_send=1)
        results.setdefault('step1', []).append(res1)

        logger.info(">>>step2: Check '#virt-who --status' with good configuration")
        status = self.vw_status()
        results.setdefault('step2', []).append(
            'success' in status[config_name]['source_status'] and
            'success' in status[config_name]['destination_status']
        )

        logger.info(">>>step3: Check '#virt-who -s' with good configuration")
        status = self.vw_status(cmd='virt-who -s')
        results.setdefault('step3', []).append(
            'success' in status[config_name]['source_status'] and
            'success' in status[config_name]['destination_status']
        )

        logger.info(">>>step4: Check #virt-who --status --json")
        json = self.vw_status(if_json=True)
        source = json[config_name]['source']
        destination = json[config_name]['destination']
        if 'libvirt' in hypervisor_type:
            source_conn = f'qemu+ssh://root@{hypervisor_server}/system?no_tty=1'
        elif 'esx' in hypervisor_type:
            source_conn = f'https://{hypervisor_server}'
        elif 'rhevm' in hypervisor_type:
            source_conn = hypervisor_server.split('ovirt-engine')[0].strip()
        elif 'kubevirt' in hypervisor_type:
            source_conn = deploy.kubevirt.endpoint
        else:
            source_conn = hypervisor_server
        results.setdefault('step4', []).append(
            source['connection'] == source_conn and
            source['status'] == 'success' and
            source['last_successful_retrieve'].split(' ')[2] == 'UTC' and
            source['hypervisors'] >= 1 and
            source['guests'] >= 1 and
            destination['connection'] == register_server and
            destination['status'] == 'success' and
            destination['last_successful_send'].split(' ')[2] == 'UTC' and
            destination['last_successful_send_job_status'] == 'FINISHED'
        )

        logger.info(">>>step5: Check '#virt-who -s' with bad configuration")
        option = 'password'
        if 'kubevirt' in hypervisor_type:
            option = 'kubeconfig'
        if 'libvirt-remote' in hypervisor_type:
            option = 'server'
        self.vw_option_update_value(f'{option}', 'xxx', config_file)
        self.vw_option_update_value('owner', 'xxx', config_file)
        status = self.vw_status(cmd='virt-who -s')
        results.setdefault('step5', []).append(
            'failure' in status[config_name]['source_status'] and
            'failure' in status[config_name]['destination_status']
        )

        logger.info(">>>step6: Check '#virt-who --status --json' with bad configuration")
        json = self.vw_status(if_json=True)
        source = json[config_name]['source']
        destination = json[config_name]['destination']
        results.setdefault('step6', []).append(
            source['status'] == 'failure' and
            destination['status'] == 'failure'
        )

        # case result
        self.vw_case_result(results)
