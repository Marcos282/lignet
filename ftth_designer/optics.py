"""Primitives for stage 2; no universal receiver limits or network diagnoses."""
from decimal import Decimal, InvalidOperation, localcontext


def nonnegative(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('Informe um número finito não negativo.') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Informe um número finito não negativo.')
    return result


def fiber_loss(distance_km, attenuation_db_km, connectors=0, connector_loss=0,
               splices=0, splice_loss=0, additional=0):
    values = list(map(nonnegative, (distance_km, attenuation_db_km, connectors,
                                   connector_loss, splices, splice_loss, additional)))
    km, attenuation, connectors, connector_loss, splices, splice_loss, extra = values
    if connectors != connectors.to_integral_value() or splices != splices.to_integral_value():
        raise ValueError('Quantidades de conectores e emendas devem ser inteiras.')
    with localcontext() as context:
        context.prec = 40
        return km * attenuation + connectors * connector_loss + splices * splice_loss + extra


def asymmetric_loss(percent, excess=0, manufacturer_loss=None):
    percent = nonnegative(percent)
    if not 0 < percent < 100:
        raise ValueError('A proporção deve estar entre 0 e 100%.')
    excess = nonnegative(excess)
    if manufacturer_loss is not None:
        return nonnegative(manufacturer_loss)
    with localcontext() as context:
        context.prec = 40
        return -Decimal(10) * (percent / 100).log10() + excess
