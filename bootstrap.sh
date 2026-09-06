#!/bin/sh
# One-time shim. Everything else lives in ansible/site.yml.
set -eu
sudo apt update && sudo apt install -y ansible git
[ -d /opt/localaipc/.git ] || sudo git clone https://github.com/Skeeee343/LocalAIPC.git /opt/localaipc
ansible-playbook -i /opt/localaipc/ansible/inventory.ini -c local /opt/localaipc/ansible/site.yml
