# 🏋️ Mi Progreso de Gimnasio

Aplicación web para registrar el progreso de entrenamiento a lo largo del tiempo, visualizarlo en un dashboard, recibir recomendaciones automáticas basadas en el análisis de tendencias, y proyectar si las metas fijadas son alcanzables según el ritmo de progreso real del usuario.

## Problema que resuelve

Según la Encuesta Nacional de Actividad Física y Deporte 2024 (Ministerio del Deporte de Chile), solo un 44,9% de los adultos chilenos cumple con la recomendación de actividad física de la OMS. Mantener la constancia es uno de los mayores desafíos para quienes entrenan. Esta app busca sostener el hábito mediante el registro sistemático del progreso y retroalimentación basada en datos propios, no en supuestos genéricos.

## Funcionalidades

- ➕ **Registro de entrenamientos**: ejercicio, series, repeticiones, peso utilizado y percepción de esfuerzo (RPE).
- ⚖️ **Registro de métricas corporales**: peso y % de grasa corporal.
- 🎯 **Metas a corto/mediano plazo**, con vínculo opcional a un ejercicio y peso objetivo específico.
- 📋 **Historial completo** de todos los registros.
- 📊 **Dashboard**: progresión por ejercicio, volumen de entrenamiento, frecuencia semanal y evolución corporal.
- 💡 **Motor de recomendaciones**: detecta progreso sostenido, estancamiento (plateau) y falta de constancia, con sugerencias accionables.
- 📈 **Estimación de viabilidad de metas**: proyecta, mediante regresión lineal sobre tu propio historial, si vas a alcanzar tu meta antes de la fecha límite.

## Tecnologías

- **Python** + **Streamlit** — interfaz web
- **SQLite** — base de datos local
- **pandas / numpy** — análisis de datos y proyecciones
- **scikit-learn** — modelo base de clasificación y clustering (ver sección abajo)

## Cómo correrlo localmente

```bash
git clone <URL-de-este-repositorio>
cd <carpeta-del-repositorio>
pip install -r requirements.txt
python -m streamlit run app.py
```

La app se abre automáticamente en el navegador. La base de datos (`gym_progress.db`) se crea sola la primera vez que se ejecuta.

## Estructura del proyecto

```
├── app.py                 # Interfaz de la aplicación (Streamlit)
├── db.py                  # Capa de acceso a datos (SQLite)
├── recomendaciones.py     # Motor de recomendaciones basado en tendencias propias
├── viabilidad.py          # Estimación de viabilidad de metas (regresión lineal)
├── requirements.txt       # Dependencias del proyecto
└── .gitignore
```

## Sobre el modelo base entrenado con datos públicos

Al iniciar el proyecto no existían datos propios para entrenar un modelo (*cold-start problem*). Como solución, se entrenó un modelo base (clasificación y clustering) usando el dataset público *Gym Members Exercise Dataset* (Kaggle) — incluyendo su respectivo EDA.

Sin embargo, ese dataset depende de variables que esta app no puede capturar sin un dispositivo wearable (frecuencia cardíaca, calorías quemadas, litros de agua). Por eso, el motor de recomendaciones real (que sí está integrado en la app) se construyó analizando directamente el historial propio de cada usuario, en lugar de aplicar ese modelo externo. Esto tiene una ventaja adicional: las recomendaciones se **personalizan automáticamente** con cada nuevo registro, sin necesidad de reentrenar ningún modelo — el sistema mejora con el uso por diseño, no por un paso adicional de reentrenamiento.

## Buenas prácticas aplicadas

- Código modular (capa de datos, lógica de negocio e interfaz separadas en archivos distintos).
- `.gitignore` para no versionar la base de datos local ni archivos de entorno.
- Migraciones de base de datos seguras (los cambios de esquema no eliminan datos ya guardados).
- Lógica de negocio separada de la interfaz, y probada de forma independiente con datos simulados antes de integrarla.

## Autor

**Christian André Eriza Barraza**
Ciencia de Datos — Talento Digital (2026)
[LinkedIn](https://www.linkedin.com/in/christian-eriza-barraza-1583682a6/) · christian.eriza@gmail.com

## Próximos pasos

- Alojar la app en Streamlit Community Cloud para acceso público.
- Grabar un video técnico explicando el proyecto (YouTube).
- Incorporar más señales al motor de recomendaciones (ej. relación entre RPE y velocidad de progreso).
