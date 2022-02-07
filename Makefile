.ONESHELL:
.PHONY: prepare run clean services

prepare:
	poetry install

run:
	poetry run python -m thorlabs_ell9k_ctrl.server.app

clean:
	rm -r .venv poetry.lock


services: services/thorlabs_ell9k_ctrl.service
	echo "> Creating links to services in /etc/systemd/system/"
	sudo ln -s `pwd`/services/*.service /etc/systemd/system/
	sudo systemctl daemon-reload

	echo "> Enabling services and starting server"
	sudo systemctl enable thorlabs_ell9k_ctrl.service
	sudo systemctl start thorlabs_ell9k_ctrl.service


services/thorlabs_ell9k_ctrl.service:
	echo "> Creating services..."
	mkdir -p services
	cat <<EOF > $@
	[Unit]
	Description=Server for controlling the Thorlabs ELL9K filter slider
	After=network.target
	
	[Service]
	User=$$USER
	WorkingDirectory=$$(pwd)
	ExecStart=$$(pwd)/.venv/bin/python -m ELL9K.main
	Restart=always
	RestartSec=10
	
	[Install]
	WantedBy=multi-user.target
	EOF
