#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$REPO_ROOT" || exit

: "${REPO_URL:?REPO_URL must be set for associating the image}"
: "${IMAGE_TAG_BASE:?IMAGE_TAG_BASE must be set for the image}"

get_commit_time() {
  TZ=UTC0 git log -1 \
    --format='tformat:%cd' \
    --date='format:%Y-%m-%dT%H:%M:%SZ'
}

SOURCE_EPOCH="$(get_commit_time)"
export SOURCE_EPOCH

image_tag_timestamp="${SOURCE_EPOCH//:/}"
image_tag_timestamp="${image_tag_timestamp//-/}"
image_tag_timestamp="${image_tag_timestamp,,}"

git_commit="$(git rev-parse HEAD)"
image_tag="$IMAGE_TAG_BASE:${image_tag_timestamp}-g${git_commit:0:8}"

echo "source epoch = $SOURCE_EPOCH"
echo "repo url     = $REPO_URL"
echo "image tag    = $image_tag"

output_param="type=image,name=${image_tag}"

add_annotation() {
    local k="$1"
    local v="$2"

    output_param="$output_param,annotation.$k=$v,annotation-index.$k=$v"
}

add_annotation org.opencontainers.image.title "RuyiSDK Backend"
add_annotation org.opencontainers.image.description "Backend for online features of RuyiSDK"
add_annotation org.opencontainers.image.licenses "Apache-2.0"
add_annotation org.opencontainers.image.source "$REPO_URL"
add_annotation org.opencontainers.image.url "$REPO_URL"
add_annotation org.opencontainers.image.documentation "$REPO_URL"
add_annotation org.opencontainers.image.revision "$git_commit"

[[ -n $PUSH_IMAGE ]] && output_param="$output_param,push=true"

args=(
    --rm
    --platform "linux/amd64"  # linux/arm64 too slow to build, linux/riscv64 is not yet supported
    -o "$output_param"
    .
)
exec docker buildx build "${args[@]}"
