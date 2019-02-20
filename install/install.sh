#!/bin/bash

report () {
    message=$1
    echo >&2 "$message"
}

fatal () {
    exit 1
}

check_command_present() {
    local command_name=$1
    if ! command -v $command_name >/dev/null 2>&1; then
        report "Command $command_name is needed but not present on this system"
        fatal
    fi
}

check_supported_os() {
    # Only allow an operating system version that was actually tested
    check_command_present "uname"
    uname_out=$(uname)
    if [ "$uname_out" != "Linux" ]; then
        report "It appears that you are not running on Linux: uname reports $uname_out"
        report "The installation script currently only supports Linux"
        fatal
    fi
    check_command_present "lsb_release"
    distributor_id=$(lsb_release -is)
    if [ "$distributor_id" != "Ubuntu" ]; then
        report "It appears that you are not running a different distribution of Linux than Ubuntu"
        report "lsb_release reports $distributor_id"
        report "The installation script currently only supports Ubuntu"
        fatal
    fi
    release=$(lsb_release -rs)
    if [ "$release" != "18.04" ]; then
        report "It appears that you are running a different version of Ubuntu than 18.04"
        report "lsb_release reports $release"
        report "The installation script currently only supports Ubuntu 18.04"
        fatal
    fi
}

check_git_directory () {
    if [ ! -d ".git" ]; then
        report "It appears that the current directory is not the root directory of the git repository"
        report "I don't see a .git subdirectory"
        report "You must run the installation script from the root directory of the git repository"
        fatal
    fi
    if [ ! -d "rift" ]; then
        report "It appears that this git repository is not a clone of the rift-python repository"
            report "I don't see a rift subdirectory"
        report "You must run the installation script from the root directory of the cloned rift-python git repository"
        fatal
    fi
}

create_virtual_env () {
    cmd="sudo apt-get update"
    if ! command $cmd; then
        report "Coult update apt-get"
        report "\"$cmd\" returned non-zero status code"
        fatal
    fi
    cmd="sudo apt-get install virtualenv"
    if ! command $cmd; then
        report "Coult not install virtualenv"
        report "\"$cmd\" returned non-zero status code"
        fatal
    fi
}

check_supported_os
check_git_directory
create_virtual_env
