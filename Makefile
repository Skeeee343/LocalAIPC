# Remote management from Mac (default). Fill ansible/inventory.ini [server]
# + ansible/secrets.yml (admin_ssh_key), then:
export ANSIBLE_CONFIG=ansible/ansible.cfg

check:
	ansible-playbook -i ansible/inventory.ini --limit server ansible/site.yml --check --diff
	ansible server -i ansible/inventory.ini -m shell -a 'curl -s localhost:11434/api/tags; echo; curl -sf localhost:8787/healthz; echo; nvidia-smi -L'
	curl -sf localhost:3000/health; echo # adapter runs on this Mac, not the server

apply:
	ansible-playbook -i ansible/inventory.ini --limit server ansible/site.yml

# On-box fallback (first install already ran bootstrap.sh; debug only).
check-local:
	ansible-playbook -i ansible/inventory.ini --limit local -c local ansible/site.yml --check --diff

apply-local:
	ansible-playbook -i ansible/inventory.ini --limit local -c local ansible/site.yml
