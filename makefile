check:
	bash check.sh

clean:
	rm -rf *.egg-info

deploy:
	python setup.py sdist
	python setup.py sdist upload
	make clean

install:
	bash activate.sh && \
		python setup.py install

run:
	bash activate.sh && \
		python run.py
