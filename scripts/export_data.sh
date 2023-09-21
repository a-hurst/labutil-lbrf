#!/bin/bash

pipenv run klibs export

arg=0
for table in "$@"; do
    (( arg++ ))
    pipenv run klibs export -t $table
done
