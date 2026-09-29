"""Is this deployment configured as the formative pilot? (cycle 10, C10-06)

Reads the configuration the way the application does -- the root keys of ``.streamlit/secrets.toml``
(the user's, then the project's), and then the environment -- and checks it against
docs/READINESS_PILOTO_FORMATIVO.md. It starts nothing and writes nothing, and it never prints a
secret, a URL or a hash: only which rule holds and why.

    python3 tools_pilot_preflight.py              # the configuration
    python3 tools_pilot_preflight.py --connect    # also open the database, reading only

Exit status 0 when every required rule holds, 1 otherwise. A recommendation never fails it.
"""
from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRUE = {"1", "true", "yes", "on"}
OFF = {"off", "none", "0", "false", "no"}
REQUIRED, RECOMMENDED = "required", "recommended"


def load_settings(secrets_paths=None, environ=None):
    """{name: value}: root keys of the secrets files (later files win), then environment variables."""
    environ = os.environ if environ is None else environ
    paths = secrets_paths if secrets_paths is not None else (
        Path.home() / ".streamlit" / "secrets.toml", ROOT / ".streamlit" / "secrets.toml")
    secrets = {}
    for path in paths:
        path = Path(path)
        if path.is_file():
            with path.open("rb") as handle:
                data = tomllib.load(handle)
            secrets.update({key: str(value) for key, value in data.items() if not isinstance(value, dict)})
    names = set(secrets) | {name for name in environ if name.startswith("MRS_") or name == "OPENAI_API_KEY"}
    return {name: str(secrets[name]) if name in secrets else str(environ.get(name, "")) for name in names}


def _is(settings, name, values):
    return str(settings.get(name, "")).strip().lower() in values


def checks(settings, connect=False):
    """Every rule, as (id, level, holds, message). No message carries a value that could be a secret."""
    sys.path.insert(0, str(ROOT))
    import check_database
    found = []

    def rule(identifier, level, holds, message):
        found.append((identifier, level, bool(holds), message))

    rule("auth_mode", REQUIRED, _is(settings, "MRS_AUTH_MODE", {"accounts"}),
         "MRS_AUTH_MODE = accounts: cuentas por persona y permisos en la base.")
    url = str(settings.get("MRS_DATABASE_URL", "")).strip()
    complaint = check_database.describe(url)
    rule("database_url", REQUIRED, complaint is None,
         "MRS_DATABASE_URL es una URL PostgreSQL bien formada." if complaint is None
         else "MRS_DATABASE_URL: " + complaint)
    rule("no_local_sqlite", REQUIRED, not _is(settings, "MRS_ALLOW_LOCAL_SQLITE", TRUE),
         "MRS_ALLOW_LOCAL_SQLITE no está activo: SQLite es sólo para desarrollo local.")
    offline = _is(settings, "MRS_OFFLINE_CASES", TRUE)
    rule("offline_cases", REQUIRED, offline,
         "MRS_OFFLINE_CASES = 1: casos del banco, sin generación de casos ni de fotos, sin IA en el encuentro.")
    key_present = bool(str(settings.get("OPENAI_API_KEY", "")).strip())
    rule("provider_key_withheld", REQUIRED, offline or not key_present,
         ("La clave del proveedor está presente y MRS_OFFLINE_CASES la retiene en todas partes."
          if key_present and offline else
          "No hay clave del proveedor configurada." if not key_present else
          "Hay una clave del proveedor y nada la retiene: la aplicación podría llamar al proveedor."))
    rule("image_review", REQUIRED, _is(settings, "MRS_IMAGE_REQUIRE_REVIEW", TRUE),
         "MRS_IMAGE_REQUIRE_REVIEW = on: sólo fotos con sus dos revisiones humanas aprobadas.")
    rule("no_replay_case", REQUIRED, not str(settings.get("MRS_REPLAY_CASE", "")).strip(),
         "MRS_REPLAY_CASE no está definido: el piloto usa los 31 casos del banco, ningún caso escrito por IA.")
    rule("paid_generation_off", RECOMMENDED, _is(settings, "MRS_PAID_GENERATION", OFF),
         "MRS_PAID_GENERATION = off (el modo sin conexión ya la cierra; esto la cierra dos veces).")
    rule("free_generation_closed", RECOMMENDED, not _is(settings, "MRS_FREE_GENERATION", {"all", "everyone", "any"}),
         "MRS_FREE_GENERATION no abre la generación libre a todas las cuentas.")
    rule("no_pinned_case", RECOMMENDED, not str(settings.get("MRS_DEFAULT_VARIANT", "")).strip(),
         "MRS_DEFAULT_VARIANT no está definido: el currículo elige el caso.")
    rule("no_batch_settings", RECOMMENDED,
         not any(str(settings.get(name, "")).strip() for name in (
             "MRS_SYNTHETIC_ACCOUNTS", "MRS_BATCH_STAFF_USER", "MRS_BATCH_STAFF_PASSWORD",
             "MRS_BATCH_RESIDENT_USER", "MRS_BATCH_RESIDENT_PASSWORD")),
         "Sin las variables del lote de prueba (MRS_SYNTHETIC_ACCOUNTS, MRS_BATCH_*): no hay cuentas ni "
         "contraseñas de prueba en el despliegue.")
    rule("code_version", RECOMMENDED, bool(str(settings.get("MRS_CODE_VERSION", "")).strip()) or (ROOT / ".git").exists(),
         "Cada encuentro podrá registrar el commit que lo produjo (MRS_CODE_VERSION o el checkout).")
    admin_hash = str(settings.get("MRS_ADMIN_PASSWORD_HASH", "")).strip()
    if admin_hash or str(settings.get("MRS_ADMIN_USERNAME", "")).strip():
        problem = check_database.describe_admin_hash(admin_hash)
        rule("admin_bootstrap", REQUIRED, bool(str(settings.get("MRS_ADMIN_USERNAME", "")).strip()) and problem is None,
             "MRS_ADMIN_USERNAME y MRS_ADMIN_PASSWORD_HASH bien formados para crear el primer administrador."
             if problem is None else "MRS_ADMIN_PASSWORD_HASH: " + problem)
    if connect and complaint is None:
        found.extend(_connection_checks(url))
    return found


