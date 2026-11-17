# Próxima sesión de trabajo — Proyecto Oráculo

**Última sesión de trabajo:** 25 de agosto de 2026  
**Próxima sesión:** semana siguiente, fecha por definir  
**Objetivo principal:** completar la captura de metadatos faltantes de los partidos y dejar preparada una carga piloto de extremo a extremo.

## Contexto de la sesión

El ETL ya normaliza estadísticas de equipos, jugadores y alineaciones, pero todavía no puede construir automáticamente todo el contexto requerido por el `Pipeline`. Faltan principalmente los metadatos generales del partido y la identidad estable de los equipos.

Se trabajará únicamente con partidos finalizados. Por esta razón se acordó:

- eliminar `LIGAS.Rondas`, porque el total de jornadas aporta poco valor analítico;
- eliminar `PARTIDOS.Estado_partido` del modelo persistente;
- conservar `PARTIDOS.Ronda`, porque representa la jornada concreta del encuentro;
- conservar y capturar `PARTIDOS.Fecha_hora_utc`;
- utilizar identificadores estables de Sofascore para partidos, equipos, jugadores y entrenadores.

El recurso `official-tweets` fue descartado como fuente de `EQUIPOS.Id_equipo`: su `account.id` corresponde a una cuenta de X/Twitter y no al equipo en Sofascore.

## Resultado esperado

Al terminar la próxima sesión debería existir, para al menos un partido de prueba, información suficiente para construir automáticamente:

- el registro de `PARTIDOS`;
- los dos registros de `EQUIPOS`;
- las relaciones local y visitante en `PARTIDOS_EQUIPOS`;
- los entrenadores principal local y visitante;
- el contexto que consume el `Pipeline`.

La carga masiva y la integración definitiva con `../../main.py` quedan fuera del objetivo inmediato si primero no se valida correctamente este flujo piloto.

## Tareas prioritarias

### 1. Identificar las fuentes de metadatos del partido

Revisar la página del partido y la sección **Network** del navegador para buscar uno o más JSON que contengan:

- `EQUIPOS.Id_equipo` de local y visitante;
- `EQUIPOS.Nombre_equipo`;
- `EQUIPOS.Slug`;
- condición local o visitante;
- identificador del partido, como validación adicional.

Evaluar las alternativas en este orden:

1. interceptar un JSON de Sofascore que entregue ambos equipos y sus IDs;
2. reutilizar otro JSON ya descargado que contenga los mismos IDs de equipo;
3. extraer los datos desde el HTML o estado embebido de la página;
4. recurrir a scraping manual de elementos visibles solo si no existe una fuente estructurada estable.

**Criterio de término:** encontrar una fuente reproducible que permita relacionar inequívocamente el equipo local y el visitante con sus IDs de Sofascore. Probarla en más de un partido antes de incorporarla al scraper.

### 2. Modificar el scraping de metadatos generales

Capturar desde la página del partido:

- `PARTIDOS.Fecha_hora_utc`;
- `PARTIDOS.Goles_local`;
- `PARTIDOS.Goles_visita`.

Consideraciones:

- convertir la fecha a UTC antes de persistirla;
- conservar `NULL` cuando un valor realmente no esté disponible y no sustituirlo automáticamente por cero;
- verificar que el marcador corresponda al resultado final y no al descanso, penales u otro periodo;
- validar que el partido esté finalizado durante el scraping, aunque el estado no se almacene en la base;
- evitar depender exclusivamente de textos traducidos o selectores visuales frágiles si existe un timestamp o dato estructurado.

**Criterio de término:** generar un JSON de prueba con fecha UTC y marcador final correctos para al menos dos partidos.

### 3. Interceptar y guardar el JSON de managers

Agregar la captura del recurso que entrega `homeManager` y `awayManager`.

El ejemplo validado contiene:

- `homeManager.id` y `awayManager.id`: identificadores externos de Sofascore;
- `name`: nombre completo;
- `shortName`: nombre abreviado;
- `slug`: identificador textual;
- `fieldTranslations`: traducciones opcionales que no son necesarias para la primera versión.

