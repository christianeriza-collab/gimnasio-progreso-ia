"""
db.py - Capa de acceso a datos para la app de progreso de gimnasio.
Usa SQLite como motor de base de datos (Fase 1 del proyecto).
"""

import sqlite3
from contextlib import contextmanager
from datetime import date

DB_PATH = "gym_progress.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen. Se debe llamar al iniciar la app."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entrenamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                ejercicio TEXT NOT NULL,
                series INTEGER NOT NULL,
                repeticiones INTEGER NOT NULL,
                peso_kg REAL NOT NULL,
                rpe INTEGER,
                notas TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metricas_corporales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                peso_kg REAL NOT NULL,
                grasa_pct REAL,
                notas TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                tipo TEXT NOT NULL,
                fecha_objetivo TEXT,
                estado TEXT NOT NULL DEFAULT 'en progreso',
                fecha_creacion TEXT NOT NULL,
                ejercicio_relacionado TEXT,
                peso_objetivo_kg REAL
            )
        """)
        conn.commit()
        _migrar_columnas_metas(conn)


def _migrar_columnas_metas(conn):
    """
    Agrega columnas nuevas a bases de datos creadas con una versión anterior
    del esquema (Fase 1-4), sin perder los datos ya guardados.
    """
    columnas_existentes = {row["name"] for row in conn.execute("PRAGMA table_info(metas)").fetchall()}
    if "ejercicio_relacionado" not in columnas_existentes:
        conn.execute("ALTER TABLE metas ADD COLUMN ejercicio_relacionado TEXT")
    if "peso_objetivo_kg" not in columnas_existentes:
        conn.execute("ALTER TABLE metas ADD COLUMN peso_objetivo_kg REAL")
    conn.commit()


# ---- Entrenamientos ----

def agregar_entrenamiento(fecha, ejercicio, series, repeticiones, peso_kg, rpe=None, notas=""):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO entrenamientos (fecha, ejercicio, series, repeticiones, peso_kg, rpe, notas)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (fecha, ejercicio, series, repeticiones, peso_kg, rpe, notas),
        )
        conn.commit()


def obtener_entrenamientos():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM entrenamientos ORDER BY fecha DESC").fetchall()
        return [dict(r) for r in rows]


def obtener_ejercicios_unicos():
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT ejercicio FROM entrenamientos ORDER BY ejercicio").fetchall()
        return [r["ejercicio"] for r in rows]


# ---- Métricas corporales ----

def agregar_metrica(fecha, peso_kg, grasa_pct=None, notas=""):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO metricas_corporales (fecha, peso_kg, grasa_pct, notas)
               VALUES (?, ?, ?, ?)""",
            (fecha, peso_kg, grasa_pct, notas),
        )
        conn.commit()


def obtener_metricas():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM metricas_corporales ORDER BY fecha DESC").fetchall()
        return [dict(r) for r in rows]


# ---- Metas ----

def agregar_meta(descripcion, tipo, fecha_objetivo, ejercicio_relacionado=None, peso_objetivo_kg=None):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO metas (descripcion, tipo, fecha_objetivo, estado, fecha_creacion,
                                   ejercicio_relacionado, peso_objetivo_kg)
               VALUES (?, ?, ?, 'en progreso', ?, ?, ?)""",
            (descripcion, tipo, fecha_objetivo, date.today().isoformat(),
             ejercicio_relacionado, peso_objetivo_kg),
        )
        conn.commit()


def obtener_metas():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM metas ORDER BY fecha_objetivo ASC").fetchall()
        return [dict(r) for r in rows]


def marcar_meta_cumplida(meta_id):
    with get_connection() as conn:
        conn.execute("UPDATE metas SET estado = 'cumplida' WHERE id = ?", (meta_id,))
        conn.commit()


def eliminar_meta(meta_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
        conn.commit()
