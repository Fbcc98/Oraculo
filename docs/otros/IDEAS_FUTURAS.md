# Ideas futuras — Proyecto Oráculo

**Creado:** 25 de agosto de 2026  
**Propósito:** conservar oportunidades de mejora que no forman parte necesariamente de la próxima sesión de programación.

Este documento funciona como una lluvia de ideas organizada. Las prioridades son preliminares y pueden cambiar después de completar el primer flujo de carga de extremo a extremo.

## Criterio preliminar de prioridad

- **Alta:** mejora necesaria para disponer de datos históricos confiables o preparar correctamente el análisis.
- **Media:** aporta robustez, trazabilidad o nuevas variables útiles, pero no bloquea el flujo básico.
- **Baja / exploratoria:** idea con valor potencial que requiere investigación o una base más madura.

## Modelo de datos

### Separar ligas y temporadas — Prioridad alta

Actualmente `LIGAS` mezcla la identidad de la competición con los atributos de una temporada concreta. Evaluar separar:

- `LIGAS`: identidad estable de la competición, nombre y país;
- `TEMPORADAS_LIGA`: temporada, ID externo de temporada y relación con la liga;
- `PARTIDOS`: relación con la temporada de la liga correspondiente.

Esto permitiría almacenar varias temporadas sin repetir conceptualmente la liga y facilitaría análisis longitudinales.

### Diseñar `AUSENCIAS_PARTIDO` — Prioridad alta

Capturar jugadores ausentes por lesión, suspensión, duda u otro motivo. La primera versión acordada no necesita `Fecha_desde` ni `Fecha_hasta`.

Antes de implementarla se debe confirmar:

- endpoint disponible y estabilidad del formato;
- presencia de `Id_jugador` e `Id_equipo`;
- catálogo o texto libre para el motivo;
- momento de disponibilidad del dato, importante para evitar fuga de información;
- tratamiento de jugadores ausentes que no existan todavía en `JUGADORES`.

### Modelar entrenadores y cuerpo técnico — Prioridad alta

Decidir si el recurso `managers` justifica una entidad específica `ENTRENADORES_PARTIDO` o si se mantiene `CUERPO_TECNICO_PARTIDO` con el rol de entrenador principal.

En una etapa posterior podría separarse:

- `TECNICOS`, como catálogo de personas;
- `TECNICOS_PARTIDO`, como relación histórica entre partido, equipo, técnico y rol.

Esto evitaría repetir el nombre y slug del mismo entrenador en todos los partidos y permitiría estudiar cambios de entrenador.

### Revisar la identidad de países — Prioridad media

Mantener `PAIS.Id_pais` como identificador interno y `Codigo_alpha3` como valor único cuando esté disponible. Definir una estrategia para países sin código, nombres alternativos y nacionalidades que no representen países reconocidos de forma estándar.

### Historial de pertenencia de equipos a competiciones — Prioridad media

Evaluar una relación explícita entre equipo y temporada de liga. No guardar una liga permanente dentro de `EQUIPOS`, porque ascensos, descensos y cambios de competición hacen que esa relación sea temporal.

### Catálogos para valores repetidos — Prioridad baja

Evaluar catálogos o restricciones para posiciones, periodos, roles técnicos y tipos de ausencia. Implementarlos solo si mejoran realmente la integridad sin volver rígido el ETL frente a valores nuevos de la fuente.

## Web scraping y adquisición de datos

### Extracción estructurada de metadatos generales — Prioridad alta

Consolidar una extracción por partido que entregue equipos, fecha, marcador, torneo, temporada y estado operativo. Preferir endpoints JSON o estado estructurado de la página por sobre selectores visuales.

### Bitácora `EXTRACCIONES` — Prioridad alta

Registrar cada recurso descargado o procesado con:

- partido;
- tipo de recurso;
- fuente;
- fecha y hora UTC de extracción;
- ruta o identificación del archivo crudo;
- versión estadística cuando exista;
- resultado, código HTTP o error.

Esta tabla facilitará reproducibilidad, auditoría y reintentos.

### Estrategia de reintentos y recuperación — Prioridad media

Agregar reintentos con espera progresiva, límites por recurso, detección de archivos incompletos y reanudación sin repetir descargas válidas.

### Validación de respuestas — Prioridad media

Definir contratos mínimos por recurso: claves requeridas, tipos esperados y comportamiento ante cambios de esquema. Conservar siempre el JSON crudo para poder reprocesar sin volver a consultar la web.

### Control de duplicados y nombres de archivos — Prioridad media

Normalizar la convención de archivos usando liga, temporada, ronda, tipo de recurso e ID del partido. Evaluar un manifiesto que permita saber qué recursos están completos para cada encuentro.

### Detección responsable de límites del sitio — Prioridad media

Controlar frecuencia, concurrencia, tiempos de espera y respuestas de bloqueo. Evitar sobrecargar la fuente y documentar cualquier restricción técnica o de uso relevante.

### Fuentes alternativas — Prioridad exploratoria

Investigar fuentes alternativas solamente para campos que no estén disponibles de manera consistente en la fuente principal. Antes de combinarlas, estudiar licencias, estabilidad, cobertura e identidad cruzada de equipos y jugadores.

### Tweets oficiales y señales externas — Prioridad exploratoria

El recurso `official-tweets` no sirve como fuente del ID de equipo de Sofascore. Podría estudiarse en el futuro para análisis de noticias, alineaciones anunciadas o sentimiento, manteniéndolo separado del modelo estadístico principal.

## ETL y calidad de datos

### Pipeline completo e idempotente — Prioridad alta

Lograr que una segunda ejecución sobre los mismos archivos no duplique registros ni produzca resultados distintos. Definir claramente qué tablas usan inserción, actualización o rechazo.