def _connection_checks(url):
    """Open the database, reading only: is it reachable, and does it hold an active administrator?"""
    try:
        import psycopg
        with psycopg.connect(url, connect_timeout=10) as connection:
            cursor = connection.execute("SELECT to_regclass('mrs_users') IS NOT NULL")
            has_tables = bool(cursor.fetchone()[0])
            admins = 0
            if has_tables:
                admins = connection.execute(
                    "SELECT COUNT(*) FROM mrs_users WHERE role = 'admin' AND active = 1").fetchone()[0]
    except Exception as error:                     # the driver's message can carry the URL
        return [("database_reachable", REQUIRED, False,
                 f"No se pudo abrir la base ({type(error).__name__}); python3 check_database.py dice por qué.")]
    return [("database_reachable", REQUIRED, True, "La base responde."),
            ("administrator", RECOMMENDED, admins > 0,
             f"La base tiene {admins} administrador(es) activo(s)." if has_tables else
             "La base aún no tiene tablas: la aplicación las crea al abrir, con el administrador inicial.")]


def report(found):
    lines = []
    for identifier, level, holds, message in found:
        mark = "OK " if holds else ("FALLA" if level == REQUIRED else "AVISO")
        lines.append(f"[{mark}] {identifier}: {message}")
    failed = [item for item in found if item[1] == REQUIRED and not item[2]]
    lines.append("")
    lines.append("Configuración del piloto: LISTA." if not failed else
                 f"Configuración del piloto: NO LISTA ({len(failed)} regla(s) obligatoria(s) sin cumplir).")
    return "\n".join(lines), not failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--connect", action="store_true", help="also open the database, reading only")
    parser.add_argument("--secrets", action="append", help="a secrets.toml to read instead of the default ones")
    args = parser.parse_args(argv)
    text, ready = report(checks(load_settings(args.secrets), connect=args.connect))
    print(text)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
