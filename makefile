check:
	bash check.sh

clean:
	rm -rf *.egg-info

deploy:
	python setup.py sdist
	python setup.py sdist upload
	make clean

install:
	bash install.sh

run:
	source activate.sh && \
		python run.py
