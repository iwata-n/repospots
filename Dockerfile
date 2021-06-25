FROM python:3.9.5-alpine3.13

ADD requirements.txt .
ADD repospots.py .
RUN pip install -r requirements.txt