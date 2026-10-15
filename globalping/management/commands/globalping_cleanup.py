from django.core.management.base import BaseCommand
from globalping.tasks import cleanup,expire_stalled


class Command(BaseCommand):
    help='Remove histórico Global Ping expirado e marca tarefas abandonadas (sem enviar medições).'
    def handle(self,*args,**options):
        expire_stalled()
        cleanup()
        self.stdout.write(self.style.SUCCESS('Histórico expirado removido; tarefas abandonadas verificadas.'))
