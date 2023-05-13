FROM python:3.9-alpine

RUN adduser -D python
RUN mkdir /home/python/app/ && chown -R python:python /home/python/app
WORKDIR /home/python/app

USER python

RUN pip install --user requests flask

COPY --chown=python:python . .

EXPOSE 5000
ENTRYPOINT ["python", "-u", "index.py"]
CMD ["--config", "settings.config"]