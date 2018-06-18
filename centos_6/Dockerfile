FROM centos:6
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y \
 && yum groupinstall -y "development tools" \
 && yum install -y \
  zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel \
  tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel \
 && yum install -y wget \
 && cd ~ \
 && wget http://python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz \
 && tar xf Python-3.6.3.tar.xz \
 && cd ~/Python-3.6.3 \
 && ./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" \
 && make \
 && make altinstall \
 && strip /usr/local/lib/libpython3.6m.so.1.0 \
 && cd ~ && rm -rf ~/Python-3.6.3 \
 && wget https://bootstrap.pypa.io/get-pip.py -O /usr/local/bin/get-pip.py \
 && python3.6 /usr/local/bin/get-pip.py \
 && pip install urllib3 ansible==2.5.4.0 \
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
