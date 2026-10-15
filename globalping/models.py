import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from core.models import Timestamped


def default_requests(): return settings.GLOBALPING_REQUESTS_PER_HOUR
def default_probes(): return settings.GLOBALPING_MAX_PROBES
def default_budget(): return settings.GLOBALPING_PROBES_PER_HOUR


class GlobalpingPolicy(Timestamped):
    """One installation-wide policy; secrets are never stored in this model."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    enabled = models.BooleanField('Ferramenta habilitada', default=True)
    requests_per_hour = models.PositiveIntegerField('Inícios por IP e usuário/hora', default=default_requests, validators=[MinValueValidator(1), MaxValueValidator(120)])
    reads_per_hour = models.PositiveIntegerField('Consultas locais por IP e usuário/hora', default=1800, validators=[MinValueValidator(60), MaxValueValidator(7200)])
    max_probes = models.PositiveSmallIntegerField('Máximo de sondas por medição', default=default_probes, validators=[MinValueValidator(1), MaxValueValidator(50)])
    probes_per_hour = models.PositiveIntegerField('Orçamento global de sondas/hora', default=default_budget, validators=[MinValueValidator(1), MaxValueValidator(250)])
    cache_seconds = models.PositiveIntegerField('Cache de resultados (segundos)', default=300, validators=[MinValueValidator(30), MaxValueValidator(3600)])
    history_hours = models.PositiveSmallIntegerField('Histórico temporário (horas)', default=24, validators=[MinValueValidator(1), MaxValueValidator(168)])
    timeout_seconds = models.PositiveSmallIntegerField('Tempo máximo da medição (segundos)', default=90, validators=[MinValueValidator(45), MaxValueValidator(180)])
    poll_seconds = models.PositiveSmallIntegerField('Intervalo de consulta à API (segundos)', default=2, validators=[MinValueValidator(1), MaxValueValidator(15)])

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        return cls.objects.filter(pk=1).first() or cls()

    def __str__(self): return 'Limites do Lignet Global Ping'


class Measurement(Timestamped):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    session_hash = models.CharField(max_length=64, db_index=True)
    kind = models.CharField(max_length=12, choices=[('ping','Ping'),('traceroute','Traceroute'),('dns','DNS'),('http','HTTP')])
    target = models.CharField(max_length=253)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='queued', db_index=True)
    remote_id = models.CharField(max_length=128, blank=True, db_index=True)
    probes_requested = models.PositiveSmallIntegerField()
    probes_count = models.PositiveSmallIntegerField(null=True, blank=True)
    # Actual usage from provider headers; unknown stays null (never guessed).
    consumed = models.PositiveIntegerField(null=True, blank=True)
    remaining = models.PositiveIntegerField(null=True, blank=True)
    quota_reset = models.PositiveIntegerField(null=True, blank=True)
    quota_limit = models.PositiveIntegerField(null=True, blank=True)
    credits_consumed = models.PositiveIntegerField(null=True, blank=True)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    poll_count = models.PositiveSmallIntegerField(default=0)
    etag = models.CharField(max_length=256, blank=True)
    results = models.JSONField(default=dict)
    error = models.CharField(max_length=300, blank=True)
    retry_after = models.PositiveIntegerField(null=True, blank=True)
    from_cache = models.BooleanField(default=False)
    measured_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['session_hash', '-created_at'])]
        constraints = [models.CheckConstraint(condition=models.Q(probes_requested__gte=1, probes_requested__lte=50), name='globalping_probe_range')]
