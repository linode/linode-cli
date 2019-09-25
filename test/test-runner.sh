#!/usr/bin/env bash

# Trap ctrl-c and reset .env file
trap ctrl_c INT

function ctrl_c() {
    source "$PWD/.env"

    unset LINODE_CLI_TOKEN

    if [ -f ".tmp-tag" ]; then
        rm .tmp-*
    fi

    echo -e "export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=NONE\nexport TOKEN_2_IN_USE_BY=NONE\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT" > ./.env
}

if ( ! (command -v parallel > /dev/null) ); then
    echo "The Linode-CLI requires GNU Parallel to be installed and added to your PATH"
    echo "For information on how to install, visit https://www.gnu.org/software/parallel/"
    exit 1
fi

if [[ $1 != "--allow-delete-resources" && $1 != "--force" && $1 != "-f" ]]; then
    echo -e "\n ####WARNING!#### \n"
    echo -e  "Running the Linode CLI tests requires removing all resources on your account\n"
    echo -e "Run this command with the --allow-delete-resources flag to accept this fate\n"
    exit 1
fi

if [ "$1" = "--allow-delete-resources" ]; then
    echo -e "\n\n"
    read -p "WARNING: Running the Linode CLI tests will REMOVE ALL account data. Are you sure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    	echo "Phew, that was a close one!"
        exit 0
    fi
fi

# Change current directory to test if called from base
if ( ! (echo "$PWD" | grep "test" > /dev/null ) ); then
    cd "$PWD/test" || exit
fi

# If .env file does not exist, attempt to generate one from global env vars
# Only relevant when running via docker
if [[  $DOCKER_BATS = "TRUE" ]]; then
    echo -e "[DEFAULT]\ntoken = ${TOKEN_1}\ndefault-user = test-user\n\n[test-user]" > /apps/.linode-cli \
        && echo -e "export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=NONE\nexport TOKEN_2_IN_USE_BY=NONE\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT" > /src/linode-cli/test/.env
fi

find . -name "*.bats" -not \( -path './test_helper*' \) | parallel --will-cite --jobs 2 bats
