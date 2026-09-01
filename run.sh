#!/bin/bash

docker run -e GOODREADS_USER=<email> -e GOODREADS_PASSWORD=<passwrod>--init \
--rm -it -p 8080:8080 goodreads-scraper 