Este recurso **sí sirve** para asociar el entrenador principal a cada lado del partido. La posición `homeManager` o `awayManager` determina el equipo a través de `PARTIDOS_EQUIPOS`, una vez resueltos los IDs de ambos equipos.

**Criterio de término:** descargar el JSON con un nombre de archivo consistente, conservar el JSON crudo y comprobar que ambos IDs se extraen correctamente. El scraper debe tolerar que uno de los dos managers no venga informado.

### 4. Resolver el alcance del modelo de entrenadores

El JSON de managers informa entrenadores principales, no un cuerpo técnico completo. Para la primera implementación se propone una de estas dos alternativas:

- mantener `CUERPO_TECNICO_PARTIDO` y registrar `Rol = "Entrenador principal"`;
- renombrar o rediseñar la entidad como `ENTRENADORES_PARTIDO` para representar exactamente lo que entrega la fuente.

Decidirlo antes de modificar el esquema. No almacenar las traducciones del nombre en esta etapa.

Campos mínimos propuestos:

- `Id_partido`;
- `Id_equipo`;
- `Id_tecnico` o `Id_entrenador`;
- `Nombre_tecnico` o `Nombre_entrenador`;
- `Nombre_corto`;
- `Slug`;
- `Rol`, únicamente si se conserva el modelo genérico de cuerpo técnico.

**Criterio de término:** dejar documentado el nombre definitivo de la entidad, su clave primaria y su relación con `PARTIDOS_EQUIPOS`.

### 5. Actualizar el modelo acordado

Modificar el esquema y la documentación para:

- eliminar `LIGAS.Rondas`;
- eliminar `PARTIDOS.Estado_partido`;
- incorporar la entidad elegida para entrenadores;
- mantener `PARTIDOS.Ronda` y `PARTIDOS.Fecha_hora_utc`;
- revisar el orden de carga y las claves de conflicto en `../../etl/loader.py`.

Como la base todavía no está poblada, se puede regenerar durante el desarrollo, pero cualquier operación sobre el archivo existente debe confirmar previamente que no contiene información que se quiera conservar.

**Criterio de término:** el esquema creado desde cero debe coincidir con la documentación y pasar una comprobación de claves foráneas.

### 6. Construir automáticamente el contexto del Pipeline

Usar los datos capturados para formar:

- liga y temporada;
- partido;
- equipos local y visitante;
- `id_equipo_local` e `id_equipo_visita`;
- relaciones de `PARTIDOS_EQUIPOS`;
- datos de managers, si se incorporan al mismo ciclo de carga.

**Criterio de término:** el contexto no debe requerir IDs de equipo escritos manualmente ni inferir localía a partir del orden de los slugs de la URL.

### 7. Ejecutar una carga piloto y auditarla

Procesar primero uno o dos partidos y comprobar:

- ausencia de duplicados;
- consistencia entre los IDs de equipo de todos los recursos;
- exactamente un local y un visitante por partido;
- fecha almacenada en UTC;
- marcador correcto;
- entrenador asociado al equipo correcto;
- claves foráneas válidas;
- columnas inesperadamente nulas.

**Criterio de término:** obtener una carga transaccional repetible e idempotente para el conjunto piloto.

## Orden sugerido para la sesión

1. Inspeccionar **Network** y localizar el JSON con los equipos.
2. Confirmar los IDs en dos partidos diferentes.
3. Capturar fecha, marcador y managers.
4. Guardar ejemplos crudos de cada recurso.
5. Adaptar el scraper.
6. Ajustar esquema, procesadores y loader.
7. Ejecutar y auditar la carga piloto.

## Datos que deben conservarse como evidencia

Para cada nuevo recurso se debe registrar:

- URL o patrón del endpoint;
- método HTTP y parámetros relevantes;
- ejemplo de respuesta cruda;
- partido del que fue obtenido;
- significado de cada campo utilizado;
- comportamiento cuando el recurso o algún campo no está disponible.

## Fuera de alcance para esta sesión

- carga histórica completa;
- entrenamiento de modelos de machine learning;
- análisis de tweets;
- implementación completa de ausencias;
- automatización avanzada de reintentos y monitoreo;
- interfaz de usuario o visualizaciones.

Estas materias permanecen en `IDEAS_FUTURAS.md` hasta que sean priorizadas.
