all: setup data build

setup:
	sudo apt-get update
	sudo apt-get install pkg-config libhdf5-dev libboost-dev libosmpbf-dev -y

data:
	mkdir -p data
	curl -C - -o "./data/berlin-latest.osm.pbf" "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf"

build:
	make -C atlashdf build

python:
	make -C python_module jq
	make -C python_module wheel
	make -C python_module install

viewer:
	make -C viewer

docker:
	docker build -t atlashdf .

run:
	docker run -it -p 8888:8888 atlashdf

clean:
	rm -f *.o atlashdf viewer
	make -C atlashdf clean
	make -C python_module clean
