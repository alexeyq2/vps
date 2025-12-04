#!/bin/bash

./down.sh
sudo rm -rf srv/certbot/*
./up.sh
