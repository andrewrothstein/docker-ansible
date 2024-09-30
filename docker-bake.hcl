variable "UPSTREAM_REGISTRY" {
  default = "docker.io"
}

variable "UPSTREAM_ORG" {
  default = "library"
}

variable "OS" {}
variable "OS_VER" {}
variable "SHA" {}

variable "UPSTREAM_OS" {
  default = "${OS}"
}

variable "UPSTREAM_OS_VER" {
  default = "${OS_VER}"
}

variable "UPSTREAM_IMAGE" {
  default = "${UPSTREAM_REGISTRY}/${UPSTREAM_ORG}/${UPSTREAM_OS}:${UPSTREAM_OS_VER}"
}

variable "TARGET_OS" {
  default = "${OS}"
}

variable "TARGET_OS_VER" {
  default = "${OS_VER}"
}

variable "TARGET_IMAGE_SEMVER" {
  default = "0.0.0"
}

variable "TARGET_IMAGE" {
  default = "docker-ansible:${TARGET_IMAGE_SEMVER}-${TARGET_OS}.${TARGET_OS_VER}"
}

target "default" {
  context = "."
  dockerfile-inline = <<-EOF

  FROM ${UPSTREAM_IMAGE}
  COPY profile.d/* /etc/profile.d
  ENV WDIR=/docker-ansible${SHA}
  RUN mkdir -p $WDIR
  WORKDIR $WDIR
  ADD . $WDIR
  SHELL ["/bin/sh", "-lc"]
  RUN set -ex; ansible_install ${TARGET_OS} ${TARGET_OS_VER}; rm -rf .git/
  EOF

  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
  ]
  tags = [
    "docker.io/andrewrothstein/${TARGET_IMAGE}",
    "ghcr.io/andrewrothstein/${TARGET_IMAGE}",
  ]
}
