"""Is this deployment configured as the formative pilot? (cycle 10, C10-06; fail-closed, 2026-10-06)

Reads the configuration the way the application does and asks the application's own readers what they
would do with it:

* the root keys of ``.streamlit/secrets.toml`` (the user's, then the project's), parsed by Streamlit's
  own parser, and copied into the environment by Streamlit's own rule (text and numbers only: a TOML
  boolean never reaches the environment);
* the environment the application starts with;
* ``offline_cases``, ``image_scene`` and ``account_portal``, the readers the application calls, run on
  that view.

Every requirement of the pilot freeze (``pilot_freeze.RUNTIME_FLAGS``, the table "Indicadores del entorno"
of docs/revision/PILOT_FREEZE_MANIFEST.md) is a required rule: one that does not hold, or that cannot be
read, fails the preflight. A setting the freeze wants unset fails with any value. It starts nothing and
writes nothing, and it never prints a secret, a URL, a hash or a setting's value: only which rule holds
and why.

    python3 tools_pilot_preflight.py                 # the configuration
    python3 tools_pilot_preflight.py --connect       # also open the database, reading only
    python3 tools_pilot_preflight.py --commit SHA    # the commit to deploy (default: this checkout's HEAD)

With ``--secrets`` the file is the deployment's whole configuration: a hosted deployment receives its
Secrets and none of this machine's environment, so the local ``MRS_*``, ``OPENAI_API_KEY`` and
``STREAMLIT_*`` variables are left out (and named in a warning). ``fastReruns`` is read from the
``.streamlit/config.toml`` of the commit to deploy.

Exit status 0 only when every required rule holds, 1 otherwise. A recommendation never fails it.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED, RECOMMENDED = "required", "recommended"
ROLES = ("resident", "faculty", "admin")
FAST_RERUNS_OVERRIDE = "STREAMLIT_RUNNER_FAST_RERUNS"
_SHA = re.compile(r"[0-9a-f]{7,40}")

#: The rule that enforces each requirement of the pilot freeze (pilot_freeze.RUNTIME_FLAGS). A new
#: requirement there fails test_tools_pilot_preflight.py until it has its rule here.
FREEZE_RULES = {
    ".streamlit/config.toml [runner] fastReruns": "fast_reruns",
    "MRS_OFFLINE_CASES": "offline_cases",
    "MRS_PAID_GENERATION": "paid_generation_off",
    "MRS_FREE_GENERATION": "free_generation_closed",
    "MRS_DEFAULT_VARIANT": "no_pinned_case",
    "MRS_REPLAY_CASE": "no_replay_case",
    "MRS_CODE_VERSION": "code_version",
    "MRS_IMAGE_REQUIRE_REVIEW": "image_review",
}


def default_secrets_paths():
    return Path.home() / ".streamlit" / "secrets.toml", ROOT / ".streamlit" / "secrets.toml"


def _deployment_setting(name):
    return name.startswith(("MRS_", "STREAMLIT_")) or name == "OPENAI_API_KEY"


def target_environ(environ):
    """The environment a hosted deployment starts with: this machine's, without its deployment settings."""
    kept = {name: value for name, value in environ.items() if not _deployment_setting(name)}
    return kept, sorted(name for name in environ if _deployment_setting(name))


class RuntimeView:
    """The configuration as the application receives it: the parsed Secrets and its starting environment.

    ``config_path`` names a config.toml to read instead of the one in the commit to deploy (tests).
    ``ignored`` names the local variables left out because the deployment does not receive them.
    """

    def __init__(self, secrets, environ, config_path=None, ignored=()):
        self.secrets = dict(secrets)
        self.environ = dict(environ)
        self.config_path = Path(config_path) if config_path is not None else None
        self.ignored = tuple(ignored)

    def is_set(self, name):
        """Present with a value, in the Secrets (of any type) or in the starting environment."""
        value = self.secrets.get(name)
        if value is not None and str(value).strip():
            return True
        return bool(str(self.environ.get(name, "")).strip())


def load_view(secrets_paths=None, environ=None, config_path=None, ignored=()):
    """Parse the Secrets files as Streamlit does (later files win). A malformed file raises, as it does there."""
    from streamlit.runtime.secrets import Secrets
    parser = Secrets()
    secrets = {}
    for path in (secrets_paths if secrets_paths is not None else default_secrets_paths()):
        if Path(path).is_file():
            parsed, _ = parser._parse_toml_file(str(path))
            secrets.update(parsed)
    return RuntimeView(secrets, os.environ if environ is None else environ, config_path, ignored)


