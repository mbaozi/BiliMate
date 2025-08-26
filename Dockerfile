# 使用官方 Python 3.11.9 slim 镜像
FROM python:3.11.9-slim

ENV PYTHONPATH=/app
WORKDIR /app

COPY requirements-a.txt requirements-b.txt /app/
RUN pip install --no-cache-dir -r requirements-a.txt
RUN pip install --no-cache-dir -r requirements-b.txt

CMD ["python", "./BiliMate/app.py"]