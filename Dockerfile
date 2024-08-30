FROM python:3.12.2

WORKDIR /code

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

RUN pip uninstall --yes werkzeug
RUN pip install -v https://github.com/pallets/werkzeug/archive/refs/tags/2.0.3.tar.gz

CMD ["python","OSRS_CDF_App.py"]