# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

ENV REDIS_ENDPOINT=127.0.0.1
ENV REDIS_PORT=6379
ENV REDIS_DB=0

ENV SCHEDULER_TIMES=30

WORKDIR /scheduler

COPY setup_beat.py .

COPY functions /scheduler/functions

COPY run_beat.py .

COPY packages.txt .

RUN pip3 install -r packages.txt

CMD ["python", "run_beat.py"]