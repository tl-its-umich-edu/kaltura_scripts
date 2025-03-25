# Use a Python base image
FROM python:3.13-slim

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app/
COPY . /app/

# Set the local time zone of the Docker image
ENV TZ=America/Detroit
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["python", "/app/kaltura_admin.py", "/app/env.json"]

# Done!