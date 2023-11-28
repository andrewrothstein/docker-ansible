# useful package manager functions
_pacman_install() {
    pacman \
        -Syu \
        --noconfirm \
        $@
}

_pacman_clean() {
    pacman -Sc
}

_dnf_install() {
    dnf install -y $@
}

_dnf_up() {
    dnf update -y
}

_dnf_clean() {
    dnf clean all
}

_dnf_remove() {
    dnf remove -y $@
}

_apt() {
    DEBIAN_FRONTEND=noninteractive apt $@
}

_apt_install() {
    _apt install -y $@
}

_apt_remove() {
    _apt remove -y $@
}

_apt_up() {
    _apt update -y
    _apt upgrade -y
}

_apt_clean() {
    DEBIAN_FRONTEND=noninteractive apt-get clean -y
}

_apk_add () {
    apk add $@
}

_apk_del () {
    apk del $@
}

_apk_clean () {
    rm -rf /var/cache/apk/*
}

_apk_up () {
    apk update
    apk upgrade
}

_pip_install() {
    pip install -U $1 --user
}
_pip_install_pipx() {
    _pip_install pip
    _pip_install pipx
}

_install_dnf () {
    _dnf_up
    _dnf_install \
        python3 \
        python3-pip \
        systemd \
        wget \
        which
    _dnf_clean
    _pip_install_pipx
}

install_fedora () {
    _install_dnf
}

install_rockylinux () {
    _install_dnf
}

_install_archlinux () {
    _pacman_install \
        which \
        python \
        python-pipx
    _pacman_clean
}

_install_ubuntu () {
    _apt_up
    _apt_install \
        pipx \
        language-pack-en \
        wget
    _apt_clean
}

_install_debian () {
    os_ver=$1
    _apt_up
    _apt_install \
        wget
    if [ "${os_ver}" = "bullseye" ];
    then
        _apt_install \
            python3-pip \
            python3-venv
        _pip_install_pipx
    else
        _apt_install pipx
    fi
    _apt_clean
}

_install_apk () {
    _apk_up
    _apk_add \
        ca-certificates \
        python3 \
        py3-pip \
        py3-virtualenv \
        wget
    _apk_clean
    _pip_install_pipx
}

_install_alpine () {
    _install_apk
}

_write_local_cfg () {
    mkdir -p /etc/ansible
    cat >/etc/ansible/ansible.cfg <<HERE
[defaults]
inventory = /etc/ansible/inventories
transport = local
callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
HERE
}

_write_inventories () {
    mkdir -p /etc/ansible/inventories
    cat >/etc/ansible/inventories/localhost <<HERE
localhost
HERE
}

_ansible_ping_localhost () {
    ansible --version \
        && ansible all --list-hosts \
        && ansible localhost -m ping
}

ansible_install() {
    os=$1
    os_ver=$2
    _install_${os} $os_ver
    pipx ensurepath
    pipx install ansible --include-deps
    _write_local_cfg
    _write_inventories ${os}
    _ansible_ping_localhost
}
