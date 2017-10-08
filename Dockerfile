FROM ubuntu:14.10

RUN apt-get update && apt-get install -y build-essential unzip curl python-pip python-dev python-matplotlib python-lxml \
	python-numpy python-dateutil python-gdal python-yaml python-serial python-xlwt python-shapely python-pil python-gdal \
	python-reportlab python-reportlab-accel python-tweepy python-xlrd python-pyth python-boto ansible 

RUN pip install selenium\>=2.23.0 sunburnt\>=0.6 TwitterSearch\>=1.0 requests\>=2.3.0

RUN curl -o web2py.zip https://codeload.github.com/web2py/web2py/zip/R-2.9.11 && unzip web2py.zip && mv web2py-R-2.9.11 /home/web2py && rm web2py.zip

ADD . /home/web2py/applications/eden

RUN cp /home/web2py/applications/eden/private/templates/000_config.py /home/web2py/applications/eden/models/000_config.py && sed -i 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' /home/web2py/applications/eden/models/000_config.py

CMD python /home/web2py/web2py.py -i 0.0.0.0 -p 8000 -a eden 
