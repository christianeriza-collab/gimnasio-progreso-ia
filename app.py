"""
app.py - App de progreso de gimnasio (Fase 1: captura de datos + Fase 2: dashboard)

Correr con: streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

import db
import recomendaciones as rec
import viabilidad as viab

st.set_page_config(page_title="Mi Progreso de Gimnasio", page_icon="🏋️", layout="wide")

db.init_db()

st.title("🏋️ Mi Progreso de Gimnasio")
st.caption("Fase 1: registra tus entrenamientos, métricas corporales y metas.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "➕ Entrenamiento",
        "⚖️ Métricas corporales",
        "🎯 Metas",
        "📋 Historial",
        "📊 Dashboard",
        "💡 Recomendaciones",
    ]
)

# --- TAB 1: Registrar entrenamiento ---
with tab1:
    st.subheader("Registrar entrenamiento")

    ejercicios_previos = db.obtener_ejercicios_unicos()

    with st.form("form_entrenamiento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today())
            if ejercicios_previos:
                ejercicio_sel = st.selectbox(
                    "Ejercicio", options=["-- nuevo ejercicio --"] + ejercicios_previos
                )
                if ejercicio_sel == "-- nuevo ejercicio --":
                    ejercicio = st.text_input("Nombre del nuevo ejercicio")
                else:
                    ejercicio = ejercicio_sel
            else:
                ejercicio = st.text_input("Ejercicio (ej. Sentadilla, Banco plano)")
            series = st.number_input("Series", min_value=1, max_value=20, value=3, step=1)
        with col2:
            repeticiones = st.number_input(
                "Repeticiones por serie", min_value=1, max_value=100, value=10, step=1
            )
            peso_kg = st.number_input(
                "Peso utilizado (kg)", min_value=0.0, max_value=500.0, value=20.0, step=0.5
            )
            rpe = st.slider(
                "Percepción de esfuerzo (RPE, opcional)",
                min_value=0, max_value=10, value=0,
                help="0 = no registrar, 1 = muy fácil, 10 = esfuerzo máximo",
            )

        notas = st.text_area("Notas (opcional)")

        submitted = st.form_submit_button("Guardar entrenamiento")
        if submitted:
            if not ejercicio:
                st.error("Debes indicar el nombre del ejercicio.")
            else:
                db.agregar_entrenamiento(
                    fecha=fecha.isoformat(),
                    ejercicio=ejercicio.strip(),
                    series=int(series),
                    repeticiones=int(repeticiones),
                    peso_kg=float(peso_kg),
                    rpe=int(rpe) if rpe > 0 else None,
                    notas=notas.strip(),
                )
                st.success(f"Entrenamiento de '{ejercicio}' guardado ✅")
                st.rerun()

# --- TAB 2: Métricas corporales ---
with tab2:
    st.subheader("Registrar métrica corporal")

    with st.form("form_metrica", clear_on_submit=True):
        fecha_m = st.date_input("Fecha", value=date.today(), key="fecha_metrica")
        peso_corporal = st.number_input(
            "Peso corporal (kg)", min_value=0.0, max_value=300.0, value=70.0, step=0.1
        )
        grasa_pct = st.number_input(
            "% de grasa corporal (opcional, 0 = no registrar)",
            min_value=0.0, max_value=60.0, value=0.0, step=0.1,
        )
        notas_m = st.text_area("Notas (opcional)", key="notas_metrica")

        submitted_m = st.form_submit_button("Guardar métrica")
        if submitted_m:
            db.agregar_metrica(
                fecha=fecha_m.isoformat(),
                peso_kg=float(peso_corporal),
                grasa_pct=float(grasa_pct) if grasa_pct > 0 else None,
                notas=notas_m.strip(),
            )
            st.success("Métrica corporal guardada ✅")
            st.rerun()

# --- TAB 3: Metas ---
with tab3:
    st.subheader("Definir una nueva meta")

    ejercicios_para_metas = db.obtener_ejercicios_unicos()

    with st.form("form_meta", clear_on_submit=True):
        descripcion = st.text_input("Descripción de la meta (ej. 'Sentadilla 80kg x5')")
        tipo = st.selectbox("Plazo", options=["Corto plazo", "Mediano plazo"])
        fecha_objetivo = st.date_input("Fecha objetivo")

        st.caption(
            "Opcional: vincula esta meta a un ejercicio y un peso objetivo para que "
            "la app pueda estimar si es alcanzable según tu ritmo de progreso actual."
        )
        ejercicio_relacionado_sel = st.selectbox(
            "Ejercicio relacionado (opcional)",
            options=["-- ninguno --"] + ejercicios_para_metas,
        )
        peso_objetivo_kg = st.number_input(
            "Peso objetivo (kg) — solo si vinculaste un ejercicio",
            min_value=0.0, max_value=500.0, value=0.0, step=0.5,
        )

        submitted_meta = st.form_submit_button("Guardar meta")
        if submitted_meta:
            if not descripcion:
                st.error("Describe tu meta antes de guardar.")
            else:
                ejercicio_final = (
                    ejercicio_relacionado_sel if ejercicio_relacionado_sel != "-- ninguno --" else None
                )
                peso_final = peso_objetivo_kg if (ejercicio_final and peso_objetivo_kg > 0) else None
                db.agregar_meta(
                    descripcion.strip(), tipo, fecha_objetivo.isoformat(),
                    ejercicio_relacionado=ejercicio_final, peso_objetivo_kg=peso_final,
                )
                st.success("Meta guardada 🎯")
                st.rerun()

    st.divider()
    st.subheader("Mis metas")

    metas = db.obtener_metas()
    entrenamientos_para_viabilidad = db.obtener_entrenamientos()

    if not metas:
        st.info("Todavía no has definido ninguna meta.")
    else:
        for meta in metas:
            col1, col2, col3 = st.columns([3, 1, 1])
            estado_emoji = "✅" if meta["estado"] == "cumplida" else "⏳"
            with col1:
                st.write(
                    f"{estado_emoji} **{meta['descripcion']}** — {meta['tipo']} "
                    f"(objetivo: {meta['fecha_objetivo']})"
                )
                if meta["estado"] != "cumplida":
                    diagnostico = viab.estimar_viabilidad(meta, entrenamientos_para_viabilidad)
                    icono_viabilidad = {
                        "viable": "✅",
                        "en_riesgo": "⚠️",
                        "estancado": "🛑",
                        "cumplida": "🎉",
                        "datos_insuficientes": "📋",
                        "sin_datos": "📋",
                        "sin_vinculo": "ℹ️",
                        "proyeccion": "📈",
                    }.get(diagnostico["tipo"], "ℹ️")
                    st.caption(f"{icono_viabilidad} {diagnostico['mensaje']}")
            with col2:
                if meta["estado"] != "cumplida":
                    if st.button("Marcar cumplida", key=f"cumplir_{meta['id']}"):
                        db.marcar_meta_cumplida(meta["id"])
                        st.rerun()
            with col3:
                if st.button("Eliminar", key=f"eliminar_{meta['id']}"):
                    db.eliminar_meta(meta["id"])
                    st.rerun()

# --- TAB 4: Historial ---
with tab4:
    st.subheader("Historial de entrenamientos")
    entrenamientos = db.obtener_entrenamientos()
    if entrenamientos:
        df_entrenamientos = pd.DataFrame(entrenamientos)
        st.dataframe(df_entrenamientos, use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no has registrado entrenamientos.")

    st.subheader("Historial de métricas corporales")
    metricas = db.obtener_metricas()
    if metricas:
        df_metricas = pd.DataFrame(metricas)
        st.dataframe(df_metricas, use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no has registrado métricas corporales.")

# --- TAB 5: Dashboard ---
with tab5:
    st.subheader("📊 Dashboard de progreso")

    entrenamientos = db.obtener_entrenamientos()
    metricas = db.obtener_metricas()
    metas = db.obtener_metas()

    if not entrenamientos and not metricas:
        st.info(
            "Todavía no tienes datos suficientes. Registra al menos un "
            "entrenamiento o una métrica corporal para ver tu dashboard."
        )
    else:
        # --- KPIs resumen ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Entrenamientos registrados", len(entrenamientos))

        with col2:
            dias_activos = len({e["fecha"] for e in entrenamientos}) if entrenamientos else 0
            st.metric("Días de entrenamiento", dias_activos)

        with col3:
            if metricas:
                df_m_temp = pd.DataFrame(metricas).sort_values("fecha")
                peso_inicial = df_m_temp.iloc[0]["peso_kg"]
                peso_actual = df_m_temp.iloc[-1]["peso_kg"]
                delta = round(peso_actual - peso_inicial, 1)
                st.metric("Peso corporal actual", f"{peso_actual} kg", delta=f"{delta:+.1f} kg")
            else:
                st.metric("Peso corporal actual", "Sin datos")

        with col4:
            cumplidas = sum(1 for m in metas if m["estado"] == "cumplida")
            st.metric("Metas cumplidas", f"{cumplidas}/{len(metas)}" if metas else "0/0")

        st.divider()

        # --- Progresión por ejercicio ---
        if entrenamientos:
            st.subheader("Progresión por ejercicio")

            df_e = pd.DataFrame(entrenamientos)
            df_e["fecha"] = pd.to_datetime(df_e["fecha"])

            ejercicios_dash = sorted(df_e["ejercicio"].unique())
            ejercicio_sel = st.selectbox("Elige un ejercicio", options=ejercicios_dash, key="dash_ejercicio")

            df_ej = df_e[df_e["ejercicio"] == ejercicio_sel].copy()
            df_ej["volumen"] = df_ej["series"] * df_ej["repeticiones"] * df_ej["peso_kg"]

            # "Mejor" (máximo) peso registrado por día, y volumen total de ese día
            progreso_peso = df_ej.groupby("fecha")["peso_kg"].max().sort_index()
            progreso_volumen = df_ej.groupby("fecha")["volumen"].sum().sort_index()

            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"Peso máximo por sesión — {ejercicio_sel}")
                st.line_chart(progreso_peso)
            with col_b:
                st.caption(f"Volumen de entrenamiento por sesión — {ejercicio_sel}")
                st.bar_chart(progreso_volumen)

            st.divider()

            # --- Volumen total y frecuencia (todos los ejercicios) ---
            st.subheader("Actividad general de entrenamiento")

            df_e["volumen"] = df_e["series"] * df_e["repeticiones"] * df_e["peso_kg"]
            df_e["semana"] = df_e["fecha"].dt.to_period("W").apply(lambda p: p.start_time)

            volumen_semanal = df_e.groupby("semana")["volumen"].sum()
            frecuencia_semanal = df_e.groupby("semana")["fecha"].nunique()

            col_c, col_d = st.columns(2)
            with col_c:
                st.caption("Volumen total de entrenamiento por semana")
                st.bar_chart(volumen_semanal)
            with col_d:
                st.caption("Días de entrenamiento por semana")
                st.bar_chart(frecuencia_semanal)

            st.divider()

        # --- Métricas corporales ---
        if metricas:
            st.subheader("Evolución de métricas corporales")

            df_m = pd.DataFrame(metricas)
            df_m["fecha"] = pd.to_datetime(df_m["fecha"])
            df_m = df_m.sort_values("fecha")

            col_e, col_f = st.columns(2)
            with col_e:
                st.caption("Peso corporal (kg)")
                st.line_chart(df_m.set_index("fecha")["peso_kg"])
            with col_f:
                st.caption("% de grasa corporal")
                if df_m["grasa_pct"].notna().any():
                    st.line_chart(df_m.set_index("fecha")["grasa_pct"].dropna())
                else:
                    st.info("Aún no has registrado % de grasa corporal.")

            st.divider()

        # --- Resumen de metas ---
        if metas:
            st.subheader("Resumen de metas")

            hoy = date.today()
            filas = []
            for m in metas:
                fecha_obj = pd.to_datetime(m["fecha_objetivo"]).date() if m["fecha_objetivo"] else None
                dias_restantes = (fecha_obj - hoy).days if fecha_obj else None
                filas.append(
                    {
                        "Meta": m["descripcion"],
                        "Plazo": m["tipo"],
                        "Fecha objetivo": m["fecha_objetivo"],
                        "Estado": m["estado"],
                        "Días restantes": dias_restantes if m["estado"] != "cumplida" else "—",
                    }
                )
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

# --- TAB 6: Recomendaciones ---
with tab6:
    st.subheader("💡 Recomendaciones")
    st.caption(
        "Análisis de tendencias basado en tus propios registros: progreso, "
        "estancamiento y constancia."
    )

    entrenamientos_rec = db.obtener_entrenamientos()
    metas_rec = db.obtener_metas()

    recomendaciones = rec.generar_recomendaciones(entrenamientos_rec, metas_rec)

    render_por_tipo = {
        "positivo": st.success,
        "alerta": st.warning,
        "info": st.info,
    }

    for r in recomendaciones:
        funcion_render = render_por_tipo.get(r["tipo"], st.info)
        funcion_render(f"{r['icono']} {r['mensaje']}")
