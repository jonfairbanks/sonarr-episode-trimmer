FROM python:2.7-alpine

RUN pip install --upgrade pip

RUN adduser -D python
RUN mkdir /home/python/app/ && chown -R python:python /home/python/app
WORKDIR /home/python/app

USER python

RUN pip install --user requests flask

COPY --chown=python:python . .

EXPOSE 5000
ENTRYPOINT ["python", "-u", "main.py"]
CMD ["--config", "settings.config"]