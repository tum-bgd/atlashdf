build:
	sudo rm -Rf atlashdf* build
	sudo python3 setup.py develop

docker:
	docker build -f ../Dockerfile -t atlashdf ../.

run:
	docker run -it -p 8888:8888 atlashdf
