#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'

@test "it should list available kernels" {
    kernelIdsDisplay() {
        local kernelsList=$(linode-cli kernels list --text --no-headers --format "id")
        local kernel

        for kernel in $kernelsList ; do
            run bash -c "echo $kernel | egrep 'linode'"
            [ "$status" -eq 0 ]
        done
    }

    kernelIdsDisplay
}

@test "it should display id,label,version,kvm,xen,architecture,pvops fields" {
    kernelFieldsReturned() {
        local kernelsList=$(linode-cli kernels list --text --no-headers --delimiter "," --format "id,version,kvm,xen,architecture,pvops")
        local kernelWithFields

        for kernelWithFields in $kernelsList ; do
            run bash -c "echo $kernelWithFields | egrep 'linode/.*,.*,(False|True),(False|True),(i386|x86_64),(False|True)'"
            [ "$status" -eq 0 ]
        done
    }

    kernelFieldsReturned
}

@test "it should view a kernel" {
    kernelsAvailable=$(linode-cli kernels list --text --no-headers --format "id")
    set -- $kernelsAvailable
    kernelId=$1

    run linode-cli kernels view $kernelId \
        --format "id,version,kvm,xen,architecture,pvops" \
        --text \
        --delimiter ","

    assert_success
    assert_output --partial "id,version,kvm,xen,architecture,pvops"
    assert_output --regexp "linode/.*,.*,(False|True),(False|True),(i386|x86_64),(False|True)"
}
