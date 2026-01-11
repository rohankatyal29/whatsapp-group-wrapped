#!/usr/bin/env python3
"""CLI entry point for the WhatsApp Group Wrapped Quiz."""

import socket
import uvicorn


def get_local_ip() -> str:
    """Get the local IP address for LAN access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def main():
    local_ip = get_local_ip()
    port = 8000

    print()
    print("=" * 50)
    print("  WhatsApp Group Wrapped Quiz")
    print("=" * 50)
    print()
    print(f"  Quiz Master:  http://localhost:{port}")
    print(f"  Players join: http://{local_ip}:{port}/play")
    print()
    print("=" * 50)
    print()

    uvicorn.run(
        "quiz.server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
