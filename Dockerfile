FROM python:2.7-alpine

RUN pip install --upgrade pip

RUN apk add --no-cache tini

RUN adduser -D python
RUN mkdir /home/python/app/ && chown -R python:python /home/python/app
WORKDIR /home/python/app

ENTRYPOINT ["/sbin/tini", "--"]

USER python

RUN pip install --user requests

COPY --chown=python:python . .

CMD ["python", "-u", "main.py", "--config", "settings.config"]