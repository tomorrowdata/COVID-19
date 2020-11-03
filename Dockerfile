FROM tensorflow/tensorflow:latest-py3-jupyter

RUN python3 -m pip install pandas scipy scikit-learn geopandas descartes

RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/njchiang/tikhonov.git && \
    cd tikhonov && \
    python3 setup.py install

EXPOSE 8888

RUN useradd -ms /bin/bash jupuser

USER jupuser

