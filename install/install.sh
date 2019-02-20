#!/bin/bash

fatal_error () {
    local message=$1
    echo >&2 "$message"
    exit 1
}

check_command_present() {
    local command_name=$1
    command -v $command_name >/dev/null 2>&1 || \
        fatal_error "Command $command_name is needed but not present on this system"
}

check_supported_os() {
    check_command_present "uname"
    uname_out=$(uname)
    if [ "$uname_out" != "Linux" ]; then
        fatal_error "Not running on Linux; only Linux is supported (uname reports $uname_out)"
    fi
    check_command_present "lsb_release"
    distributor_id=$(lsb_release -is)
    if [ "$distributor_id" != "Ubuntu" ]; then
        fatal_error "Not running on Ubuntu; only Ubuntu is supported (lsb_release reports $distributor_id)"
    fi
    release=$(lsb_release -rs)
    if [ "$release" != "18.04" ]; then
        fatal_error "Not running on Ubuntu 18.04; only Ubuntu 18.04 is supported (lsb_release reports $release)"
    fi
    fatal_error "OK"
}

check_supported_os
