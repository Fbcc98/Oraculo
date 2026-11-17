# Visión General del Proyecto

## 1. Propósito del Proyecto

El proyecto **"Oráculo"** es una iniciativa de ingeniería de software y ciencia de datos destinada a la recolección, estructuración y análisis estadístico de fútbol. Su propósito central es construir un ecosistema progresivo que evolucione desde la analítica exploratoria hasta la identificación y ejecución automatizada de apuestas con valor estadístico (*Value Bets*).

A nivel personal, este sistema responde a dos motores fundamentales:

* **Valor Práctico y Emocional (Motor Principal):** Construir de manera metódica, disciplinada y controlada una herramienta capaz de generar un respaldo financiero adicional para mi familia y seres queridos, retribuyendo el apoyo y cariño brindado en los momentos difíciles.
* **Valor Educativo (Sandbox Técnico):** Funcionar como un laboratorio práctico de aprendizaje continuo para consolidar habilidades en Ingeniería de Software, Arquitectura de Datos (*Web Scraping* con Playwright), Bases de Datos Relacionales (SQLite/SQL), Analítica Visual y *Machine Learning*.

---

## 2. Alcance

El alcance del proyecto abarca el ciclo completo de vida del dato y la toma de decisiones, estructurado en tres etapas evolutivas: **1) Extracción y Analítica Descriptiva**, **2) Modelado Predictivo y Filtrado de Cuotas**, y **3) Ejecución Autónoma Auditada**.

### a. Dentro del Alcance

1. **Extracción y Persistencia de Datos (Pipeline ETL):** Motor automatizado de *web scraping* para capturar estadísticas históricas y pre-partido desde una fuente deportiva principal, normalizándolas en una base de datos relacional (SQLite) como fuente única de verdad.
2. **Dashboards Automatizados de Exploración (Fase 1):** Herramientas locales de visualización conectadas directamente a SQLite para analizar tendencias, distribuciones y formular estrategias de mercado basadas en evidencia.
3. **Laboratorio de Machine Learning y Selección de Cuotas (Fase 2):** Entrenamiento y comparación de múltiples modelos predictivos basados en las estrategias definidas, complementados con mecanismos automatizados (incluyendo IA o reglas probabilísticas) para detectar cuotas de valor sin búsqueda manual.
4. **Automatización de Apuestas y Bitácora (Fase 3 - Condicional):** Flujo autónomo para extraer cuotas de la casa de apuestas, cruzarlas con las predicciones del modelo validado, ejecutar operaciones sobre un *bankroll* designado y registrar automáticamente cada movimiento en una bitácora de auditoría.

### b. Fuera del Alcance

Para proteger el foco del aprendizaje y evitar riesgos técnicos o financieros prematuros (*Scope Creep*), quedan excluidos del proyecto:

1. **Operación Real sin Validación Previa:** Queda estrictamente fuera del alcance activar apuestas automáticas con dinero real antes de que un modelo supere el umbral de validación de la Fase 2 ($\ge 60\%$ de acierto y $EV > 0$).
2. **Frecuencia Temporal En Vivo:** El sistema opera exclusivamente en escenarios pre-partido (*pre-match*). No contempla *scraping* ni apuestas en tiempo real (*in-play*).
3. **Arbitraje Multifuente (*Surebets*):** No incluye el monitoreo simultáneo de decenas de casas de apuestas para buscar diferencias de arbitraje.
4. **Productos Web o Móviles Comerciales:** No se desarrollará una plataforma web pública ni aplicación móvil; tanto los dashboards exploratorios como la orquestación operan en entorno local (CLI, scripts y herramientas locales de BI/Python).
5. **Predicción Especulativa sin Respaldo Estadístico:** Se excluye apostar sobre mercados sin patrón cuantitativo verificable en los datos históricos recolectados.

---

## 3. Objetivos del Proyecto

### a. Objetivo General

Desarrollar un sistema integral y evolutivo de ingeniería de datos y aprendizaje automático capaz de recolectar estadísticas de fútbol, facilitar la definición de estrategias mediante analítica exploratoria, validar modelos predictivos de alta precisión y automatizar de forma controlada y auditada la ejecución de apuestas de valor sobre un fondo designado.

### b. Objetivos Específicos

1. **Objetivo de Ingeniería de Datos y Exploración (Fase 1):** Construir un pipeline ETL confiable en SQLite que consolide las estadísticas de las ligas objetivo y alimente dashboards locales automatizados para definir la estrategia de apuesta.
2. **Objetivo de Modelado Predictivo y Eficiencia (Fase 2):** Implementar y comparar múltiples algoritmos de *Machine Learning* junto con filtros automatizados de cuotas, alcanzando al menos un **60 % de capacidad de acierto** con **Valor Esperado positivo ($EV > 0$)** en validación temporal.
3. **Objetivo de Automatización y Control de Riesgo (Fase 3):** Integrar el flujo completo de captura de cuotas, cruce predictivo y colocación autónoma de apuestas sobre el *bankroll* asignado, manteniendo una **bitácora automatizada** que audite cada resultado y detenga la operación ante desviaciones de rendimiento.