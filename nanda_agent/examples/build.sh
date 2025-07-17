#!/bin/bash
docker build --platform linux/amd64 -t h4x3rotab/nanda-demo:latest .
docker push h4x3rotab/nanda-demo:latest