variable "OS" {}
variable "OS_VER" {}
variable "SHA" {}

target "default" {
  context = "."
  dockerfile-inline = <<-EOF
  FROM docker.io/library/${OS}:${OS_VER}
  ENV WDIR=/docker-ansible${SHA}
  RUN mkdir -p $WDIR
  WORKDIR $WDIR
  ADD . $WDIR
  RUN sh -c "install.sh ${OS} ${OS_VER}"
  EOF

  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
  ]
  tags = [
    "docker.io/andrewrothstein/docker-ansible:0.0.0+${OS}.${OS_VER}",
    "quay.io/andrewrothstein/docker-ansible:0.0.0+${OS}.${OS_VER}",
    "ghcr.io/andrewrothstein/docker-ansible:0.0.0+${OS}.${OS_VER}"
  ]
}
