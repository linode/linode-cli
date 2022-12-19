#!/usr/bin/env bats

# THESE TESTS HAVE BEEN DISABLED UNTIL A BUG IS ADDRESSED

# load '../test_helper/bats-support/load'
# load '../test_helper/bats-assert/load'
# load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

# @test "it should attach volume to a linode during volume creation" {
#     createLinode
    
#     linode_id=$(linode-cli linodes list --format="id" --text --no-headers)

#     until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
#         echo 'still provisioning'
#     done

#     linode_id=$(linode-cli linodes list --format="id" --text --no-headers)
#     run linode-cli volumes create --label="attachedVolume" --size=10 --linode_id=$linode_id --text --no-headers --delimiter="," --format="id,label,size,region,linode_id"
#     assert_success
#     assert_output --regexp "[0-9]+,attachedVolume,10,[a-z-]+,$linode_id"
# }

# @test "it should detach from linode" {
#     attached_volume_id=$(linode-cli volumes list --label="attachedVolume" --format="id" --text --no-headers)
#     run linode-cli volumes detach $attached_volume_id --text --no-headers
#     assert_success
#     run linode-cli volumes view $attached_volume_id --text --no-headers --delimiter="," --format="id,label,size,region,linode_id"
#     assert_success
#     assert_output --regexp "$attached_volume_id,attachedVolume,10,us-east,"
# }

# @test "it should attach to a linode" {
#     volume_id=$(linode-cli volumes list --format="id" --text --no-headers)
#     linode_id=$(linode-cli linodes list --format="id" --text --no-headers)
#     run linode-cli volumes attach --linode_id=$linode_id $volume_id --text --no-headers --delimiter="," --format="id,label,size,region,linode_id"
#     assert_success
#     assert_output --regexp "$volume_id,attachedVolume,10,[a-z-]+,$linode_id"
# }

# @test "it should fail to remove while attached" {
#     attached_volume=$(linode-cli volumes list --format="id" --text --no-headers)
#     run linode-cli volumes delete $attached_volume --text --no-headers
#     assert_failure
#     assert_output --partial "Request failed: 400"
#     assert_output --partial "This volume must be detached before it can be deleted."
# }

# @test "it should fail to attach to a linode that does not belong to the user" {
#     unattached_volume=$(linode-cli volumes create --label="unattachedVolume" --region="us-east" --size=10 --text --no-headers --format="id")
#     run linode-cli volumes attach --linode_id=1 $unattached_volume --text --no-headers
#     assert_failure
#     assert_output --partial "Request failed: 403"
#     assert_output --partial "linode_id	You do not have permission to access this Linode"
# }

# @test "it should remove all volumes" {
#     run shutdownLinodes
# 	run removeLinodes
# 	run removeVolumes
# }
