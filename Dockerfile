ARG OS
ARG OS_VER
FROM docker.io/library/${OS}:${OS_VER}
ARG OS
ARG OS_VER
LABEL maintainer="Andrew Rothstein andrew.rothstein@gmail.com"
ADD ansible-install-lib ansible-install-lib
ADD install.sh install.sh
ADD requirements.yml requirements.yml
RUN ./install.sh ${OS} ${OS_VER}
