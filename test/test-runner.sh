#!/usr/bin/env bash

# Trap ctrl-c and reset .env file
trap ctrl_c INT

# Run all tests in parallel
num_parallel_jobs=2

if [[ $* =~ "--no-parallel" ]]; then
  num_parallel_jobs=1
fi

function clean_accounts() {
    grep "export TOKEN_[0-9]=" < "$PWD/.env" | cut -d '=' -f 2 | parallel --will-cite --jobs $num_parallel_jobs "$PWD/clean-accounts.sh"
}

function ctrl_c() {
    source "$PWD/.env"

    unset LINODE_CLI_TOKEN

    if [ -f ".tmp-tag" ]; then
        rm .tmp-*
    fi

    echo -e "export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=NONE\nexport TOKEN_2_IN_USE_BY=NONE\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT" > ./.env
}

function rebuild_env() {
  unset LINODE_CLI_TOKEN

  if [ -f ".tmp-tag" ]; then
        rm .tmp-*
    fi

  echo -e "export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=NONE\nexport TOKEN_2_IN_USE_BY=NONE\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT" > ./.env
}

if ( ! (command -v netcat > /dev/null) ); then
    echo "The Linode-CLI requires netcat to be installed and added to your PATH"
    exit 1
fi

if ( ! (command -v parallel > /dev/null) ); then
    echo "The Linode-CLI requires GNU Parallel to be installed and added to your PATH"
    echo "For information on how to install, visit https://www.gnu.org/software/parallel/"
    exit 1
fi

if [[ $* != *"--allow-delete-resources"* && $* != *"--force"* && $* != *"-f"* ]]; then
    echo -e "\n ####WARNING!#### \n"
    echo -e  "Running the Linode CLI tests requires removing all resources not tagged \"linuke-keep\" on your account\n"
    echo -e "If you have resources tagged \"linuke-keep\" on your Linode account, certain tests may not pass."
    echo -e "Run this command with the --allow-delete-resources flag to accept this fate\n"
    exit 1
fi

if [[ $* =~ "--allow-delete-resources" ]]; then
    echo -e "\n\n"
    read -p "WARNING: Running the Linode CLI tests will REMOVE ALL RESOURCES not tagged with \"linuke-keep\" on your account. Are you sure? (y/n) " -n 1 -r
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
    echo -e "[DEFAULT]\ntoken = ${TOKEN_1}\ndefault-user = test-user\n\n[test-user]" > /root/.linode-cli \
        && echo -e "export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=NONE\nexport TOKEN_2_IN_USE_BY=NONE\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT" > /src/linode-cli/test/.env
fi

if [[ $* =~ "--from-env" ]]; then
 rebuild_env
fi

if [[ $* =~ "--clean" ]]; then
 clean_accounts
 ctrl_c
 exit 0
fi

# Always clean accounts before tests:
clean_accounts

find . -name "*.bats" -not \( -path './test_helper*' \) | parallel --will-cite --jobs $num_parallel_jobs bats

# Preserve tests exit code:
tests_status=$?

clean_accounts
exit $tests_status
