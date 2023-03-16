import logging
import pytest
from tests.integration.helpers import *

BASE_CMD = ["linode-cli", "lke"]


@pytest.fixture(scope="session", autouse=True)
def setup_test_clusters():
    yield "setup"
    # just clean up method required for this test suite
    try:
        remove_lke_clusters()
    except:
        logging.exception("Failed the remove lke cluster..")


def test_deploy_an_lke_cluster():
    lke_version = os.popen('linode-cli lke versions-list --text --no-headers | head -1').read().rstrip()

    result = exec_test_command(BASE_CMD+['cluster-create', '--region', 'us-east', '--label', 'cli-test-1', '--node_pools.type', 'g6-standard-1',
                                         '--node_pools.count', '1', '--node_pools.disks', '[{"type":"ext4","size":1024}]', '--k8s_version',
                                         lke_version, '--text', '--delimiter', ",", '--no-headers', '--format', 'label,region,k8s_version', '--no-defaults']).stdout.decode()

    assert('cli-test-1,us-east,'+lke_version in result)