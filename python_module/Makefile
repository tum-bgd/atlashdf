build:
	docker build -f Dockerfile -t atlashdf .



start_bash:
	docker run -it -v ${PWD}/data/:/atlashdf/data/ -p 8767:8888 atlashdf bash
	


#all:
#	sudo rm -Rf atlashdf* build
#	sudo python3 setup.py develop
