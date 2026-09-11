"""
viabilidad.py - Estimación de viabilidad de metas (Fase 5)

Para metas vinculadas a un ejercicio y un peso objetivo, proyecta si el
ritmo de progreso actual del usuario le permitirá alcanzar la meta antes
de la fecha límite, usando una regresión lineal simple sobre su propio
historial (peso máximo por sesión a lo largo del tiempo).
"""

import numpy as np
import pandas as pd

MIN_SESIONES_PARA_PROYECTAR = 3


def estimar_viabilidad(meta, entrenamientos):
    """
    meta: dict (formato de db.obtener_metas()), con posibles claves
          'ejercicio_relacionado' y 'peso_objetivo_kg'.
    entrenamientos: lista de dicts (formato de db.obtener_entrenamientos()).

    Devuelve un dict {tipo, mensaje}.
    """
    ejercicio = meta.get("ejercicio_relacionado")
    objetivo = meta.get("peso_objetivo_kg")

    if not ejercicio or not objetivo:
        return {
            "tipo": "sin_vinculo",
            "mensaje": (
                "Esta meta no está vinculada a un ejercicio y peso objetivo, "
                "así que no se puede proyectar automáticamente."
            ),
        }

    if not entrenamientos:
        return {
            "tipo": "sin_datos",
            "mensaje": f"Aún no tienes registros de {ejercicio} para proyectar esta meta.",
        }

    df = pd.DataFrame(entrenamientos)
    df_ej = df[df["ejercicio"] == ejercicio].copy()

    if df_ej.empty:
        return {
            "tipo": "sin_datos",
            "mensaje": f"Aún no tienes registros de {ejercicio} para proyectar esta meta.",
        }

    df_ej["fecha"] = pd.to_datetime(df_ej["fecha"])
    serie = df_ej.groupby("fecha")["peso_kg"].max().sort_index()

    if len(serie) < MIN_SESIONES_PARA_PROYECTAR:
        return {
            "tipo": "datos_insuficientes",
            "mensaje": (
                f"Necesitas al menos {MIN_SESIONES_PARA_PROYECTAR} sesiones de "
                f"{ejercicio} para proyectar esta meta (llevas {len(serie)})."
            ),
        }

    peso_actual = float(serie.iloc[-1])
    if peso_actual >= objetivo:
        return {
            "tipo": "cumplida",
            "mensaje": (
                f"¡Ya alcanzaste o superaste tu objetivo de {objetivo:.1f} kg en "
                f"{ejercicio}! Considera marcar esta meta como cumplida."
            ),
        }

    # Regresión lineal: peso_kg en función de los días desde la primera sesión.
    dias = (serie.index - serie.index[0]).days.values.astype(float)
    pesos = serie.values.astype(float)
    pendiente_dia, _intercepto = np.polyfit(dias, pesos, 1)
    pendiente_semana = pendiente_dia * 7

    if pendiente_dia <= 0:
        return {
            "tipo": "estancado",
            "mensaje": (
                f"Tu ritmo actual en {ejercicio} es plano o negativo (no ha subido "
                f"en tu historial reciente), así que con la tendencia actual no "
                f"vas a alcanzar {objetivo:.1f} kg. Revisa la pestaña de "
                f"Recomendaciones para ajustar tu estrategia antes de que esta "
                f"proyección tenga sentido."
            ),
        }

    kg_faltantes = objetivo - peso_actual
    dias_estimados = kg_faltantes / pendiente_dia
    fecha_proyectada = serie.index[-1] + pd.Timedelta(days=dias_estimados)

    fecha_objetivo = pd.to_datetime(meta["fecha_objetivo"]) if meta.get("fecha_objetivo") else None

    if fecha_objetivo is None:
        return {
            "tipo": "proyeccion",
            "mensaje": (
                f"A tu ritmo actual (~{pendiente_semana:.2f} kg/semana), deberías "
                f"alcanzar {objetivo:.1f} kg en {ejercicio} alrededor del "
                f"{fecha_proyectada.date()}."
            ),
        }

    if fecha_proyectada.date() <= fecha_objetivo.date():
        return {
            "tipo": "viable",
            "mensaje": (
                f"Vas bien encaminado: a tu ritmo actual (~{pendiente_semana:.2f} "
                f"kg/semana), deberías alcanzar {objetivo:.1f} kg en {ejercicio} "
                f"alrededor del {fecha_proyectada.date()}, antes de tu fecha "
                f"objetivo ({fecha_objetivo.date()})."
            ),
        }

    semanas_extra = (fecha_proyectada.date() - fecha_objetivo.date()).days / 7
    return {
        "tipo": "en_riesgo",
        "mensaje": (
            f"A tu ritmo actual (~{pendiente_semana:.2f} kg/semana), proyecto que "
            f"alcanzarías {objetivo:.1f} kg en {ejercicio} recién el "
            f"{fecha_proyectada.date()} — unas {semanas_extra:.1f} semanas después "
            f"de tu fecha objetivo ({fecha_objetivo.date()}). Considera aumentar la "
            f"frecuencia o intensidad, o ajustar la fecha objetivo."
        ),
    }
