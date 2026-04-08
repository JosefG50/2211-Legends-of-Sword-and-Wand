FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py logic.py database.py ./

EXPOSE 5001

ENV MONGO_URI="mongodb://mongo:27017/"

CMD ["python", "app.py"]
