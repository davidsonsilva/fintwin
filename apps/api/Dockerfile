FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.interfaces.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
