#!/bin/bash
cd "$(dirname "$0")"
source venv/Scripts/activate
uvicorn app.main:app --port 8002 --reload
