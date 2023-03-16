import os
import time
import re
import logging

import pytest

from tests.integration.helpers import exec_test_command, exec_failing_test_command, INVALID_HOST, SUCCESS_STATUS_CODE, get_token


class TestDomainRecords:

    def test_create_a_domain(self):
        timestamp = str(time.time())

        # Current domain list
        output_current = os.popen('linode-cli domains list --format="id" --text --no-header').read()

        result = os.system('linode-cli domains create \
        --type master \
        --domain "' + timestamp + 'example.com" \
        --soa_email="pthiel@linode.com" \
        --text \
        --no-header')

        # Assert on status code returned from creating domain
        assert(result == SUCCESS_STATUS_CODE)

        output_after = os.popen('linode-cli domains list --format="id" --text --no-header').read()

        # Check if list is bigger than previous list
        assert(len(output_after.splitlines()) > len(output_current.splitlines()), "the list is not updated with new domain..")


    def test_create_domain_srv_record(self):
        domain_ids = os.popen('linode-cli domains list --format="id" --text --no-header').read()

        domain_id_arr = domain_ids.splitlines()

        result = os.popen('linode-cli domains records-create \
        --protocol=tcp \
        --type=SRV \
        --port=23 \
        --priority=4 \
        --service=telnet \
        --target=8.8.8.8 \
        --weight=4 \
        --text \
        --no-header \
        --delimiter="," \
        ' + domain_id_arr[0]).read()

        assert(re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", result),
                "Output does not match the format")

    def test_list_srv_record(self):
        domain_ids = os.popen('linode-cli domains list --format="id" --text --no-header').read()

        domain_id_arr = domain_ids.splitlines()

        result = os.popen('linode-cli domains records-list ' + domain_id_arr[0] + ' \
        --text \
        --no-header \
        --delimiter=","').read()

        assert(re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", result),
                "Output does not match the format")

    def test_view_domain_record(self):
        domain_ids = os.popen('linode-cli domains list --format="id" --text --no-header').read()
        domain_id_arr = domain_ids.splitlines()

        record_ids = os.popen('linode-cli domains records-list ' + domain_id_arr[0] +' --text --no-header --format="id"').read()
        record_id_arr = record_ids.splitlines()

        result = os.popen('linode-cli domains records-view '+domain_id_arr[0] + ' ' + record_id_arr[0] + ' \
        --target="8.8.4.4" \
        --text \
        --no-header \
        --delimiter=","').read()

        assert (re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", result),
                "Output does not match the format")


    def test_update_domain_record(self):
        domain_ids = os.popen('linode-cli domains list --format="id" --text --no-header').read()
        domain_id_arr = domain_ids.splitlines()

        record_ids = os.popen('linode-cli domains records-list ' + domain_id_arr[0] +' --text --no-header --format="id"').read()
        record_id_arr = record_ids.splitlines()

        result = os.popen('linode-cli domains records-update '+domain_id_arr[0] + ' ' + record_id_arr[0] + ' \
        --target="8.8.4.4" \
        --text \
        --no-header \
        --delimiter=","').read()

        assert (re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", result),
                "Output does not match the format")

    def test_delete_a_domain_record(self):
        domain_ids = os.popen('linode-cli domains list --format="id" --text --no-header').read()
        domain_id_arr = domain_ids.splitlines()

        record_ids = os.popen('linode-cli domains records-list ' + domain_id_arr[0] +' --text --no-header --format="id"').read()
        record_id_arr = record_ids.splitlines()

        result = os.system('linode-cli domains records-delete '+domain_id_arr[0] + ' ' + record_id_arr[0])

        # Assert on status code returned from deleting domain
        assert(result == SUCCESS_STATUS_CODE)

    def test_delete_all_domains(self):
        domain_ids = os.popen('linode-cli --text --no-headers domains list --format "id,tags"').read()
        domain_id_arr = domain_ids.splitlines()

        for id in domain_id_arr:
            result = os.system('linode-cli domains delete ' + id)
            assert(result == SUCCESS_STATUS_CODE)
