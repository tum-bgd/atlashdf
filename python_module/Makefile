all: clean jq build

jq:
	autoreconf -fi jq
	cd jq && ./configure --disable-maintainer-mode
	make -C jq

build: clean
	sudo python3 setup.py develop

wheel: clean
	sudo python3 setup.py bdist_wheel

install:
	pip install dist/*.whl --force-reinstall

clean:
	sudo rm -rf atlashdf* build dist
