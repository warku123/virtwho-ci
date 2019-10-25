from virt_who import *
from virt_who.base import Base

class Register(Base):
    #*****************************************
    # Attach Employee SKU and enable rhel repo
    #*****************************************
    def employee_sku_attach(self, ssh):
        self.rhsm_recovery(ssh)
        host = ssh['host']
        serverurl = "--serverurl={0}".format(deploy.register.serverurl)
        baseurl = "--baseurl={0}".format(deploy.register.baseurl)
        account = "--username={0} --password={1}".format(deploy.register.username, deploy.register.password)
        employee_sku = deploy.register.employee_sku
        is_registered = ""
        cmd = "subscription-manager clean; subscription-manager register {0} {1} {2}".format(serverurl, baseurl, account)
        for i in range(10):
            ret, output = self.runcmd(cmd, ssh, desc="register host to {0}".format(deploy.register.username))
            if ret == 0 or "already registered" in output:
                logger.info("Succeeded to register ({0}) to Stage Candlepin".format(host))
                is_registered = "Yes"
                break
            time.sleep(10)
        if is_registered != "Yes":
            raise FailException("Failed to register ({0})".format(host))
        cmd = "subscription-manager subscribe --pool={0}; subscription-manager repos --disable=*".format(employee_sku)
        status, output = self.run_loop(cmd, ssh, desc="attach Employee SKU")
        if status == "Yes":
            logger.info("Succeeded to attach Employee SKU({0})".format(host))
        else:
            raise FailException("Failed to attach Employee SKU({0})".format(host))

    def rhel_repo_enable(self, ssh):
        rhel_ver = self.rhel_version(ssh)
        cmd = "subscription-manager repos \
                --enable=rhel-{0}-server-rpms \
                --enable=rhel-{0}-server-optional-rpms \
                --enable=rhel-{0}-server-extras-rpms \
                --enable=rhel-server-rhscl-{0}-rpms".format(rhel_ver)
        status, output = self.run_loop(cmd, ssh, desc="enable rhel repos")
        if status != "Yes":
            raise FailException("Failed to enable rhel base repos({0})".format(ssh['host']))
        logger.info("Succeeded to enable rhel base repos({0})".format(ssh['host']))

    #**************************************
    # subscription-manager function 
    #**************************************
    def rhsm_override_uuid(self, ssh):
        ret, output = self.runcmd('uuidgen | tr a-z A-Z', ssh)
        option = r'{"dmi.system.uuid":"%s"}' % output.strip()
        cmd = "echo '{0}' > /etc/rhsm/facts/override_uuid.facts".format(option)
        ret, output = self.runcmd(cmd, ssh)
        ret, output = self.runcmd('cat /etc/rhsm/facts/override_uuid.facts', ssh)

    def rhsm_backup(self, ssh):
        ret, output = self.runcmd("ls /backup/rhsm.conf", ssh)
        if ret != 0 or "No such file or directory" in output:
            cmd = "rm -rf /backup/; mkdir -p /backup/; cp /etc/rhsm/rhsm.conf /backup/"
            self.runcmd(cmd, ssh)
        else:
            logger.info("rhsm.conf is backup already({0})".format(ssh['host']))

    def rhsm_recovery(self, ssh):
        self.system_unregister(ssh)
        ret, output = self.runcmd("rpm -qa | grep katello-ca-consumer | xargs rpm -e |sort", ssh)
        ret, output = self.runcmd("ls /backup/rhsm.conf", ssh)
        if ret == 0 and "No such file or directory" not in output:
            cmd = "rm -f /etc/rhsm/rhsm.conf; cp /backup/rhsm.conf /etc/rhsm/rhsm.conf"
            self.runcmd(cmd, ssh)
        else:
            logger.info("Failed to recovery rhsm.conf, backup file is not found({0})".format(ssh['host']))

    def system_register_config_validate(self, ssh, register_type, register_config):
        key = register_config['server']
        if "satellite" in register_type:
            key = self.get_hostname(register_config['ssh_sat'])
        cmd = "grep '{0}' /etc/rhsm/rhsm.conf".format(key)
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0 and output is not None and output != "":
            host_name = self.get_hostname(ssh)
            if "stage" in register_type:
                registered_id = self.stage_consumer_uuid(ssh, register_config, host_name, host_name)
            if "satellite" in register_type:
                registered_id = self.satellite_host_id(ssh, register_config, host_name, host_name)
            if registered_id is None or registered_id == "" or registered_id is False:
                return False
            else:
                return True
        else:
            return False

    def system_isregister(self, ssh, register_type, register_config):
        host = ssh['host']
        owner = register_config['owner']
        ret, output = self.runcmd("subscription-manager identity", ssh)
        if ret == 0:
            if "stage" in register_type:
                if owner not in output:
                    logger.info("System({0}) is registered to stage, but not expected owner".format(host))
                    self.system_register_config(ssh, register_type, register_config)
                    return False
            if self.system_register_config_validate(ssh, register_type, register_config):
                logger.info("System({0}) is registered as expected type".format(host))
                return True
            else:
                logger.info("System({0}) is registered, but not expected type".format(host))
        elif "has been deleted" in output:
            logger.info("System({0}) is unregistered on server side".format(host))
        else:
            logger.info("System({0}) is not registered".format(host))
        self.system_register_config(ssh, register_type, register_config)
        return False

    def system_register_config(self, ssh, register_type, register_config):
        server = register_config['server']
        host = ssh['host']
        self.rhsm_recovery(ssh)
        if "stage" in register_type:
            cmd = "sed -i -e 's|^hostname.*|hostname = {0}|g' /etc/rhsm/rhsm.conf".format(server)
            ret, output = self.runcmd(cmd, ssh)
            cmd = "sed -i -e 's|^baseurl.*|baseurl=https:\/\/stage.cdn.redhat.com|g' /etc/rhsm/rhsm.conf"
            ret, output = self.runcmd(cmd, ssh)
            if ret != 0:
                raise FailException("Failed to config stage register for host({0})".format(host))
        if "satellite" in register_type:
            cmd = "rpm -ihv http://{0}/pub/katello-ca-consumer-latest.noarch.rpm".format(server)
            ret, output = self.runcmd(cmd, ssh)
            if ret != 0:
                raise FailException("Failed to config satellite register for host({0})".format(host))

    def system_register(self, ssh, register_type, register_config):
        server = register_config['server']
        username = register_config['username']
        password = register_config['password']
        owner = register_config['owner']
        host = ssh['host']
        if "stage" in register_type:
            cmd = "subscription-manager register --username={0} --password={1}".format(username, password)
        if "satellite" in register_type:
            cmd = "subscription-manager register --username={0} --password={1} --org={2}".format(username, password, owner)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh)
            if ret == 0 or "system has been registered" in output or "system is already registered" in output:
                logger.info("Succeeded to register system {0} to {1}({2})".format(host, server, register_type))
                return True
            elif "certificate verify failed" in output:
                cmd = "sed -i -e 's|^insecure.*|insecure = 1|g' /etc/rhsm/rhsm.conf"
                ret, output = self.runcmd(cmd, ssh)
                self.system_unregister(ssh)
            elif "Please unregister or remove hosts" in output:
                self.system_unregister(ssh)
            time.sleep(180)
        raise FailException("Failed to register system {0} to {1}({2})".format(host, server, register_type))

    def system_register_with_ak(self, ssh, register_config, key_name):
        owner = register_config['owner']
        self.system_unregister(ssh)
        cmd = 'subscription-manager register  --org="{0}" --activationkey="{1}"'.format(owner, key_name)
        ret, output = self.runcmd(cmd, ssh)
        if 'system has been registered with ID' in output:
            logger.info('Succeded to register system using activation_key: {0}'.format(key_name))
        else:
            raise FailException('Failed to register system using activation_key')

    def system_unregister(self, ssh):
        for i in range(3):
            ret, output = self.runcmd("subscription-manager unregister", ssh)
            ret, output = self.runcmd("subscription-manager clean", ssh)
            if ret == 0:
                logger.info("Succeeded to unregister and clean system({0})".format(ssh['host']))
                return output.strip()
            logger.warning("unregister subscription return code {0}, try again after 180s...".format(ret))
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to unregister subscription after trying 3 loops")

    def sku_attr_callback(self, attrs):
        sku_attr = dict()
        attrs = attrs.strip().split("\n")
        for line in attrs:
            if re.match(r"^Subscription Name:", line):
                sku_name = line.split(':')[1].strip()
                sku_attr['sku_name'] = sku_name
            if re.match(r"^SKU:", line):
                sku_id = line.split(':')[1].strip()
                sku_attr['sku_id'] = sku_id
            if re.match(r"^Contract:", line):
                contract_id = line.split(':')[1].strip()
                sku_attr['contract_id'] = contract_id
            if re.match(r"^Pool ID:", line):
                pool_id = line.split(':')[1].strip()
                sku_attr['pool_id'] = pool_id
            if re.match(r"^Available:", line):
                available = line.split(':')[1].strip()
                sku_attr['available'] = available
            if re.match(r"^Suggested:", line):
                suggested = line.split(':')[1].strip()
                sku_attr['suggested'] = suggested
            if re.match(r"^Service Level:", line):
                service_level = line.split(':')[1].strip()
                sku_attr['service_level'] = service_level
            if re.match(r"^Service Type:", line):
                service_type = line.split(':')[1].strip()
                sku_attr['service_type'] = service_type
            if re.match(r"^Subscription Type:", line):
                sub_type = line.split(':')[1].strip()
                sku_attr['sub_type'] = sub_type
            if re.match(r"^Ends:", line):
                ends = line.split(':')[1].strip()
                sku_attr['ends'] = ends
            if re.match(r"^System Type:", line) \
                    or re.match(r"^Entitlement Type:", line):
                sku_type = line.split(':')[1].strip()
                sku_attr['sku_type'] = sku_type
        return sku_attr

    def system_sku_attr(self, ssh, sku_id, sku_type, exp_exist=True):
        if "physical" in sku_type.lower():
            sku_type= "Physical"
        elif "virtual" in sku_type.lower():
            sku_type= "Virtual"
        else:
            raise FailException("Unknown sku type, please check")
        for i in range(3):
            self.system_sku_refresh(ssh)
            cmd = "subscription-manager list --av --all --matches=%s | tail -n +4" % sku_id
            ret, output = self.runcmd(cmd, ssh, desc="subscription list matches")
            if ret == 0 and not output and exp_exist is False:
                logger.info("Succeeded to search, unexpected sku %s(%s) is not exist" % (sku_id, sku_type))
                return output
            if ret == 0 and "No available subscription pools" not in output \
                    and "Remote server error" not in output and "Pool ID:" in output:
                sku_list = output.strip().split('\n\n')
                sku_attrs = dict()
                if len(sku_list) > 0:
                    for attrs in sku_list:
                        pattern_1 = r"System Type:.*%s" % sku_type
                        pattern_2 = r"Entitlement Type:.*%s" % sku_type
                        if re.search(pattern_1, attrs) \
                                or re.search(pattern_2, attrs):
                            sku_attrs = self.sku_attr_callback(attrs)
                if sku_attrs and exp_exist:
                    logger.info("Succeeded to search, expected sku %s(%s) is exist" %(sku_id, sku_type))
                    return sku_attrs
                if sku_attrs and exp_exist is False:
                    logger.warning("Failed to search, unexpected sku %s(%s) is exist" %(sku_id, sku_type))
                if not sku_attrs and exp_exist:
                    logger.warning("Failed to search, expected sku %s(%s) is not exist" %(sku_id, sku_type))
                if not sku_attrs and exp_exist is False:
                    logger.info("Succeeded to search, unexpected sku %s(%s) is not exist" % (sku_id, sku_type))
                    return sku_attrs
            logger.warning("Failed to list expected subscription, try again after 180s...")
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to find %s(%s)" %(sku_id, sku_type))

    def system_sku_refresh(self, ssh):
        for i in range(3):
            cmd = "subscription-manager refresh"
            ret, output = self.runcmd(cmd, ssh, desc="subscription refresh")
            if ret == 0:
                logger.info("Succeeded to refresh subscription")
                return output.strip()
            if "Error loading certificate" in output:
                raise FailException("Failed to refresh subscription due to Error loading certificate, need to register")
            logger.warning("refresh subscription return code %s, try again after 180s ..." % ret)
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to refresh subscription after trying 3 loops")

    def system_sku_attach(self, ssh, pool_id=None, quantity=None):
        if pool_id is not None and quantity is not None:
            cmd = "subscription-manager attach --pool=%s --quantity=%s" % (pool_id, quantity)
        elif pool_id is not None and quantity is None:
            cmd = "subscription-manager attach --pool=%s"  % (pool_id)
        else:
            cmd = "subscription-manager attach --auto"
        logger.info("attach command: %s" % cmd)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh, desc="subscription attach")
            if ret == 0:
                logger.info("Succeeded to attach subscription")
                return output.strip()
            if "--auto" in cmd and "Unable to find available" in output:
                logger.warning("Failed to attach subscription by auto")
                return output.strip()
            if "Multi-entitlement not supported" in output:
                logger.warning("It's a 'Standard' subscription type, quantity=2*N is only used for 'Stackable'")
                return output.strip()
            logger.warning("attach subscription return code {0}, try again after 180s...".format(ret))
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to attach subscription after trying 3 loops")

    def system_sku_consumed(self, ssh, exp_exist=True):
        for i in range(3):
            self.system_sku_refresh(ssh)
            cmd = "subscription-manager list --co"
            ret, output = self.runcmd(cmd, ssh, desc="subscription list consumed")
            status = re.findall(r"Status Details:\s+(.*?)\n", output)
            if ret != 0 or "Subscription management service doesn't support" in output:
                logger.warning("Consumed status is: %s, try again after 180s..." % status)
                logger.warning(output)
                time.sleep(180)
            elif exp_exist == True and "No consumed subscription pools" in output:
                logger.warning("No consumed found, try again after 180s...")
                logger.warning(output)
                time.sleep(180)
            else:
                logger.info("Succeeded to list consumed with status: %s" % status)
                return output.strip()
        raise FailException("Failed to list consumed after trying 3 loops")

    def system_sku_installed(self, ssh):
        for i in range(3):
            self.system_sku_refresh(ssh)
            cmd = "subscription-manager list --in | tail -n +4"
            ret, output = self.runcmd(cmd, ssh, desc="subscription list installed")
            if ret == 0 and output.strip() != "":
                attrs = dict()
                output = output.strip().split('\n')
                for line in output:
                    if re.match(r"^Product Name:", line):
                        product_name = line.split(':')[1].strip()
                        attrs['product_name'] = product_name
                    if re.match(r"^Product ID:", line):
                        product_id = line.split(':')[1].strip()
                        attrs['product_id'] = product_id
                    if re.match(r"^Version:", line):
                        version = line.split(':')[1].strip()
                        attrs['version'] = version
                    if re.match(r"^Arch:", line):
                        arch = line.split(':')[1].strip()
                        attrs['arch'] = arch
                    if re.match(r"^Status:", line):
                        status = line.split(':')[1].strip()
                        attrs['status'] = status
                    if re.match(r"^Status Details:", line):
                        status_details = line.split(':')[1].strip()
                        attrs['status_details'] = status_details
                    if re.match(r"^Starts:", line):
                        starts = line.split(':')[1].strip()
                        attrs['starts'] = starts
                    if re.match(r"^Ends:", line):
                        ends = line.split(':')[1].strip()
                        attrs['ends'] = ends
                logger.info("Succeeded to list installed subscription, status: %s" % attrs['status'])
                return attrs
            logger.warning("list installed subscription return code %s, try again after 180s..." % ret)
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to list installed subscription after trying 3 loops")

    def system_sku_unattach(self, ssh, pool_id=None):
        if pool_id is not None:
            cmd = "subscription-manager remove --pool=%s" % pool_id
        else:
            cmd = "subscription-manager remove --all"
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh, desc="subscription unattached")
            if ret ==0:
                logger.info("Succeeded to remove consumed subscription")
                return output.strip()
            if "Error loading certificate" in output:
                logger.warning("Failed to remove subscription due to Error loading certificate, register again")
                self.system_unregister(ssh)
                return False
            co_data = self.system_sku_consumed(ssh, exp_exist=False)
            if "No consumed subscription pools" in co_data:
                logger.info("Succeeded to remove consumed subscription")
                return output.strip()
            logger.warning("remove subscription return code %s, try again after 180s..." % ret)
            logger.warning(output)
            time.sleep(180)
        raise FailException("Failed to remove subscription after trying 3 loops")

    def system_disable_auto_attach(self, ssh):
        cmd = "subscription-manager auto-attach --disable"
        ret, output = self.runcmd(cmd, ssh, desc="subscription disable auto-attach")
        if ret == 0:
            logger.info("Succeeded to disable auto-attach")
        else:
            raise FailException("Failed to disable auto-attach")

    def system_custom_facts_create(self, ssh, facts_key, facts_value):
        option = r'{"%s":"%s"}' % (facts_key, facts_value)
        cmd = "echo '%s' > /etc/rhsm/facts/custom.facts" % option
        ret, output = self.runcmd(cmd, ssh, desc="create custom.facts")
        if ret != 0:
            raise FailException("Failed to create custom.facts")
        logger.info("Succeeded to create custom.facts")
        cmd = "subscription-manager facts --update"
        ret, output = self.runcmd(cmd, ssh, desc="subscription facts update")
        '''time sleep for satellite conflicts with tasks when run facts --update'''
        time.sleep(60)
        if ret != 0 and "Successfully updated" not in output:
            raise FailException("Failed to update subscription facts")
        logger.info("Succeeded to update subscription facts")
        cmd = "subscription-manager facts --list |grep '%s:'" % facts_key
        ret, output = self.runcmd(cmd, ssh, desc="subscription facts check")
        if ret != 0 and facts_key not in output:
            raise FailException("Failed to check subscription facts: %s" % facts_key)
        actual_value = output.split(": ")[1].strip()
        if facts_value == actual_value:
            logger.info("Succeeded to check subscription facts: %s:%s" %(facts_key, actual_value))
            return True
        else:
            logger.error("Failed to check subscription facts: %s:%s" %(facts_key, actual_value))
            return False

    def system_custom_facts_remove(self, ssh):
        ret, output = self.runcmd('rm -f /etc/rhsm/facts/custom.facts', ssh)
        for i in range(3):
            ret, output = self.runcmd('subscription-manager facts --update', ssh)
            time.sleep(60)
            if ret == 0 and "Successfully updated" in output:
                logger.info("Succeeded to remove custom.facts")
                return True
            time.sleep(60)
        raise FailException("Failed to remove custom.facts")

    #**************************************
    # Stage API Function
    # https://access.redhat.com/solutions/431773
    # https://hosted.englab.nay.redhat.com/issues/11373
    #**************************************
    def stage_consumer_clean(self, ssh, register_config):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        owner = register_config['owner']
        cmd = "curl -s -k -u {0}:{1} {2}/owners/{3}/consumers".format(
                username, password, api, owner)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh)
            consumer_list = self.is_json(output.strip())
            if consumer_list is not False and consumer_list is not None and consumer_list != "":
                for item in consumer_list:
                    consumer_uuid = item['uuid'].strip()
                    cmd = "curl -s -k -u {0}:{1} -X DELETE {2}/consumers/{3}".format(
                            username, password, api, consumer_uuid)
                    ret, output = self.runcmd(cmd, ssh)
                    logger.info("Succeeded to delete consumer: {0}".format(consumer_uuid))
                return True
            logger.warning("can't get the expected json data, try again after 30s ...")
            time.sleep(30)
        logger.error("Failed to clean consumers due to invalid json data")
        return False

    def stage_consumer_uuid(self, ssh, register_config, host_name, host_uuid, retry=True):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        owner = register_config['owner']
        cmd = "curl -s -k -u {0}:{1} {2}/owners/{3}/consumers".format(
                username, password, api, owner)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh)
            consumer_list = self.is_json(output.strip())
            if ret == 0 and "system is unable to complete the requested" not in output \
                    and consumer_list is not False and consumer_list is not None and consumer_list != "" \
                    and (host_name in output or host_uuid in output):
                results = dict()
                for item in consumer_list:
                    if host_name in item['name'].strip() or host_uuid in item['name'].strip():
                        consumer_uuid = item['uuid'].strip()
                        last_checkin = item['lastCheckin'].strip()
                        results[last_checkin] = consumer_uuid
                if results:
                    latest_time = max(results.keys())
                    consumer_uuid = results[latest_time]
                    logger.info("Succeeded to get stage consumer_uuid: {0}:{1}".format(
                        host_name, consumer_uuid))
                    return consumer_uuid
            if retry is False:
                return None
            logger.warning("no consumer_uuid found, try again after 180s...")
            logger.warning(output)
            time.sleep(180)
        logger.error("Failed to get stage consumer_uuid for host({0})".format(host_name))
        return None

    def stage_consumer_delete(self, ssh, register_config, host_name, host_uuid, retry=True):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        consumer_uuid = self.stage_consumer_uuid(ssh, register_config, host_name, host_uuid, retry)
        if consumer_uuid is not None and consumer_uuid != "":
            cmd = "curl -s -k -u {0}:{1} -X DELETE {2}/consumers/{3}".format(
                    username, password, api, consumer_uuid)
            ret, output = self.runcmd(cmd, ssh)
            cmd = "curl -s -k -u {0}:{1} -X GET {2}/consumers/{3}".format(
                    username, password, api, consumer_uuid)
            ret, output = self.runcmd(cmd, ssh)
            if host_name not in output:
                logger.info("Succeeded to delete host {0}".format(host_name))
        else:
            logger.info("Host({0}) is not found in stage server".format(host_name))
        return True

    def stage_consumer_attach(self, ssh, register_config, host_name, host_uuid, pool_id):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        consumer_uuid = self.stage_consumer_uuid(ssh, register_config, host_name, host_uuid)
        if consumer_uuid is not None and consumer_uuid != "":
            cmd = "curl -s -k -u {0}:{1} -X POST {2}/consumers/{3}/entitlements?pool={4}".format(
                    username, password, api, consumer_uuid, pool_id)
            for i in range(3):
                ret, output = self.runcmd(cmd, ssh)
                if "unit has already had the subscription matching pool ID" in output:
                    logger.warning("consumer_uuid({0}) is already attached to pool({1}), will remove it".format(
                        consumer_uuid, pool_id))
                    self.stage_consumer_unattach(ssh, register_config, host_name, host_uuid)
                if ret == 0 and consumer_uuid in output and pool_id in output:
                    logger.info("Succeeded to attach pool({0}) for consumer({1})".format(
                        pool_id, consumer_uuid))
                    return True
                logger.warning("Failed to attach pool({0}) for consumer({1}), try again after 15s".format(
                    pool_id, consumer_uuid))
                time.sleep(15)
        raise FailException("Failed to attach pool({0}) for consumer({1})".format(
            pool_id, consumer_uuid))

    def stage_consumer_unattach(self, ssh, register_config, host_name, host_uuid):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        consumer_uuid = self.stage_consumer_uuid(ssh, register_config, host_name, host_uuid)
        if consumer_uuid is not None and consumer_uuid != "":
            cmd = "curl -s -k -u {0}:{1} -X DELETE {2}/consumers/{3}/entitlements".format(
                    username, password, api, consumer_uuid)
            ret, output = self.runcmd(cmd, ssh)
            if ret == 0:
                logger.info("Succeeded to remove attached pools for consumer: {0}".format(host_name))
                return True
        raise FailException("Failed to remove attached pools for consumer: {0}".format(host_name))

    def stage_consumer_associate(self, ssh, register_config, host_name, host_uuid, guest_uuid):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        consumer_uuid = self.stage_consumer_uuid(ssh, register_config, host_name, host_uuid)
        if consumer_uuid is not None and consumer_uuid != "":
            cmd = "curl -s -k -u {0}:{1} {2}/consumers/{3}/guestids".format(
                    username, password, api, consumer_uuid)
            ret, output = self.runcmd(cmd, ssh)
            if ret == 0 and guest_uuid in output:
                logger.info("Hypervisor and Guest are associated in stage web")
                return True
        logger.error("Hypervisor and Guest are not associated in stage web")
        return False

    def stage_job_delete(self, ssh, register_config, job_ids):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        if len(job_ids) > 0:
            for job_id in job_ids:
                cmd = "curl -s -k -u {0}:{1} -X DELETE {2}/jobs/{3}".format(
                        username, password, api, job_id.strip())
                ret, output = self.runcmd(cmd, ssh)
                logger.info("Finished to cancel job {0}".format(job_id))

    #**************************************
    # Satellite API Function
    #**************************************
    def satellite_host_setting(self, ssh, register_config):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/settings/?per_page=1000".format(username, password, api)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh, debug=False)
            output = self.is_json(output.strip())
            if output is not False and output is not None and output != "":
                for item in output["results"]:
                    if item['name'] == "unregister_delete_host":
                        curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
                        json_data = json.dumps('{"value":"true"}')
                        cmd = 'curl -X PUT -s -k {0} -u {1}:{2} -d {3} {4}/api/settings/{5}'.format(
                                curl_header, username, password, json_data, api, item['id'])
                        ret, output = self.runcmd(cmd, ssh)
                        if ret == 0 and '"value":true' in output:
                            logger.info("Succeeded to update unregister_delete_host option to True")
                        else:
                            logger.error("Failed to update unregister_delete_host option to True")
                        break
                return True
        logger.error("Failed to set satellite host for unregister_delete_host")
        return False

    def satellite_host_id(self, ssh, register_config, host_name, host_uuid, retry=True):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/?per_page=1000".format(
                username, password, api)
        for i in range(3):
            rex = [host_name, host_name.lower(), host_uuid, host_uuid.lower()]
            ret, output = self.runcmd(cmd, ssh, desc="satellite hosts list", debug=False)
            output = self.is_json(output.strip())
            if output is not False and output is not None and output != "" and 'results' in output.keys():
                results = dict()
                for item in output['results']:
                    if ret == 0 and any(key in item['name'] for key in rex):
                        host_id = str(item['id']).strip()
                        create_at = item['created_at'].strip()
                        results[create_at] = host_id
                if results:
                    latest_time = max(results.keys())
                    host_id = results[latest_time]
                    logger.info("Succeeded to get satellite host_id: {0}:{1}".format(host_name, host_id))
                    return host_id
            if retry is False:
                return None
            logger.warning("no results found for host_id, try again after 15s...")
            time.sleep(15)
        logger.warning("Failed to get satellite host_id for host({0}), maybe mapping is not sent".format(host_name))
        return None

    def satellite_katello_id(self, ssh, register_config, pool_id, org_name="Default_Organization"):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        org_id = self.satellite_org_id_get(ssh, register_config, org_name)
        cmd = "curl -X GET -s -k -u {0}:{1} {2}/katello/api/organizations/{3}/subscriptions/?per_page=1000".format(
                username, password, api, org_id)
        for i in range(3):
            ret, output = self.runcmd(cmd, ssh, desc="satellite pools list", debug=False)
            output = self.is_json(output.strip())
            if output is not False and output is not None and output != "" and 'results' in output.keys():
                for item in output['results']:
                    if pool_id in item['cp_id']:
                        katello_id = str(item['id']).strip()
                        logger.info("Succeeded to get satellite katello_id: {0}({1})".format(katello_id, pool_id))
                        return katello_id
            logger.warning("no results found for katello_id, try again after 15s...")
            time.sleep(15)
        logger.error("Failed to get satellite katello_id for pool({0})".format(pool_id))
        return None

    def satellite_host_delete(self, ssh, register_config, host_name, host_uuid, retry=True):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        host_id = self.satellite_host_id(ssh, register_config, host_name, host_uuid, retry)
        if host_id is not None and host_id != "":
            cmd = "curl -X DELETE -s -k -u {0}:{1} {2}/api/v2/hosts/{3}".format(
                    username, password, api, host_id)
            ret, output = self.runcmd(cmd, ssh, desc="satellite host delete")
            cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}".format(
                    username, password, api, host_id)
            ret, output = self.runcmd(cmd, ssh, desc="satellite host get")
            if host_name not in output:
                logger.info("Succeeded to delete host: {0}".format(host_name))
        else:
            logger.info("Host({0}) is not found in satellite server".format(host_name))
        return True

    def satellite_host_attach(self, ssh, register_config, host_name, host_uuid, pool_id, quantity=1):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        host_id = self.satellite_host_id(ssh, register_config, host_name, host_uuid)
        katello_id = self.satellite_katello_id(ssh, register_config, pool_id)
        if host_id is not None and host_id != "" and katello_id is not None and katello_id != "":
            curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
            json_data = json.dumps('{"subscriptions":[{"id":%s, "quantity":%s}]}' % (katello_id, quantity))
            cmd = 'curl -X PUT -s -k {0} -u {1}:{2} -d {3} {4}/api/v2/hosts/{5}/subscriptions/add_subscriptions'.format(
                    curl_header, username, password, json_data, api, host_id)
            for i in range(3):
                ret, output = self.runcmd(cmd, ssh, desc="satellite attach pool")
                if pool_id in output and "subscription_id" in output and "product_id" in output:
                    logger.info("Succeeded to attach pool({0}) for host_id({0})".format(pool_id, host_id))
                    return True
                logger.warning("can't attach pool({0}) for host_id({1}), try again after 15s".format(pool_id, host_id))
                time.sleep(15)
        raise FailException("Failed to attach pool({0}) for host_id({1})".format(pool_id, host_id))

    def satellite_host_unattach(self, ssh, register_config, host_name, host_uuid):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        host_id = self.satellite_host_id(ssh, register_config, host_name, host_uuid)
        if host_id is not None and host_id != "":
            '''get all the attached subscriptions(katello_ids) for the host'''
            katello_ids = dict()
            cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}/subscriptions/?per_page=1000".format(
                    username, password, api, host_id)
            for i in range(3):
                ret, output = self.runcmd(cmd, ssh, desc="satellite host consumed list", debug=False)
                output = self.is_json(output.strip())
                if output is not False and output is not None and output != "" and 'results' in output.keys():
                    for item in output['results']:
                        if 'cp_id' in item.keys():
                            katello_ids[item['cp_id']] = str(item['id']).strip()
                    break
                logger.warning("no results found for host subscriptions, try again after 15s...")
                time.sleep(15)
            '''remove all the attached subscriptions(katello_ids) for the host'''
            if katello_ids:
                logger.info("Succeeded to find consumed pools for host_id({0}): {1}".format(host_id, katello_ids))
                for cp_id, katello_id in katello_ids.items():
                    curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
                    json_data = json.dumps('{"subscriptions":[{"id":%s}]}' % katello_id)
                    cmd = 'curl -X PUT -s -k {0} -u {1}:{2} -d {3} {4}/api/v2/hosts/{5}/subscriptions/remove_subscriptions'.format(
                            curl_header, username, password, json_data, api, host_id)
                    ret, output = self.runcmd(cmd, ssh, desc="satellite remove pool")
                    if ret == 0:
                        logger.info("Succeeded to remove pool({0}) for host_id({1})".format(cp_id, host_id))
                    else:
                        logger.error("Failed to remove pool({0}) for host_id({1})".format(cp_id, host_id))
            else:
                logger.info("no consumed pools for host_id({0})".format(host_id))

    def satellite_host_associate(self, ssh, register_config, hypervisor_hostname, hypervisor_uuid, guest_hostname, guest_uuid):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        hypervisor_hostid = self.satellite_host_id(ssh, register_config, hypervisor_hostname, hypervisor_uuid)
        guest_hostid = self.satellite_host_id(ssh, register_config, guest_hostname, guest_uuid)
        for i in range(3):
            time.sleep(60)
            results = list()
            if hypervisor_hostid is not None and hypervisor_hostid != "" \
                    and guest_hostid is not None and guest_hostid != "":
                cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}".format(username, password, api, hypervisor_hostid)
                ret, output = self.runcmd(cmd, ssh, desc="satellite host show")
                rex = [guest_hostname, guest_hostname.lower(), guest_uuid, guest_uuid.lower()]
                if ret == 0 and any(key in output for key in rex):
                    results.append("Yes")
                    logger.info("Succeeded to find guest associated info in hypervisor page")
                else:
                    results.append("No")
                    logger.error("Failed to find guest associated info in hypervisor page")
                cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}".format(username,password, api, guest_hostid)
                ret, output = self.runcmd(cmd, ssh, desc="satellite host show")
                rex = [hypervisor_hostname, hypervisor_hostname.lower(), hypervisor_uuid, hypervisor_uuid.lower()]
                if ret == 0 and any(key in output for key in rex):
                    results.append("Yes")
                    logger.info("Succeeded to find hypervisor host associated info in guest page")
                else:
                    results.append("No")
                    logger.error("Failed to find hypervisor host associated info in guest page")
            if "No" in results or results is None:
                logger.warning("no hypervisor and guest associated info found, try again after 60s...")
            else:
                return True
        return False

    def satellite_org_create(self, ssh, register_config, org_name, org_label="", desc=""):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        if org_label == "":
            org_label = org_name
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        org_json = json.dumps('{"name":"%s", "label":"%s", "description":"%s"}' \
                            % (org_name, org_label, desc))
        cmd = "curl {0} -X POST -s -k -u {1}:{2} -d {3} {4}/katello/api/organizations".format(
                curl_header, username, password, org_json, api)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            for i in range(3):
                output = self.satellite_org_list(ssh, register_config)
                if 'results' in output.keys():
                    for item in output['results']:
                        if item['name'] == org_name:
                            logger.info("succeeded to create organization {0}".format(org_name))
                            return
                logger.warning("no org found for creation, try again after 15s...")
                time.sleep(15)
        raise FailException("Failed to create organization")

    def satellite_org_list(self, ssh, register_config):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        for i in range(3):
            cmd = "curl -X GET -s -k -u {0}:{1} '{2}/katello/api/organizations'".format(
                    username, password, api)
            ret, output = self.runcmd(cmd, ssh)
            output = self.is_json(output.strip())
            if ret == 0 and output is not False and output is not None and output != "":
                return output
        raise FailException("Failed to list organization info")

    def satellite_org_id_get(self, ssh, register_config, org_name):
        for i in range(3):
            org_list = self.satellite_org_list(ssh, register_config)
            if 'results' in org_list.keys():
                for item in org_list['results']:
                    if item['label'] == org_name:
                        org_id = item['id']
                        return org_id
            logger.warning("no {0} organization find, try again after 15s...".format(org_name))
            time.sleep(15)
        logger.warning("Failed to find organization: {0}".format(org_name))
        return False

    def satellite_hosts_list(self, ssh, register_config, org_name):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        org_id = self.satellite_org_id_get(ssh, register_config, org_name)
        cmd = "curl -X GET -s -k -u {0}:{1} '{2}/api/organizations/{3}/hosts'".format(username, password, api, org_id)
        ret, output = self.runcmd(cmd, ssh, debug=False)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("succeeded to list all hosts")
            return output
        else:
            raise FailException("Failed to list all hosts")

    def satellite_hosts_search(self, ssh, register_config, org_name, hostname, hostuuid, exp_exist=True):
        hosts = self.satellite_hosts_list(ssh, register_config, org_name)
        if 'results' in hosts.keys():
            name_list = []
            for item in hosts['results']:
                name = item['name']
                name_list.append(name)
            name_list = str(name_list)
            res1 = re.findall('.*%s.*' % hostname, name_list, re.I)
            res2 = re.findall('.*%s.*' % hostuuid, name_list, re.I)
            num = len(res1) + len(res2)
            if num > 0 and exp_exist is True:
                    logger.info("Succeeded to search, expected host is exist in org {0}".format(org_name))
                    return True
            if num == 0 and exp_exist is True:
                    logger.error("Failed to search, expected host is not exist in org {0}".format(org_name))
                    return False
            if num > 0 and exp_exist is False:
                    logger.error("Failed to search, unexpected host is exist in org {0}".format(org_name))
                    return False
            if num == 0 and exp_exist is False:
                    logger.info("Succeeded to search, unexpected host is not exist in org {0}".format(org_name))
                    return True
        else:
            if exp_exist is True:
                logger.error("Failed to search, expected host is not exist in org {0}".format(org_name))
                return False
            if exp_exist is False:
                logger.info("Succeeded to search, unexpected host is not exist in org {0}".format(org_name))
                return True

    def satellite_hosts_get(self, ssh, register_config, host_name, host_uuid, desc=""):
        admin_user = register_config['username']
        admin_passwd = register_config['password']
        server = register_config['server']
        baseurl = "https://{0}".format(server)
        host_id = self.satellite_host_id(ssh, register_config, host_name, host_uuid)
        cmd = "curl -X GET -s -k -u {0}:{1} {2}/api/v2/hosts/{3}" \
            .format(admin_user, admin_passwd, baseurl, host_id)
        ret, output = self.runcmd(str(cmd), ssh, desc=desc)
        if ret == 0 and output is not False and output is not None:
            logger.info("Succeed to get expected host info")
            output = self.is_json(output.strip())
            return output
        else:
            logger.info("Failed to get host info")
            return None

    def satellite_active_key_create(self, ssh, register_config, key_name, org_id=1, desc=""):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        active_key_json = json.dumps('\
                {"organization_id":"%s", \
                "name":"%s", "description":"%s", \
                "environment_id":1, \
                "environment": {"id":1, "name":"Library"}, \
                "content_view_id":"1", \
                "content_view":{"id":1,"name":"Default Organization View"}}' % (org_id, key_name, desc))
        cmd = "curl {0} -X POST -s -k -u {1}:{2} -d {3} {4}/katello/api/activation_keys".format(
                curl_header, username, password, active_key_json, api)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            for i in range(5):
                output = self.satellite_active_key_list(ssh, register_config, org_id)
                if 'results' in output.keys():
                    for item in output['results']:
                        if item['name'] == key_name:
                            logger.info("succeeded to create activation_key")
                            return
                logger.warning("no results found for created activation_key, try again after 30s...")
                time.sleep(30)
        raise FailException("Failed to create activation_key")

    def satellite_active_key_delete(self, ssh, register_config, key_name, org_id=1):
        key_id = self.satellite_active_key_id_get(ssh, register_config, key_name, org_id)
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        cmd = "curl {0} -X DELETE -s -k -u {1}:{2} {3}/katello/api/activation_keys/{4}".format(
                curl_header, username, password, api, key_id)
        ret, output = self.runcmd(cmd, ssh)
        if ret == 0:
            for i in range(5):
                output = self.satellite_active_key_list(ssh, register_config, org_id)
                if output['total'] != 0:
                    for item in output['results']:
                        id_list = []
                        id_list.append(item['id'])
                        if key_id not in id_list:
                            logger.info("Succeeded to delete activation_key id: {0}".format(key_id))
                            return
                        logger.warning("Activation key still exists, try again after 30s...")
                        time.sleep(30)
                else:
                    logger.info("Succeeded to delete activation_key id: {0}".format(key_id))
                    return
        raise FailException("Failed to delete activation_key")

    def satellite_active_key_list(self, ssh, register_config, org_id=1):
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        cmd = "curl -X GET -s -k -u {0}:{1} '{2}/katello/api/activation_keys?organization_id={3}'".format(
                username, password, api, org_id)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            return output
        raise FailException("Failed to list activation_keys info")

    def satellite_active_key_id_get(self, ssh, register_config, key_name, org_id=1):
        output = self.satellite_active_key_list(ssh, register_config, org_id)
        if output is not False and output is not None and output != "":
            for item in output['results']:
                if item['name'] == key_name:
                    key_id = item['id']
                    logger.info("Succeded to get activation key id: %s" % key_id)
                    return key_id
        raise FailException("Failed to get activation key id of %s" % key_name)

    def satellite_active_key_attach_sku(self, ssh, register_config, key_name, katello_id, org_id=1, quantity=1):
        key_id = self.satellite_active_key_id_get(ssh, register_config, key_name, org_id)
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        curl_header = '-H "accept:application/json,version=2" -H "content-type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":%s, "quantity":%s}' \
                 % (key_id, katello_id, quantity))
        cmd = "curl {0} -X PUT -s -k -u {1}:{2} -d {3} {4}/katello/api/v2/activation_keys/{5}/add_subscriptions".format(
                curl_header, username, password, data_json, api, key_id)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to add subscription {0} for activation key".format(katello_id))
        else:
            raise FailException("Failed to add subscription for activation key")

    def satellite_active_key_unattach_sku(self, ssh, register_config, key_name, katello_id, org_id=1):
        key_id = self.satellite_active_key_id_get(ssh, register_config, key_name, org_id)
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"id":"%s", "subscription_id":"%s"}' \
                 % (key_id, katello_id))
        cmd = "curl {0} -X PUT -s -k -u {1}:{2} -d {3} {4}/katello/api/v2/activation_keys/{5}/remove_subscriptions".format(
                curl_header, username, password, data_json, api, key_id)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to remove subscription from activation key")
        else:
            raise FailException("Failed to remove subscription from activation key")

    def satellite_active_key_auto_attach_enable(self, ssh, register_config, key_name, org_id=1, auto_attach='true'):
        key_id = self.satellite_active_key_id_get(ssh, register_config, key_name, org_id)
        api = register_config['api']
        username = register_config['username']
        password = register_config['password']
        curl_header = '-H "Accept:application/json,version=2" -H "Content-Type:application/json"'
        data_json = json.dumps('{"organization_id":"%s", "auto_attach":"%s"}' % (org_id, auto_attach))
        cmd = "curl {0} -X PUT -s -k -u {1}:{2} -d {3} {4}/katello/api/activation_keys/{5}".format(
                curl_header, username, password, data_json, api, key_id)
        ret, output = self.runcmd(cmd, ssh)
        output = self.is_json(output.strip())
        if ret == 0 and output is not False and output is not None and output != "":
            logger.info("Succeeded to set auto_attach to {}".format(auto_attach))
        else:
            raise FailException("Failed to set auto_attach")

