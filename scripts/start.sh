#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

case "${1:-}" in
  "") docker compose up -d --no-build ;;
  --build) docker compose up -d --build ;;
  *) printf '用法：bash scripts/start.sh [--build]\n' >&2; exit 2 ;;
esac

frontend_url='http://localhost:8080'
printf '\n正在等待前端和后端就绪…\n'
for ((attempt = 1; attempt <= 60; attempt++)); do
  if curl --noproxy '*' --fail --silent --output /dev/null --connect-timeout 1 --max-time 2 "$frontend_url/" \
    && curl --noproxy '*' --fail --silent --output /dev/null --connect-timeout 1 --max-time 2 "$frontend_url/healthz"; then
    printf '\n杭电校园助手已就绪\n\n'
    printf '  前端地址：%s/\n\n' "$frontend_url"
    printf 'macOS 终端：按住 Command 并点击上方地址即可打开。\n'
    printf '查看日志：make logs\n停止服务：make down\n'
    exit 0
  fi
  sleep 1
done

printf '\n等待超时，前端或后端尚未就绪。请运行 docker compose ps 和 make logs 查看原因。\n' >&2
exit 1
