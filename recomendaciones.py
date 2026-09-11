"""
recomendaciones.py - Motor de recomendaciones (Fase 4)

Analiza los datos propios del usuario (entrenamientos, métricas, metas) para
generar recomendaciones accionables, sin depender de variables que la app no
captura (frecuencia cardíaca, calorías, etc.).

Reglas implementadas:
  1. Progreso / estancamiento (plateau) por ejercicio, según el peso máximo
     levantado por sesión.
  2. Alerta de constancia si han pasado muchos días desde el último registro.
  3. Conexión simple entre un ejercicio estancado y una meta activa relacionada.
"""

from datetime import date

import pandas as pd

DIAS_ALERTA_INACTIVIDAD = 7
MIN_SESIONES_PARA_TENDENCIA = 3
VENTANA_TENDENCIA = 4


def analizar_progreso_ejercicio(serie_pesos):
    """
    Recibe una pandas.Series de peso máximo por sesión (indexada por fecha,
    ordenada cronológicamente) para UN ejercicio, y devuelve un diagnóstico.
    """
    n = len(serie_pesos)

    if n < MIN_SESIONES_PARA_TENDENCIA:
        return {
            "estado": "insuficiente",
            "n_sesiones": n,
        }

    valores = serie_pesos.values
    ultimo = float(valores[-1])
    maximo_previo = float(valores[:-1].max())
    maximo_historico = float(valores.max())
    primera_sesion = float(valores[0])

    ventana = valores[-VENTANA_TENDENCIA:] if n >= VENTANA_TENDENCIA else valores
    incrementos = sum(1 for i in range(1, len(ventana)) if ventana[i] > ventana[i - 1])

    if ultimo > maximo_previo:
        estado = "progreso"
    elif incrementos == 0:
        estado = "estancado"
    else:
        estado = "variable"

    return {
        "estado": estado,
        "n_sesiones": n,
        "ultimo_peso": ultimo,
        "maximo_historico": maximo_historico,
        "primera_sesion_peso": primera_sesion,
    }


def analizar_frecuencia(fechas_entrenamiento, hoy=None):
    """
    Recibe una lista/serie de fechas (strings o date) de todas las sesiones
    registradas y evalúa si ha pasado demasiado tiempo desde la última.
    """
    if hoy is None:
        hoy = date.today()

    if len(fechas_entrenamiento) == 0:
        return {"alerta": False, "dias_desde_ultimo": None, "ultima_fecha": None}

    fechas = sorted(pd.to_datetime(pd.Series(list(fechas_entrenamiento))).dt.date.unique())
    ultima_fecha = fechas[-1]
    dias_desde_ultimo = (hoy - ultima_fecha).days

    return {
        "alerta": dias_desde_ultimo >= DIAS_ALERTA_INACTIVIDAD,
        "dias_desde_ultimo": dias_desde_ultimo,
        "ultima_fecha": ultima_fecha.isoformat(),
    }


