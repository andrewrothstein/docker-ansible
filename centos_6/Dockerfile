FROM centos:6
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y \
 && yum groupinstall -y "development tools" \
 && yum install -y \
  zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel \
  tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel wget \
 && cd ~ \
 && wget http://python.org/ftp/python/2.7.9/Python-2.7.9.tar.xz \
 && tar xf Python-2.7.9.tar.xz \
 && cd ~/Python-2.7.9 \
 && ./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" \
 && make \
 && make altinstall \
 && cd ~ && rm -rf ~/Python-2.7.9 \
 && wget https://bootstrap.pypa.io/get-pip.py -O /usr/local/bin/get-pip.py \
 && python2.7 /usr/local/bin/get-pip.py \
 && pip2.7 install rpm dnf urllib3 ansible==2.5.4.0 \
 && yum clean all

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
