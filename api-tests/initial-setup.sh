#!/usr/bin/env bash

ROOT_DOMAIN=localhost:5000
EMAIL=test@email.com
USERNAME=bert
PASSWORD=jammer_pw

# # Register account
# curl --request post \
# 	--form "email="$CREDENTIAL"" \
# 	--form "password="$CREDENTIAL"" \
# 	--form "re-password="$CREDENTIAL"" \
# 	--form "username="$CREDENTIAL"" \
# 	--include \
# 	--location \
# 	"$ROOT_DOMAIN"/register

# Log in to account & get cookie
curl --request POST \
	--form "email="$EMAIL"" \
	--form "password="$PASSWORD"" \
	--include \
	--location \
	--cookie-jar ./api-tests/api-cookie.txt \
	"$ROOT_DOMAIN"/login

# Test home page loads
curl --location \
	--include \
	--cookie ./api-tests/api-cookie.txt \
	"$ROOT_DOMAIN"/
