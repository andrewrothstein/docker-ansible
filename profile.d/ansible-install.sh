#!/bin/bash

# Install ansible using uv
_install_ansible() {
    uv tool install --python 3.13 ansible
}

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
localhost
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
    # Install ansible using uv
    _install_ansible

    # Configure ansible
    _write_local_cfg
    _write_inventories

    # Test the installation
    _ansible_ping_localhost
}
