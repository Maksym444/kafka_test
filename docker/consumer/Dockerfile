FROM python:3.9

RUN apt update

RUN mkdir /app
WORKDIR /app

COPY ./src ./src
RUN mkdir ./log
COPY ./entrypoint.sh /entrypoint.sh
COPY ./Pipfile ./Pipfile
#COPY ./Pipfile.lock ./Pipfile.lock

RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
RUN pipenv lock
RUN pipenv install --system --deploy --ignore-pipfile

WORKDIR /app/src

ENTRYPOINT ["/entrypoint.sh"]
#CMD ["bash"]