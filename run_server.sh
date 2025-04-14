#!/bin/bash
echo "Starting FastAPI Server..."
uvicorn main:app --reload --host 127.0.0.1 --port 8000
