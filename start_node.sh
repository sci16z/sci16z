#!/bin/bash
source .venv/bin/activate
export NODE_ENV=production
# export POOL_URL=${POOL_URL}
python sci16z/node/src/main.py 