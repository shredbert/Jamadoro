#!/usr/bin/env bash

ROOT_DOMAIN=localhost:5000

curl --request POST \
	--cookie api-tests/api-cookie.txt \
	--form "duration-secs=3000" \
	--include \
	--location \
	"$ROOT_DOMAIN"/add-pomodoro
