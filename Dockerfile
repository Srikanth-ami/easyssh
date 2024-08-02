
FROM python:latest
WORKDIR /app
#COPY .requirements.txt /app
#COPY ./requirements.txt /app/requirements.txt
COPY requirements.txt requirements.txt
COPY . /app
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 6000
CMD ["python", "app.py"]

