FROM python:3.8.0-alpine3.10
COPY requirements.txt publish.py /
RUN pip install -r requirements.txt
ENTRYPOINT ["/publish.py"]
