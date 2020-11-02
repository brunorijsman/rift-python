#!/bin/bash

TRUE=1
FALSE=0

VERBOSE=$FALSE

report () {
    message=$1
    echo >&2 "$message"
}

report_no_newline () {
    message=$1
    echo -n >&2 "$message"
}

fatal () {
    exit 1
}

parse_command_line_arguments () {
    while [[ $# -gt 0 ]]; do
        key=$1
        case $key in
            -v|--verbose)
                VERBOSE=$TRUE
                shift
                ;;
            *)
                report "Unexpected command line argument $key"
                fatal
                ;;
        esac
    done
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
    if [ "$release" != "16.04" ] && [ "$release" != "18.04" ] && [ "$release" != "20.04" ]; then
        report "It appears that you are running an unsupported version of Ubuntu"
        report "lsb_release reports $release"
        report "The installation script currently only supports Ubuntu 16.04, 18.04, or 20.04"
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

check_can_run_sudo () {
    if [ $(sudo echo hello) != hello ]; then
    report "It appears that you cannot run sudo from a script"
    report "The ability to run sudo from the installation script is required"
        fatal
    fi
}

run_cmd () {
    cmd=$1
    msg=$2
    if [ $VERBOSE == $TRUE ]; then
        report "***** $msg *****"
        report "$cmd"
        if ! command $cmd; then
            report "FAILED"
            report "\"$cmd\" returned non-zero status code"
            fatal
        fi
        report "OK"
    else
        report_no_newline "${msg}... "
        if ! command $cmd >/dev/null 2>&1; then
            report "FAILED"
            report "\"$cmd\" returned non-zero status code"
            fatal
        fi
        report "OK"
    fi
}
    
apt_get_install () {
    package=$1
    run_cmd "sudo apt-get install -y $package" "Installing $package"
}

create_and_activate_virtual_env () {
    run_cmd "sudo apt-get update" "Updating apt-get"
    apt_get_install "build-essential"
    apt_get_install "python3-dev"
    apt_get_install "python3-venv"
    apt_get_install "traceroute"
    run_cmd "python3 -m venv env" "Creating virtual environment"
    run_cmd "source env/bin/activate" "Activating virtual environment"
}

pip_install_dependencies () {
    check_command_present pip
    case $(python --version) in
        Python\ 3\.[567]\.?)
            run_cmd "pip install -r requirements-3-567.txt" "Installing Python module dependencies"
            ;;
        Python\ 3\.8\.?)
            run_cmd "pip install -r requirements-3-8.txt" "Installing Python module dependencies"
            ;;
        *)
            report "Unsupported version of Python"
            fatal
            ;;
    esac


}

parse_command_line_arguments $@
check_supported_os
check_git_directory
check_can_run_sudo
create_and_activate_virtual_env
pip_install_dependencies

