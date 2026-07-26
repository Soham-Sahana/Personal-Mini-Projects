FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /code

COPY ./pyproject.toml ./README.md ./uv.lock* ./
COPY ./expense_agent ./expense_agent
COPY ./server.py ./

RUN uv sync --frozen

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "server:fastapi_app", "--host", "0.0.0.0", "--port", "8080"]
