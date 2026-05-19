#!/usr/bin/env python
"""
Pre-deploy API smoke tests for Nova Hymnal Backend.
Run from Nova-Hymnal-Backend: python scripts/preflight_api_test.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field

# Project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

User = get_user_model()


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append(Result(name, ok, detail))

    def print_summary(self) -> int:
        passed = sum(1 for r in self.results if r.ok)
        failed = len(self.results) - passed
        print("\n" + "=" * 72)
        print("PREFLIGHT TEST SUMMARY")
        print("=" * 72)
        for r in self.results:
            mark = "PASS" if r.ok else "FAIL"
            line = f"  [{mark}] {r.name}"
            if r.detail:
                line += f" — {r.detail}"
            print(line)
        print("-" * 72)
        print(f"  Total: {len(self.results)}  Passed: {passed}  Failed: {failed}")
        print("=" * 72)
        return 0 if failed == 0 else 1


def run_django_checks(report: Report) -> None:
    try:
        call_command("check", verbosity=0)
        report.add("django check", True)
    except Exception as e:
        report.add("django check", False, str(e))

    try:
        call_command("migrate", "--check", verbosity=0)
        report.add("migrations applied", True)
    except Exception as e:
        report.add("migrations applied", False, str(e))

    try:
        from config.wsgi import application

        assert application is not None
        report.add("wsgi application import", True)
    except Exception as e:
        report.add("wsgi application import", False, str(e))

    db = settings.DATABASES["default"]
    report.add(
        "database config",
        db["ENGINE"].endswith("postgresql"),
        f"{db['ENGINE']} @ {db.get('HOST', 'local')}",
    )


def _get(client: Client, path: str, **extra):
    return client.get(path, HTTP_HOST="localhost", **extra)


def _post(client: Client, path: str, **extra):
    return client.post(path, HTTP_HOST="localhost", **extra)


def run_api_tests(report: Report) -> None:
    client = Client()
    base = "/api/v1"

    # --- Public read endpoints ---
    endpoints = [
        ("GET", f"{base}/denominations/", 200),
        ("GET", f"{base}/categories/", 200),
        ("GET", f"{base}/authors/", 200),
        ("GET", f"{base}/hymns/", 200),
        ("GET", f"{base}/hymns/?denomination=1&hymn_period=new", 200),
        ("GET", f"{base}/hymns/daily/", [200, 404]),
        ("GET", f"{base}/sheet-music/", 200),
        ("GET", "/swagger/", 200),
        ("GET", "/admin/login/", 200),
    ]

    for method, path, expected in endpoints:
        resp = _get(client, path) if method == "GET" else _post(client, path)
        ok = (
            resp.status_code in expected
            if isinstance(expected, list)
            else resp.status_code == expected
        )
        detail = f"HTTP {resp.status_code}"
        if ok and path.endswith("/hymns/") and resp.status_code == 200:
            try:
                data = resp.json()
                count = data.get("count", len(data.get("results", [])))
                detail += f", count={count}"
            except Exception:
                pass
        if ok and path.endswith("/denominations/"):
            try:
                data = resp.json()
                n = len(data.get("results", data if isinstance(data, list) else []))
                detail += f", hymnals={n}"
            except Exception:
                pass
        report.add(f"{method} {path}", ok, detail)

    # --- Hymn detail (first hymn if any) ---
    list_resp = _get(client, f"{base}/hymns/?page_size=1")
    if list_resp.status_code == 200:
        results = list_resp.json().get("results", [])
        if results:
            hymn_id = results[0]["id"]
            try:
                detail_resp = _get(client, f"{base}/hymns/{hymn_id}/")
            except Exception as e:
                report.add(
                    f"GET {base}/hymns/{{id}}/",
                    False,
                    f"id={hymn_id} raised {e}",
                )
                detail_resp = None
            if detail_resp is not None:
                report.add(
                    f"GET {base}/hymns/{{id}}/",
                    detail_resp.status_code == 200,
                    f"id={hymn_id} HTTP {detail_resp.status_code}",
                )
                if detail_resp.status_code == 200:
                    body = detail_resp.json()
                    has_verses = "verses" in body
                    report.add("hymn detail has verses", has_verses)
        else:
            report.add("GET hymn detail", False, "no hymns in database")
    else:
        report.add("GET hymn detail", False, f"list failed HTTP {list_resp.status_code}")

    # --- Auth: protected without token ---
    sub_resp = _get(client, f"{base}/subscriptions/status/")
    report.add(
        "GET subscriptions/status/ (no auth)",
        sub_resp.status_code == 401,
        f"HTTP {sub_resp.status_code}",
    )

    # --- Auth: register + login + profile + subscription status ---
    suffix = uuid.uuid4().hex[:8]
    username = f"preflight_{suffix}"
    password = "PreflightTest1!"
    reg = _post(
        client,
        f"{base}/auth/register/",
        data=json.dumps(
            {
                "username": username,
                "email": f"{username}@test.local",
                "password": password,
                "password2": password,
                "platform": "web",
            }
        ),
        content_type="application/json",
    )
    reg_detail = f"HTTP {reg.status_code}"
    if reg.status_code == 400 and "application/json" in reg.get("Content-Type", ""):
        reg_detail += f" {reg.json()}"
    report.add(
        "POST auth/register/",
        reg.status_code in (201, 400),
        reg_detail,
    )

    login = _post(
        client,
        f"{base}/auth/login/",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    if login.status_code == 200:
        tokens = login.json()
        access = tokens.get("access")
        report.add("POST auth/login/", True, "access token received")
        auth = {"HTTP_AUTHORIZATION": f"Bearer {access}"}
        profile = _get(client, f"{base}/auth/profile/", **auth)
        report.add(
            "GET auth/profile/",
            profile.status_code == 200,
            f"HTTP {profile.status_code}",
        )
        sub = _get(client, f"{base}/subscriptions/status/", **auth)
        report.add(
            "GET subscriptions/status/ (auth)",
            sub.status_code == 200,
            f"has_premium={sub.json().get('has_premium')}",
        )
        verify = _post(
            client,
            f"{base}/subscriptions/verify/",
            data=json.dumps(
                {
                    "transaction_id": f"test_{suffix}",
                    "product_id": "nova_hymnal_premium_web_annual",
                    "receipt_data": "{}",
                    "platform": "web",
                }
            ),
            content_type="application/json",
            **auth,
        )
        report.add(
            "POST subscriptions/verify/",
            verify.status_code in (200, 201),
            f"HTTP {verify.status_code}",
        )
        # Cleanup test user
        User.objects.filter(username=username).delete()
    else:
        report.add("POST auth/login/", False, f"HTTP {login.status_code} {login.content[:200]}")


def run_production_readiness(report: Report) -> None:
    if settings.DEBUG:
        report.add("DEBUG mode", True, "development (expected locally)")
    else:
        report.add("DEBUG mode", False, "DEBUG=False for production")

    if not settings.DEBUG:
        proxy = getattr(settings, "SECURE_PROXY_SSL_HEADER", None)
        report.add(
            "SECURE_PROXY_SSL_HEADER",
            proxy is not None,
            "required on Render when SECURE_SSL_REDIRECT=True",
        )

    hosts = settings.ALLOWED_HOSTS
    report.add(
        "ALLOWED_HOSTS",
        bool(hosts) and "*" not in hosts,
        ", ".join(hosts[:5]) + ("..." if len(hosts) > 5 else ""),
    )

    secret = settings.SECRET_KEY
    secret_ok = secret and "insecure" not in secret.lower() and len(secret) > 30
    if settings.DEBUG:
        report.add(
            "SECRET_KEY (production)",
            True,
            "skipped in DEBUG — set strong SECRET_KEY on Render",
        )
    else:
        report.add(
            "SECRET_KEY",
            secret_ok,
            "use a strong random SECRET_KEY on Render",
        )


def main() -> int:
    print("Nova Hymnal Backend — preflight tests")
    print(f"  ENV={getattr(settings, 'ENV', '?')}  DEBUG={settings.DEBUG}")
    print(f"  DB={settings.DATABASES['default']['HOST']}")
    print()

    report = Report()
    run_django_checks(report)
    run_production_readiness(report)
    run_api_tests(report)
    return report.print_summary()


if __name__ == "__main__":
    sys.exit(main())