### Auditoría automática posterior a la carga — Prioridad alta

Crear controles para:

- claves foráneas;
- duplicados;
- dos equipos por partido;
- un local y un visitante;
- fechas válidas y ordenadas;
- IDs consistentes entre recursos;
- porcentajes y estadísticas fuera de rangos razonables;
- volumen y patrón de valores nulos.

### Reporte de campos desconocidos — Prioridad media

Cuando Sofascore agregue estadísticas o cambie claves, registrar los campos no reconocidos en vez de ignorarlos silenciosamente. Esto permitirá decidir posteriormente si se incorporan al modelo.

### Versionado de transformaciones — Prioridad media

Registrar la versión del esquema y del transformador usado para cada carga. Facilitar migraciones y reprocesamiento de JSON antiguos cuando cambien las reglas de normalización.

### Pruebas automatizadas con fixtures — Prioridad media

Conservar ejemplos pequeños y anonimizados o estables de cada tipo de JSON para probar procesadores, valores ausentes, periodos inesperados y cambios de estructura.

### Unidades y convenciones — Prioridad media

Documentar porcentajes, kilómetros, metros, timestamps, booleanos y valores derivados. Evitar mezclar proporciones de `0–1` con porcentajes de `0–100`.

## Machine learning y analítica

### Definir primero el objetivo predictivo — Prioridad alta para la etapa ML

Antes de seleccionar algoritmos, definir qué se quiere predecir: resultado, goles, probabilidad de victoria, rendimiento individual u otra variable. También definir el momento exacto desde el cual se realiza la predicción.

### Prevención de fuga de información — Prioridad alta para la etapa ML

Separar estrictamente variables disponibles antes del partido de estadísticas generadas durante o después del encuentro. Usar `Fecha_hora_utc` para construir particiones temporales de entrenamiento, validación y prueba.

### Construcción de características históricas — Prioridad media

Explorar variables calculadas únicamente con partidos anteriores:

- forma reciente del equipo;
- promedios móviles de goles, xG, tiros y posesión;
- rendimiento como local o visitante;
- descanso entre partidos;
- estabilidad de alineación;
- ausencias relevantes;
- cambios de entrenador;
- fuerza del rival.

### Ratings de equipos y jugadores — Prioridad media

Evaluar Elo u otros ratings actualizados cronológicamente. Compararlos contra baselines simples antes de introducir modelos complejos.

### Baselines y métricas — Prioridad media

Definir baselines reproducibles y métricas apropiadas. Para probabilidades, considerar log loss, Brier score y calibración; para goles, métricas de conteo además del error promedio.

### Interpretabilidad y monitoreo — Prioridad baja inicialmente

Explicar qué variables impulsan cada predicción, controlar deriva entre temporadas y revisar si el rendimiento cambia por liga, periodo o tipo de equipo.

## Arquitectura y mantenibilidad

### Conectar el pipeline a `../../main.py` — Prioridad alta

Integrar scraping, procesamiento y carga una vez estabilizado el flujo piloto. Mantener etapas ejecutables por separado para facilitar depuración y reprocesamiento.

### Configuración por liga y temporada — Prioridad media

Centralizar endpoints, temporadas, rondas, rutas y parámetros sin codificarlos dentro de los scrapers. Validar la configuración al inicio de cada ejecución.

### Logging estructurado — Prioridad media

Evolucionar desde mensajes libres hacia registros con partido, recurso, etapa, severidad y error. Evitar incluir contenido excesivo o sensible en los logs.

### Migraciones de base de datos — Prioridad media

Cuando la base comience a contener datos valiosos, dejar de depender de recrearla. Adoptar migraciones versionadas y copias de seguridad verificadas antes de cambios destructivos.

### Interfaz de línea de comandos — Prioridad baja

Reemplazar progresivamente el menú interactivo por comandos reproducibles para descargar, procesar, cargar, auditar y reintentar rangos concretos.

## Visualización y producto

### Panel de calidad y cobertura — Prioridad media

Mostrar partidos descargados, recursos faltantes, errores, columnas nulas y avance por liga, temporada y ronda.

### Explorador de partidos y jugadores — Prioridad baja

Crear vistas comparativas de equipos, jugadores y periodos una vez que la base tenga suficiente cobertura y calidad.

### Presentación de predicciones — Prioridad exploratoria

Si se desarrolla un modelo, mostrar probabilidades calibradas, fecha de cálculo, datos utilizados y explicación resumida. Evitar presentar una predicción como certeza.

## Seguridad, cumplimiento y operación

### Gestión de secretos y configuración local — Prioridad media

Mantener credenciales, cookies o tokens fuera del repositorio y de los logs. Documentar las variables necesarias sin publicar sus valores.

### Revisión de términos y uso responsable — Prioridad media

Revisar las condiciones de uso y restricciones aplicables antes de ampliar volumen, automatización o redistribución de datos.

### Copias de seguridad — Prioridad media

Definir una estrategia sencilla para respaldar la base y los JSON crudos, incluyendo una prueba periódica de restauración.

## Candidatos iniciales para priorización futura

Cuando termine la captura de metadatos y la carga piloto, revisar primero:

1. separación de `LIGAS` y `TEMPORADAS_LIGA`;
2. diseño e incorporación de `AUSENCIAS_PARTIDO`;
3. bitácora `EXTRACCIONES`;
4. auditoría automática de calidad;
5. pipeline idempotente conectado a `../../main.py`;
6. pruebas automatizadas con JSON de referencia;
7. definición formal del primer objetivo de machine learning.

Las demás ideas deberían permanecer en espera hasta tener datos históricos suficientes y un flujo de adquisición estable.
