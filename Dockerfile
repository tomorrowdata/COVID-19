FROM tensorflow/tensorflow:latest-py3-jupyter

RUN apt-get update && \
    apt-get install -y git

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

EXPOSE 8888

RUN useradd -ms /bin/bash jupuser

USER jupuser