@contextmanager
def as_the_application(view):
    """The environment and ``st.secrets`` the application would see; both are restored afterwards.

    Streamlit copies every root key of the Secrets whose value is text or a number into the environment
    when it starts (``Secrets._maybe_set_environment_variable``); the readers that use ``st.secrets`` see
    the parsed values themselves.
    """
    import streamlit
    from streamlit.runtime.secrets import AttrDict, Secrets
    saved_environ, saved_secrets = dict(os.environ), streamlit.secrets
    os.environ.clear()
    os.environ.update({str(key): str(value) for key, value in view.environ.items()})
    try:
        for key, value in view.secrets.items():
            Secrets._maybe_set_environment_variable(key, value)
        streamlit.secrets = AttrDict(view.secrets)
        yield
    finally:
        streamlit.secrets = saved_secrets
        os.environ.clear()
        os.environ.update(saved_environ)


@contextmanager
def _without(name):
    """One environment variable lifted for a moment, to read another setting on its own."""
    saved = os.environ.pop(name, None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ[name] = saved


def checkout_commit(root=ROOT):
    """The full SHA of this checkout's HEAD, or None."""
    try:
        found = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    sha = found.stdout.strip().lower()
    return sha if found.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else None


def resolve_commit(commit, root=ROOT):
    """The full SHA of the commit to deploy: ``--commit`` as given or expanded by git, else HEAD."""
    if commit is None:
        return checkout_commit(root)
    commit = str(commit).strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}", commit):
        return commit
    if not _SHA.fullmatch(commit):
        return None
    try:
        found = subprocess.run(["git", "rev-parse", "--verify", "--quiet", commit + "^{commit}"], cwd=root,
                               capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    sha = found.stdout.strip().lower()
    return sha if found.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else None


def committed_file(commit, relative, root=ROOT):
    """A file as the commit to deploy holds it (not as this working tree may have it), or None."""
    try:
        found = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=root, capture_output=True, text=True,
                               timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return found.stdout if found.returncode == 0 else None


def _fast_reruns(view, expected):
    import toml                                      # the parser Streamlit reads its config.toml with
    if view.is_set(FAST_RERUNS_OVERRIDE):
        return False, (f"{FAST_RERUNS_OVERRIDE} está definido: sobrescribe la configuración del repositorio. "
                       "El congelamiento exige [runner] fastReruns = false de .streamlit/config.toml.")
    if view.config_path is not None:
        text = view.config_path.read_text(encoding="utf-8") if view.config_path.is_file() else None
    elif expected is None:
        return False, ("No se pudo determinar el commit que se despliega, ni leer su .streamlit/config.toml: el "
                       "congelamiento exige [runner] fastReruns = false.")
    else:
        text = committed_file(expected, ".streamlit/config.toml")
    if text is None:
        return False, ("No se pudo leer .streamlit/config.toml del commit que se despliega: el congelamiento exige "
                       "[runner] fastReruns = false.")
    if (toml.loads(text).get("runner") or {}).get("fastReruns") is False:
        return True, ("[runner] fastReruns = false en .streamlit/config.toml del commit que se despliega: un segundo "
                      "clic nunca inicia una ejecución concurrente.")
    return False, ("[runner] fastReruns no es el booleano false en .streamlit/config.toml del commit que se "
                   "despliega: el congelamiento lo exige (Fase 0, 0D).")


def _offline(offline_cases):
    if offline_cases.offline_cases_enabled():
        return True, ("MRS_OFFLINE_CASES: la aplicación queda sin conexión (casos del banco, sin generación de "
                      "casos ni de fotos, sin IA en el encuentro).")
    return False, ("MRS_OFFLINE_CASES: la aplicación NO queda sin conexión. Debe llegarle como texto o número "
                   "(MRS_OFFLINE_CASES = \"1\"); un booleano TOML (true) nunca llega al entorno de la aplicación.")


def _provider_key(account_portal, clinical_scene):
    from streamlit import secrets
    raw = secrets.get("OPENAI_API_KEY")
    present = bool(str(raw).strip()) if raw is not None else bool(os.environ.get("OPENAI_API_KEY", "").strip())
    reachable = bool(account_portal._setting("OPENAI_API_KEY")) or bool(clinical_scene.setting("OPENAI_API_KEY"))
    if not present:
        return True, "No hay clave del proveedor configurada."
    if not reachable:
        return True, "La clave del proveedor está presente y la aplicación la retiene en todas partes."
    return False, "Hay una clave del proveedor y la aplicación la leería: podría llamar al proveedor."


def _image_review(image_scene):
    if image_scene.review_required():
        return True, ("MRS_IMAGE_REQUIRE_REVIEW: la aplicación muestra sólo fotos con sus dos revisiones humanas "
                      "aprobadas.")
    return False, "MRS_IMAGE_REQUIRE_REVIEW no está activo en la aplicación: el congelamiento exige \"on\"."


def _paid_generation(offline_cases):
    # Read on its own: the offline switch closes paid generation as well, and the freeze wants both closed.
    with _without("MRS_OFFLINE_CASES"):
        opened = [role for role in ROLES if offline_cases.paid_generation_allowed(role)]
    if not opened:
        return True, "MRS_PAID_GENERATION cierra la generación pagada para todas las cuentas."
    return False, ("MRS_PAID_GENERATION no la cierra (la abre a: " + ", ".join(opened) + "). El congelamiento "
                   "exige MRS_PAID_GENERATION = \"off\", como texto.")


def _unset(view, name, why):
    if view.is_set(name):
        return False, f"{name} está definido: el congelamiento lo exige ausente ({why})."
    return True, f"{name} no está definido."


def _code_version(view, expected):
    value = str(os.environ.get("MRS_CODE_VERSION", "")).strip().lower()
    if not value:
        if view.is_set("MRS_CODE_VERSION"):
            return False, ("MRS_CODE_VERSION no llega al entorno de la aplicación: debe escribirse como texto "
                           "(el commit que se despliega).")
        return False, "MRS_CODE_VERSION no está definido: el congelamiento exige el commit que se despliega."
    if expected is None:
        return False, ("No se pudo determinar el commit que se despliega: corra el preflight en la copia de ese "
                       "commit o páselo con --commit.")
    if not _SHA.fullmatch(value):
        return False, "MRS_CODE_VERSION no es un commit (7 a 40 caracteres hexadecimales)."
    if not expected.startswith(value):
        return False, "MRS_CODE_VERSION no es el commit que se despliega."
    return True, "MRS_CODE_VERSION es el commit que se despliega: cada encuentro y cada turno lo registran."


def checks(view, connect=False, commit=None):
    """Every rule, as (id, level, holds, message). No message carries a setting's value or a secret.

    A rule that cannot be evaluated fails (a required one fails the preflight); the error is named by its
    class only, since a parser's or a driver's message can carry what it read.
    """
    sys.path.insert(0, str(ROOT))
    import account_portal
    import check_database
    import clinical_scene
    import image_scene
    import offline_cases
    found = []
    expected = resolve_commit(commit)

    def rule(identifier, level, evaluate):
        try:
            holds, message = evaluate()
        except Exception as error:                  # noqa: BLE001 -- fail closed, and say only its class
            holds, message = False, f"no se pudo evaluar ({type(error).__name__})."
        found.append((identifier, level, bool(holds), message))

    def database_url():
        complaint = check_database.describe(account_portal._setting("MRS_DATABASE_URL"))
        return complaint is None, ("MRS_DATABASE_URL es una URL PostgreSQL bien formada." if complaint is None
                                   else "MRS_DATABASE_URL: " + complaint)

    with as_the_application(view):
        rule("auth_mode", REQUIRED, lambda: (
            account_portal._setting("MRS_AUTH_MODE", "shared").lower() == "accounts",
            "MRS_AUTH_MODE = accounts: cuentas por persona y permisos en la base."))
        rule("database_url", REQUIRED, database_url)
        rule("no_local_sqlite", REQUIRED, lambda: (
            account_portal._setting("MRS_ALLOW_LOCAL_SQLITE", "false").lower() not in ("1", "true", "yes"),
            "MRS_ALLOW_LOCAL_SQLITE no está activo: SQLite es sólo para desarrollo local."))
        rule("fast_reruns", REQUIRED, lambda: _fast_reruns(view, expected))
        rule("offline_cases", REQUIRED, lambda: _offline(offline_cases))
        rule("provider_key_withheld", REQUIRED, lambda: _provider_key(account_portal, clinical_scene))
        rule("image_review", REQUIRED, lambda: _image_review(image_scene))
        rule("no_replay_case", REQUIRED, lambda: _unset(
            view, "MRS_REPLAY_CASE", "un caso escrito por IA está fuera de los 30 aceptados"))
        rule("paid_generation_off", REQUIRED, lambda: _paid_generation(offline_cases))
        rule("free_generation_closed", REQUIRED, lambda: _unset(
            view, "MRS_FREE_GENERATION", "la generación libre queda en el sandbox del administrador"))
        rule("no_pinned_case", REQUIRED, lambda: _unset(
            view, "MRS_DEFAULT_VARIANT", "un caso fijado salta la selección y la exclusión del congelamiento"))
        rule("code_version", REQUIRED, lambda: _code_version(view, expected))
        rule("no_batch_settings", RECOMMENDED, lambda: (
            not any(view.is_set(name) for name in (
                "MRS_SYNTHETIC_ACCOUNTS", "MRS_BATCH_STAFF_USER", "MRS_BATCH_STAFF_PASSWORD",
                "MRS_BATCH_RESIDENT_USER", "MRS_BATCH_RESIDENT_PASSWORD")),
            "Sin las variables del lote de prueba (MRS_SYNTHETIC_ACCOUNTS, MRS_BATCH_*): no hay cuentas ni "
            "contraseñas de prueba en el despliegue."))
        rule("local_environment", RECOMMENDED, lambda: (
            not view.ignored,
            "No había variables de despliegue en el entorno local." if not view.ignored else
            "Variables del entorno local que el despliegue no recibe, dejadas fuera: " + ", ".join(view.ignored)
            + ". El despliegue recibe sólo sus Secrets."))
        admin_name = account_portal._setting("MRS_ADMIN_USERNAME")
        admin_hash = account_portal._setting("MRS_ADMIN_PASSWORD_HASH")
        url = account_portal._setting("MRS_DATABASE_URL")
    if admin_hash or admin_name:
        problem = check_database.describe_admin_hash(admin_hash)
        found.append(("admin_bootstrap", REQUIRED, bool(admin_name) and problem is None,
                      "MRS_ADMIN_USERNAME y MRS_ADMIN_PASSWORD_HASH bien formados para crear el primer "
                      "administrador." if problem is None else "MRS_ADMIN_PASSWORD_HASH: " + problem))
    if connect and check_database.describe(url) is None:
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
    """The printed report and the verdict, which only the required rules decide."""
    lines = []
    for identifier, level, holds, message in found:
        mark = "OK " if holds else ("FALLA" if level == REQUIRED else "AVISO")
        lines.append(f"[{mark}] {identifier}: {message}")
    failed = [item for item in found if item[1] == REQUIRED and not item[2]]
    lines.append("")
    if not found:
        lines.append("Configuración del piloto: NO LISTA (no se evaluó ninguna regla).")
        return "\n".join(lines), False
    lines.append("Configuración del piloto: LISTA." if not failed else
                 f"Configuración del piloto: NO LISTA ({len(failed)} regla(s) obligatoria(s) sin cumplir).")
    return "\n".join(lines), not failed


def evaluate(secrets_paths=None, environ=None, connect=False, commit=None, config_path=None, ignored=()):
    """What the command prints and decides. Reading the configuration at all is itself a required rule."""
    try:
        view = load_view(secrets_paths, environ, config_path, ignored)
    except Exception as error:                     # noqa: BLE001 -- a parser's message can carry what it read
        return report([("secrets_readable", REQUIRED, False,
                        f"No se pudieron leer los Secrets como la aplicación ({type(error).__name__}).")])
    return report(checks(view, connect=connect, commit=commit))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--connect", action="store_true", help="also open the database, reading only")
    parser.add_argument("--secrets", action="append", help="a secrets.toml to read instead of the default ones")
    parser.add_argument("--commit", help="the commit to deploy (default: this checkout's HEAD)")
    args = parser.parse_args(argv)
    # A Secrets file given here is the deployment's configuration: it does not receive this machine's settings.
    environ, ignored = target_environ(os.environ) if args.secrets else (os.environ, ())
    text, ready = evaluate(args.secrets, environ, connect=args.connect, commit=args.commit, ignored=ignored)
    print(text)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