def _mensaje_progreso_ejercicio(ejercicio, diag):
    estado = diag["estado"]

    if estado == "insuficiente":
        return {
            "tipo": "info",
            "icono": "📋",
            "ejercicio": ejercicio,
            "mensaje": (
                f"Todavía tienes pocos registros de **{ejercicio}** "
                f"({diag['n_sesiones']} sesión/es). Necesitas al menos "
                f"{MIN_SESIONES_PARA_TENDENCIA} para poder analizar tu tendencia."
            ),
        }

    if estado == "progreso":
        return {
            "tipo": "positivo",
            "icono": "📈",
            "ejercicio": ejercicio,
            "mensaje": (
                f"¡Vas mejorando en **{ejercicio}**! Tu último registro "
                f"({diag['ultimo_peso']:.1f} kg) es tu nuevo máximo histórico. "
                f"Sugerencia: la próxima sesión sube la carga entre un 2,5% y un 5%, "
                f"o agrega una repetición extra antes de subir peso."
            ),
        }

    if estado == "estancado":
        return {
            "tipo": "alerta",
            "icono": "⚠️",
            "ejercicio": ejercicio,
            "mensaje": (
                f"Tu peso en **{ejercicio}** no ha subido en tus últimas sesiones "
                f"(rondando los {diag['ultimo_peso']:.1f} kg). Esto puede ser una "
                f"meseta (plateau). Sugerencias: varía el rango de repeticiones, "
                f"prueba una variante del ejercicio, o considera una semana de "
                f"descarga (menos volumen/intensidad) antes de retomar el aumento de carga."
            ),
        }

    # estado == "variable"
    return {
        "tipo": "info",
        "icono": "🔄",
        "ejercicio": ejercicio,
        "mensaje": (
            f"Tu progreso en **{ejercicio}** ha sido irregular últimamente. "
            f"Revisa la consistencia de tu descanso, técnica y alimentación "
            f"antes de forzar más carga."
        ),
    }


def _mensaje_frecuencia(diag_frecuencia):
    if not diag_frecuencia["alerta"]:
        return None
    return {
        "tipo": "alerta",
        "icono": "📅",
        "ejercicio": None,
        "mensaje": (
            f"Han pasado {diag_frecuencia['dias_desde_ultimo']} días desde tu "
            f"último entrenamiento registrado ({diag_frecuencia['ultima_fecha']}). "
            f"La constancia es clave para el progreso — intenta retomar pronto."
        ),
    }


def _conexion_con_metas(ejercicio, diag, metas):
    """Vínculo simple (coincidencia de texto) entre un ejercicio estancado y una meta activa."""
    if diag["estado"] != "estancado":
        return None

    ejercicio_lower = ejercicio.lower()
    for meta in metas:
        if meta["estado"] == "cumplida":
            continue
        if ejercicio_lower in meta["descripcion"].lower():
            return {
                "tipo": "alerta",
                "icono": "🎯",
                "ejercicio": ejercicio,
                "mensaje": (
                    f"Esto es relevante para tu meta activa **\"{meta['descripcion']}\"** "
                    f"(objetivo: {meta['fecha_objetivo']}). Con el estancamiento actual, "
                    f"quizás necesites ajustar tu enfoque en este ejercicio para alcanzarla a tiempo."
                ),
            }
    return None


def generar_recomendaciones(entrenamientos, metas, hoy=None):
    """
    Punto de entrada principal.

    entrenamientos: lista de dicts (igual formato que devuelve db.obtener_entrenamientos()).
    metas: lista de dicts (igual formato que devuelve db.obtener_metas()).

    Devuelve una lista de recomendaciones (dicts con tipo, icono, ejercicio, mensaje).
    """
    recomendaciones = []

    if not entrenamientos:
        return [{
            "tipo": "info",
            "icono": "👋",
            "ejercicio": None,
            "mensaje": "Registra tu primer entrenamiento para empezar a recibir recomendaciones.",
        }]

    df = pd.DataFrame(entrenamientos)
    df["fecha"] = pd.to_datetime(df["fecha"])

    # --- Frecuencia / constancia ---
    diag_frecuencia = analizar_frecuencia(df["fecha"], hoy=hoy)
    msg_frecuencia = _mensaje_frecuencia(diag_frecuencia)
    if msg_frecuencia:
        recomendaciones.append(msg_frecuencia)

    # --- Progreso por ejercicio ---
    for ejercicio in sorted(df["ejercicio"].unique()):
        serie = df[df["ejercicio"] == ejercicio].groupby("fecha")["peso_kg"].max().sort_index()
        diag = analizar_progreso_ejercicio(serie)
        recomendaciones.append(_mensaje_progreso_ejercicio(ejercicio, diag))

        conexion = _conexion_con_metas(ejercicio, diag, metas)
        if conexion:
            recomendaciones.append(conexion)

    return recomendaciones
