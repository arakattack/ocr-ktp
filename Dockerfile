FROM python:3.12.4-slim-bullseye
WORKDIR /usr/src/app
COPY . .
RUN apt-get update
RUN apt install -y  tesseract-ocr tesseract-ocr-ind ffmpeg libsm6 libxext6
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# CMD [ "gunicorn", "api:app --workers 4 --threads 2 --worker-class gevent --keep-alive 5 --timeout 30 --worker-connections 1000" ]

EXPOSE 80
