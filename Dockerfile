FROM python:3

RUN pip install pipenv amcrest pytz
WORKDIR /app

COPY zm-amcrest-trigger.py .

CMD [ "python", "-u", "zm-amcrest-trigger.py" ]
