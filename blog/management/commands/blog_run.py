import fcntl
import hashlib
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from blog.services import execute_run


class Command(BaseCommand):
    help = "Coleta pautas, gera o lote diário e publica artigos aprovados/agendados."

    def handle(self, **options):
        key = hashlib.sha256(str(settings.BASE_DIR).encode()).hexdigest()[:16]
        path = Path(tempfile.gettempdir()) / f"lignet-blog-{key}.lock"
        with path.open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise CommandError("Outra execução do blog está ativa neste servidor.") from exc
            # A session advisory lock also protects deployments sharing PostgreSQL.
            if connection.vendor == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_try_advisory_lock(738192046)")
                    if not cursor.fetchone()[0]:
                        raise CommandError("Outra execução do blog está ativa no banco.")
            try:
                run = execute_run()
                if run is None:
                    self.stdout.write("Rotina desabilitada no painel editorial.")
                else:
                    self.stdout.write(f"Execução #{run.pk}: {run.status}; encontradas={run.found}, "
                                      f"produzidos={run.produced}, publicados={run.published}")
                    if run.status != "complete":
                        raise CommandError("Execução com erros. Consulte o histórico editorial e o log.")
            finally:
                if connection.vendor == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_unlock(738192046)")
