FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]