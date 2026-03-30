#!/bin/bash
echo "Starting PDF service on port: ${PORT:-3040}"

exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-3040} --workers 1
