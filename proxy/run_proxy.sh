#!/bin/bash
# Run the multi-client Meshtastic TCP proxy
#
# Environment variables (all optional):
#   LISTEN_HOST     - Host to listen on (default: 0.0.0.0)
#   LISTEN_PORT     - Port to listen on (default: 4404)
#   RADIO_HOST      - Meshtastic radio IP (default: 192.168.2.144)
#   RADIO_PORT      - Meshtastic radio port (default: 4403)
#   CHANNEL         - Channel index for AI responses (default: 2)
#   RESPONSE_DELAY  - Delay in seconds before sending AI response (default: 2.0)
#   DEBUG           - Set to 1 to enable debug logging
#
# Usage examples:
#   ./run_proxy.sh
#   ./run_proxy.sh --debug
#   RESPONSE_DELAY=5 ./run_proxy.sh
#   DEBUG=1 CHANNEL=0 ./run_proxy.sh

cd "$(dirname "$0")/.."

# Default values
LISTEN_HOST=${LISTEN_HOST:-0.0.0.0}
LISTEN_PORT=${LISTEN_PORT:-4404}
RADIO_HOST=${RADIO_HOST:-192.168.2.144}
RADIO_PORT=${RADIO_PORT:-4403}
CHANNEL=${CHANNEL:-2}
RESPONSE_DELAY=${RESPONSE_DELAY:-2.0}

# Build command arguments
ARGS=(
    --listen-host "$LISTEN_HOST"
    --listen-port "$LISTEN_PORT"
    --radio-host "$RADIO_HOST"
    --radio-port "$RADIO_PORT"
    --channel "$CHANNEL"
    --response-delay "$RESPONSE_DELAY"
)

# Add debug flag if DEBUG=1
if [ "${DEBUG:-0}" = "1" ]; then
    ARGS+=(--debug)
fi

echo "Starting Multi-Client Meshtastic Proxy..."
echo "  Listen: $LISTEN_HOST:$LISTEN_PORT"
echo "  Radio: $RADIO_HOST:$RADIO_PORT"
echo "  Channel: $CHANNEL"
echo "  Response delay: ${RESPONSE_DELAY}s"
[ "${DEBUG:-0}" = "1" ] && echo "  Debug: enabled"
echo ""

pipenv run python proxy/multi_client_proxy.py "${ARGS[@]}" "$@"
