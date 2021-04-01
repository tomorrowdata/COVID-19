FROM python:3.9.2-buster

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /RTAutomation
WORKDIR /RTAutomation

COPY ./manager.py /RTAutomation/manager.py
COPY ./settings.py /RTAutomation/settings.py
COPY ./entrypoint.sh /RTAutomation/entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]