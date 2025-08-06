#!/bin/bash
cd /Users/vinhsmac/vp-chatbot/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
