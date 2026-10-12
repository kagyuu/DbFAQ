#!/bin/bash
# 開発環境専用: WSL(mirrored モード)の Docker コンテナから Windows 側の Ollama に届かせるための中継(CR-007)。
#   WSL の <docker0 の IP>:11435(既定 172.17.0.1。コンテナの host.docker.internal)で受けて、127.0.0.1:11434
#   (Windows の Ollama。mirrored モードのループバックで届く)へ転送する。docker0 の IP だけで待ち受けるので LAN からは届かない。
#   compose の api は .env の DBFAQ_LLM_BASE_URL=http://host.docker.internal:11435 で使う。
# 使い方: deploy/dev/llm-relay.sh start | stop | status
# 前提: socat(sudo apt install socat)。Windows の Ollama と同じポート 11434 は WSL では使えない(ポートを共有するため)。
set -uo pipefail
LISTEN_PORT="${LLM_RELAY_PORT:-11435}"
# 待ち受けるアドレス。既定は docker0 の IP(取れなければ 172.17.0.1)
BIND="${LLM_RELAY_BIND:-$(ip -4 -o addr show docker0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)}"
BIND="${BIND:-172.17.0.1}"
TARGET="${LLM_RELAY_TARGET:-127.0.0.1:11434}"
PIDFILE="${XDG_RUNTIME_DIR:-/tmp}/dbfaq-llm-relay.pid"

running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

case "${1:-status}" in
  start)
    if running; then echo "running (pid $(cat "$PIDFILE"), $BIND:$LISTEN_PORT -> $TARGET)"; exit 0; fi
    command -v socat > /dev/null || { echo "socat がありません(sudo apt install socat)"; exit 1; }
    setsid nohup socat "TCP-LISTEN:$LISTEN_PORT,bind=$BIND,fork,reuseaddr" "TCP:$TARGET" > /dev/null 2>&1 &
    echo $! > "$PIDFILE"
    sleep 0.5
    if running; then echo "started (pid $(cat "$PIDFILE"), $BIND:$LISTEN_PORT -> $TARGET)"; else echo "起動できませんでした"; exit 1; fi
    ;;
  stop)
    if running; then kill "$(cat "$PIDFILE")" && rm -f "$PIDFILE" && echo stopped; else rm -f "$PIDFILE"; echo "not running"; fi
    ;;
  status)
    if running; then echo "running (pid $(cat "$PIDFILE"), $BIND:$LISTEN_PORT -> $TARGET)"; else echo "not running"; exit 1; fi
    ;;
  *) echo "usage: $0 start|stop|status"; exit 2 ;;
esac
