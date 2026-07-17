# Improvement Roadmap

Objetivo: aumentar valor profesional sin ocultar deuda tecnica. Priorizacion basada en impacto curricular, riesgo funcional y esfuerzo estimado.

## Quick Wins

| Mejora | Impacto | Esfuerzo | Prioridad | Evidencia / razon |
| --- | --- | --- | --- | --- |
| Conectar heatmap del dashboard a `/api/strategy/heatmap` | Alto | Bajo | P0 | `dashboard.html` usa `Math.random()` aunque el backend ya expone datos reales. |
| Definir o reemplazar `resetToBetting()` | Alto | Bajo | P0 | `index.html` invoca una funcion no encontrada por `rg`. |
| Eliminar dependencia de `current_state` o sincronizarla | Alto | Bajo | P0 | `ux-enhancements.js` usa `current_state` sin definicion visible. |
| Depurar `requirements.txt` | Medio | Bajo | P1 | `numpy`, `pandas`, `matplotlib` no aparecen usados directamente; dificultaron instalacion. |
| Agregar badges de tests, Docker y licencia | Medio | Bajo | P1 | Mejora lectura inicial de GitHub. |
| Documentar variables de entorno | Medio | Bajo | P1 | `APP_ENV`, `SECRET_KEY`, `DATABASE_URL` ya existen. |

## Backlog priorizado

| Mejora | Impacto | Esfuerzo | Prioridad | Resultado esperado |
| --- | --- | --- | --- | --- |
| Tests de Flask API con `app.test_client()` | Alto | Medio | P0 | Validar `/api/start`, `/bet`, `/hit`, `/stand`, `/probability`, auth y errores. |
| Tests de split, insurance y double down | Alto | Bajo | P0 | Reducir riesgo en acciones avanzadas de Blackjack. |
| Reemplazar heatmap mock por datos reales | Alto | Bajo | P0 | Dashboard deja de mostrar informacion falsa. |
| Pruebas Socket.IO | Alto | Medio | P1 | Validar create/join room, turnos y start_training. |
| Completar lifecycle multijugador | Alto | Alto | P1 | Manejar host, desconexion, limpieza de salas, apuestas por jugador y nueva ronda. |
| Separar estado de juego de Flask session | Alto | Alto | P1 | Facilitar escalado, testing y persistencia real de partidas. |
| Logging estructurado | Medio | Medio | P2 | Reemplazar `print` en errores DB/socket por logging configurable. |
| Indices DB para leaderboard | Medio | Bajo | P2 | Mejorar consultas por `peak_balance`. |
| Validacion de payloads API | Medio | Medio | P2 | Evitar entradas invalidas y estados inconsistentes. |
| Reducir globals frontend | Medio | Medio | P2 | Consolidar estado cliente en un modulo. |
| Cobertura de frontend con Playwright | Medio | Medio | P2 | Verificar flujos reales de login/juego/dashboard. |
| Versionar datos de Q-table | Medio | Medio | P3 | Evitar incompatibilidades de estados y facilitar reproducibilidad. |

## Higiene del repositorio

| Area | Estado actual | Mejora recomendada | Prioridad |
| --- | --- | --- | --- |
| README | Actualizado y breve | Mantener screenshots reales cuando UI este verificada | P2 |
| Licencia | Existe `LICENSE` | Confirmar que GitHub detecte MIT correctamente | P2 |
| GitHub Topics | No verificable localmente | Agregar `python`, `flask`, `blackjack`, `q-learning`, `monte-carlo`, `socketio` | P1 |
| Descripcion del repo | No verificable localmente | Usar descripcion tecnica corta: "Flask Blackjack simulator with Q-Learning, Monte Carlo and Socket.IO" | P1 |
| `.gitignore` | Existe | Confirmar exclusion de `.venv`, `instance`, `flask_session`, caches y DB local | P0 |
| `.gitattributes` | Existe | Mantener normalizacion de line endings | P2 |
| Estructura | Clara por capas | Considerar `docs/` para reviews y evidencia | P3 |
| Formato | `pyproject.toml` configura ruff | Agregar comando documentado de lint | P2 |
| Badges | CI, Python, Flask, tests, licencia | Agregar Docker si se publica imagen | P3 |
| CI/CD | Compile + pytest | Agregar lint y matriz Python 3.11/3.12 si aplica | P2 |
| Documentacion tecnica | Review y CV evidence existen | Mantener matriz de cumplimiento actualizada tras cambios | P1 |

## Mejoras por area profesional

| Area | Mejora de mayor valor | Por que aumenta valor curricular |
| --- | --- | --- |
| Backend | Tests de rutas, auth y DB | Demuestra confiabilidad mas alla del dominio puro. |
| IA | Evaluacion reproducible de politica Q-Learning vs baseline | Convierte IA de feature a evidencia medible. |
| Frontend | Reparar funciones globales y heatmap real | Evita que la demo falle en entrevista. |
| Arquitectura | Extraer servicio de estado de juego | Mejora escalabilidad y testabilidad. |
| DevOps | CI con lint + tests + build Docker | Muestra flujo profesional completo. |

## Orden recomendado

1. Reparar `resetToBetting`, `current_state` y heatmap mock.
2. Agregar tests de acciones avanzadas y endpoints Flask.
3. Depurar dependencias y actualizar instrucciones de instalacion.
4. Completar multijugador o documentarlo explicitamente como experimental.
5. Agregar verificacion frontend automatizada.
6. Mejorar persistencia de partidas y observabilidad.

## Criterio de salida para portafolio

| Criterio | Minimo aceptable |
| --- | --- |
| Demo local | Login, iniciar partida, apostar, hit/stand, nueva ronda y dashboard sin errores JS visibles. |
| Tests | Core, IA, API Flask y acciones avanzadas cubiertas. |
| Documentacion | README breve + Technical Review honesto + Roadmap actualizado. |
| Reproducibilidad | Instalacion limpia desde `requirements.txt` sin dependencias innecesarias. |
| Honestidad | Multijugador marcado como parcial hasta cubrir lifecycle completo. |
