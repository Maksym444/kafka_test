FROM python:3.9

RUN apt update

RUN mkdir /app
RUN mkdir -p /app/src/static/media
WORKDIR /app


COPY ./src ./src
RUN mkdir ./log
COPY ./Pipfile ./Pipfile
COPY ./Pipfile.lock ./Pipfile.lock

RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
#RUN pipenv lock
RUN pipenv install --system --deploy --ignore-pipfile

WORKDIR /app/src
CMD ["bash"]