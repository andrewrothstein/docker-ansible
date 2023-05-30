variable "OS" {}
variable "OS_VER" {}

target "both" {
  context = "."
  dockerfile = "Dockerfile"
  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
  tags = [
    "docker.io/andrewrothstein/docker-ansible:${OS}_${OS_VER}",
    "quay.io/andrewrothstein/docker-ansible:${OS}_${OS_VER}",
    "ghcr.io/andrewrothstein/docker-ansible:${OS}_${OS_VER}"
  ]
}

target "only" {
  inherits = [
    "both"
  ]
  platforms = [
    "linux/amd64"
  ]
}
