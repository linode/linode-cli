#!/bin/bash

read -p "WARNING: Running the Linode CLI tests will REMOVE ALL account data. Are you sure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
	echo "Phew, that was a close one!"
    exit 1
fi

bats linodes
