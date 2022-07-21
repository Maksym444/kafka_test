FROM python:3.8

RUN apt update

RUN mkdir /app
WORKDIR /app

COPY ./src ./src
COPY ./log ./log
COPY ./Pipfile ./Pipfile
#COPY ./Pipfile.lock ./Pipfile.lock

RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
RUN pipenv lock
RUN pipenv install --system --deploy --ignore-pipfile

WORKDIR /app/src
CMD ["bash"]