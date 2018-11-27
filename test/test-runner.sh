#!/bin/bash

if [[ $1 = "--allow-delete-resources" ]]
then
    echo -e "\n\n"
    read -p "WARNING: Running the Linode CLI tests will REMOVE ALL account data. Are you sure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
    	echo "Phew, that was a close one!"
        exit 0
    fi

    testsWorkingDir=$(echo $PWD | grep test)

    if [[ $? != 0 ]]
    then
        cd $PWD/test
    fi

    bats $(ls */*.bats)
else
    echo -e "\n ####WARNING!#### \n"
    echo -e  "Running the Linode CLI tests requires removing all resources on your account\n"
    echo -e "Run this command with the --allow-delete-resources flag to accept this fate\n"
    exit 1
fi
