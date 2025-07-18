#!/bin/bash

# Usage: ./build.sh yourname/repo:tag
# e.g. ./build.sh h4x3rotab/nanda-demo:latest

docker build --platform linux/amd64 -t "${1}" .
docker push "${1}"
