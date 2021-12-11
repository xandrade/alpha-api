#!/bin/bash

docker stop api-tcp5000 && docker rm api-tcp5000
cd /root
rm alpha-api -r
git clone https://github.com/xandrade/alpha-api.git
cd alpha-api
docker build -t api .
docker run --name api-tcp5000 --restart unless-stopped -e PORT=5000 -e HOST="0.0.0.0" -p 5000:5000 -v "/root/db":"/usr/src/api/db" -d api 
docker log api-tcp5000
 