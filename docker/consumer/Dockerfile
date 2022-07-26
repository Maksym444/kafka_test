FROM python:3.9

ARG PIPENV_INSTALL_ARG
#ENV PIPENV_INSTALL_ARG $PIPENV_INSTALL_ARG

RUN apt update
RUN echo ${PIPENV_INSTALL_ARG}

RUN mkdir /app
WORKDIR /app

COPY ./src ./src
RUN mkdir ./log
COPY ./entrypoint.sh /entrypoint.sh
COPY ./Pipfile ./Pipfile
COPY ./Pipfile.lock ./Pipfile.lock

RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
# RUN pipenv lock
RUN pipenv install --system --deploy --ignore-pipfile ${PIPENV_INSTALL_ARG}

WORKDIR /app/src

ENTRYPOINT ["/entrypoint.sh"]
#CMD ["bash"]