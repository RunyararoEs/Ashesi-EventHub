import re
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


def _require_debug():
    if not settings.DEBUG:
        raise Http404()


@ensure_csrf_cookie
def test_runner_page(request):
    _require_debug()
    return render(
        request,
        'test_runner.html',
        {
            'suites': [
                {
                    'label': 'users',
                    'tests': [
                        'UserManager (create_user, create_superuser)',
                        'User roles & is_staff',
                        'Club, Student, ClubAdmin, SystemAdmin',
                        'Cascade deletes',
                    ],
                },
                {
                    'label': 'events',
                    'tests': [
                        'Event ↔ Club relations & ordering',
                        'Unique (club, slug)',
                        'EventRegistration uniqueness',
                        'Cascade deletes',
                    ],
                },
                {
                    'label': 'notifications',
                    'tests': [
                        'Club sync from event on save',
                        'Read state & related_name',
                        'Cascade on recipient delete',
                    ],
                },
            ],
        },
    )


def _parse_django_test_output(text: str) -> dict:
    """Extract per-test rows and summary from unittest-style output."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ' ... ok' in line:
            name = line.split(' ... ok')[0].strip()
            rows.append({'name': name, 'status': 'ok'})
        elif ' ... FAIL' in line:
            name = line.split(' ... FAIL')[0].strip()
            rows.append({'name': name, 'status': 'fail'})
        elif ' ... ERROR' in line:
            name = line.split(' ... ERROR')[0].strip()
            rows.append({'name': name, 'status': 'error'})

    summary = None
    ran = None
    duration_s = None
    ok = None
    m = re.search(r'^Ran\s+(\d+)\s+tests?\s+in\s+([\d.]+)s', text, re.MULTILINE)
    if m:
        ran = int(m.group(1))
        duration_s = float(m.group(2))
    if re.search(r'^OK\s*$', text, re.MULTILINE):
        ok = True
    if re.search(r'^FAILED\s', text, re.MULTILINE):
        ok = False
    if ran is not None:
        summary = {'ran': ran, 'duration_s': duration_s, 'ok': ok}

    return {'cases': rows, 'summary': summary}


@require_POST
def run_tests_api(request):
    _require_debug()
    manage_py = Path(settings.BASE_DIR) / 'manage.py'
    cmd = [
        sys.executable,
        str(manage_py),
        'test',
        'users',
        'events',
        'notifications',
        '--verbosity=2',
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return JsonResponse(
            {
                'exit_code': -1,
                'stdout': '',
                'stderr': 'Tests timed out after 180s.',
                'parsed': {'cases': [], 'summary': None},
            },
            status=504,
        )

    combined = (proc.stdout or '') + '\n' + (proc.stderr or '')
    parsed = _parse_django_test_output(combined)
    return JsonResponse(
        {
            'exit_code': proc.returncode,
            'stdout': proc.stdout or '',
            'stderr': proc.stderr or '',
            'parsed': parsed,
        }
    )
