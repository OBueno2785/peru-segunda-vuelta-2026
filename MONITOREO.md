# Monitoreo recurrente del IAR (indicador adelantado)

El Índice de Aceptación en Redes es un **indicador adelantado**: su valor importa menos que su
**tendencia** en el tiempo. Por eso se re-mide periódicamente y se acumula en
`data/indice_historial.csv`, que alimenta los sparklines del dashboard.

## Qué hace cada corrida

1. **Recolectar** (web): por departamento / macro-región, buscar noticias y señales de redes
   recientes de Keiko Fujimori y Roberto Sánchez; estimar el sentimiento neto.
2. **Actualizar** la columna `net` (−1..1, + = Keiko) de `data/indice_redes.csv`. Opcional:
   alimentar `data/social_signals.csv` con métricas de social listening.
3. **Agregar el snapshot** y regenerar:
   ```bash
   python -m src.agregar_snapshot   # re-deriva IAR y agrega la fila de hoy al histórico
   python main.py                   # regenera informe.html / resultados.json
   ```
4. **Publicar**: commit y push (la tendencia queda visible en el dashboard).

## Prompt sugerido para el agente programado

> Eres el monitor del IAR de `peru-segunda-vuelta-2026`. Para cada macro-región del Perú
> (Lima/Callao, costa norte, oriente, sierra norte, sierra centro, sur andino) busca en la web
> noticias y reacciones en redes de los últimos días sobre **Keiko Fujimori** y **Roberto
> Sánchez**. Estima un `net` por departamento en [−1, 1] (+ favorece a Keiko) y actualiza
> `data/indice_redes.csv` (columna `net` y `fuente` con fecha). Luego ejecuta
> `python -m src.agregar_snapshot` y `python main.py`, y haz commit y push con mensaje
> `chore(iar): snapshot <fecha>`. No cambies la base de los finalistas ni el modelo de trasvase.

## Cadencia

Recomendado **diario** hasta el 7-jun-2026 (día de la elección), cuando el indicador adelantado
es más informativo. Se puede crear como agente programado (rutina cron) — ver `/schedule`.

## Notas

- Es un proxy de **noticias/redes** vía web; el `net` es estimación, no medición directa de
  APIs de X/Meta (sin acceso). `social_signals.csv` permite incorporar datos medidos.
- `agregar_snapshot` reemplaza las filas del día si se corre más de una vez por fecha.
