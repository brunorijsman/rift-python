#! /bin/bash

check_log_file () {
    log_file=$1
    if [[ -e $log_file ]]; then
        echo
        echo "##### Errors in $log_file ####"
        echo
        if ! grep "Did not find expected pattern" $log_file --color -B 50 -A 20; then
            tail -1000 $log_file
        fi
    fi
}

check_log_file rift_expect.log
check_log_file rift_telnet_expect.log
check_log_file test_telnet_expect

exit 0
