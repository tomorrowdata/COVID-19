FROM python:3.9.2-buster

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /RTAutomation
WORKDIR /RTAutomation

COPY ./run_manager.py /RTAutomation/run_manager.py
COPY ./entrypoint.sh /RTAutomation/entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]