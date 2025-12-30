#!/bin/bash

: "${RUYISDK_API_HOST:?RUYISDK_API_HOST must be set}"
: "${RUYISDK_API_USERNAME:?RUYISDK_API_USERNAME must be set}"
: "${RUYISDK_API_PASSWORD:?RUYISDK_API_PASSWORD must be set}"

time_start="2024-04-10T00:00:00+08:00"
time_end="$(date -Iseconds)"

do_login() {
	curl "$RUYISDK_API_HOST"/oauth2/token \
		-s \
		-X POST \
		-H 'Content-Type: application/x-www-form-urlencoded' \
		--data-raw "grant_type=password&username=${RUYISDK_API_USERNAME}&password=${RUYISDK_API_PASSWORD}"
}

get_accesstoken() {
	do_login | jq -r '.access_token'
}

ACCESS_TOKEN="$(get_accesstoken)"

common_args=(
	-s
	-H 'Content-Type: application/json'
	-H "Authorization: Bearer $ACCESS_TOKEN"
)

curl "$RUYISDK_API_HOST"/admin/process-telemetry-v1 \
	"${common_args[@]}" \
	--data-raw "{\"time_start\":\"${time_start}\",\"time_end\":\"${time_end}\"}"

curl "$RUYISDK_API_HOST"/admin/refresh-github-stats-v1 \
	"${common_args[@]}" \
	--data-raw '{}'

curl "$RUYISDK_API_HOST"/admin/refresh-repo-news-v1 \
	"${common_args[@]}" \
	--data-raw '{}'

hour="$(date +%H)"
hour="${hour//0}"  # test(1) cannot handle 08 (seems treated as invalid octal)
if [[ $hour -eq 8 ]]; then
	curl "$RUYISDK_API_HOST"/admin/refresh-pypi-stats-v1 \
		"${common_args[@]}" \
		--data-raw '{}'
fi
