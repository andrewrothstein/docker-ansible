#!/bin/bash

# Configure ansible local settings
_write_local_cfg() {
    mkdir -p /etc/ansible
    cat >/etc/ansible/ansible.cfg <<HERE
[defaults]
inventory = /etc/ansible/inventories
transport = local
callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
HERE
}

# Setup ansible inventories
_write_inventories() {
    mkdir -p /etc/ansible/inventories
    cat >/etc/ansible/inventories/localhost <<HERE
localhost ansible_python_interpreter=${HOME}/.local/share/uv/tools/ansible-core/bin/python3
HERE
}

# Test ansible installation
_ansible_ping_localhost() {
    ansible --version \
        && ansible all --list-hosts \
        && ansible localhost -m ping
}

# Main installation function
ansible_install() {
    uv tool install ansible-core

    # Configure ansible
    _write_local_cfg
    _write_inventories

    # Test the installation
    _ansible_ping_localhost
}
