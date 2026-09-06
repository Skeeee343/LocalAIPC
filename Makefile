check:
	ansible-playbook -i ansible/inventory.ini -c local ansible/site.yml --check --diff
	curl -s localhost:11434/api/tags; echo
	curl -sf localhost:8787/healthz; echo
	curl -sf localhost:3000/health; echo
	nvidia-smi -L

apply:
	ansible-playbook -i ansible/inventory.ini -c local ansible/site.yml
