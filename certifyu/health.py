"""Lightweight liveness / readiness endpoints for uptime monitors.

GET /health     — liveness; returns 200 if the process can respond.
GET /healthz    — readiness; verifies the DB is reachable too. Returns 503 on
                  database failure so an orchestrator can route around the host.
"""
from django.db import connection
from django.http import JsonResponse


def liveness(request):
    return JsonResponse({'status': 'ok'})


def readiness(request):
    db_ok = False
    error = None
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
        db_ok = True
    except Exception as exc:  # pragma: no cover - defensive
        error = type(exc).__name__
    code = 200 if db_ok else 503
    return JsonResponse({'status': 'ok' if db_ok else 'degraded',
                         'database': db_ok, 'error': error}, status=code)
