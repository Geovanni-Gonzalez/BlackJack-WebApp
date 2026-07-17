# CV Evidence

Documento reutilizable para Master Resume, LinkedIn y entrevistas. Solo incluye evidencia verificable en el repositorio.

## Competencias demostradas

| Evidencia | Competencia demostrada | Evidencia en codigo | Nivel de profundidad |
| --- | --- | --- | --- |
| Motor de Blackjack con turnos, apuestas y resolucion | Modelado de dominio, POO, reglas de negocio | `app/core/game.py`, `app/core/rules.py`, `app/core/cards.py` | Python nivel 3: clases, composicion, estado mutable controlado. |
| Monte Carlo para recomendar hit/stand | Simulacion probabilistica | `app/ai/montecarlo.py` | Algoritmos nivel 3: simulacion repetida con zapato restante. |
| Q-Learning tabular | Aprendizaje por refuerzo basico | `app/ai/qlearning.py`, `q_table.json` | IA nivel 2: Q-table, epsilon-greedy, persistencia JSON. |
| Conteo Hi-Lo | Algoritmo incremental de conteo | `app/ai/counter.py` | Algoritmos nivel 2: O(1) por carta. |
| API Flask modular | Backend web y arquitectura por capas | `app/__init__.py`, `app/web/controllers/api.py` | Backend nivel 3: app factory, blueprints, REST, sesiones. |
| Autenticacion y formularios | Seguridad web basica | `app/web/controllers/auth.py`, `app/web/forms.py` | Web nivel 2: hashing, CSRF, validacion de formularios. |
| Persistencia con ORM | Modelado relacional y CRUD | `app/data/models.py` | DB nivel 2: SQLAlchemy models y queries simples. |
| Eventos en tiempo real | WebSockets con Socket.IO | `app/web/controllers/sockets.py`, `app/web/static/js/socket_client.js` | Realtime nivel 2: eventos y rooms basicos. |
| Pruebas unitarias | Calidad y regresion | `tests/test_*.py` | Testing nivel 2: reglas, core e IA cubiertos. |
| CI/CD basico | Automatizacion de validacion | `.github/workflows/ci.yml` | DevOps nivel 2: compile + pytest en GitHub Actions. |
| Contenerizacion | Empaquetado de aplicacion | `Dockerfile`, `docker-compose.yml` | DevOps nivel 2: imagen y servicio local. |

## Nuevas habilidades y tecnologias

| Categoria | Elementos respaldados |
| --- | --- |
| Lenguajes | Python, JavaScript, HTML, CSS |
| Backend | Flask, Blueprints, Flask app factory, Flask sessions, CSRF, rate limiting |
| APIs | REST JSON, Fetch API |
| Tiempo real | Flask-SocketIO, Socket.IO rooms/events |
| Persistencia | SQLite, SQLAlchemy ORM, JSON |
| IA / algoritmos | Q-Learning tabular, epsilon-greedy, Monte Carlo, Hi-Lo card counting |
| Testing | pytest, pruebas unitarias de dominio y algoritmos |
| DevOps | GitHub Actions, Docker, Docker Compose |
| Frontend | ES modules, Chart.js, DOM rendering |

## Conceptos tecnicos

| Concepto | Evidencia reutilizable |
| --- | --- |
| POO | Clases para cartas, manos, juego y agentes. |
| Arquitectura por capas | Separacion `core`, `ai`, `data`, `web`. |
| App Factory | Inicializacion de Flask y extensiones en `create_app()`. |
| Repository/DAO | No demostrado como patron formal; SQLAlchemy se usa directamente desde controladores. |
| Strategy/Factory | Factory simple para singletons de IA en `app/ai/factory.py`; estrategias por dificultad en `ai_turn`. |
| REST | Endpoints de acciones, probabilidades, Q-values, leaderboard y estrategia. |
| WebSockets | Eventos para lobby, acciones de juego y entrenamiento. |
| Persistencia | SQLite para usuarios/leaderboard y JSON para Q-table. |
| Manejo de errores | Basico: try/except en sync DB, leaderboard y sockets; no hay logging estructurado. |
| Testing | 24 pruebas unitarias pasan. |
| CI/CD | Workflow GitHub Actions ejecuta compileall y pytest. |

## Logros verificables

| Logro | Evidencia |
| --- | --- |
| Desarrollo de motor de Blackjack con acciones avanzadas | `BlackJackGame` implementa hit, stand, double down, split, insurance, withdraw y payouts. |
| Integracion de IA en flujo de juego | `ai_turn`, `/api/probability`, `/api/qvalues` conectan algoritmos con decisiones. |
| Persistencia de aprendizaje | `QLearningAgent.save/load` usa `q_table.json`. |
| Visualizacion y metricas de sesion | UI muestra balance, rondas, conteo, precision IA/jugador y Chart.js. |
| Validacion automatizada del nucleo | `24 passed` con pytest el 2026-07-16. |
| Automatizacion de calidad en GitHub | Workflow CI compila y ejecuta pruebas en push/PR. |

## Bullets para curriculum

- Desarrolle un simulador web de Blackjack en Flask con motor de reglas, apuestas, turnos, persistencia SQLite y API REST JSON.
- Integre estrategias de decision con Monte Carlo, Q-Learning tabular persistente y conteo Hi-Lo para recomendar acciones hit/stand.
- Modele el dominio del juego con clases Python para mazo, manos, reglas, rondas y resolucion de ganadores.
- Implemente autenticacion con Flask-WTF, hashing de contrasenas, sesiones Flask, CSRF y rate limiting.
- Agregue eventos en tiempo real con Flask-SocketIO para lobby, acciones multijugador y streaming de entrenamiento Q-Learning.
- Automatice validacion con pytest y GitHub Actions; la suite actual verifica 24 casos de reglas, core e IA.
- Prepare empaquetado local con Docker Compose, configuracion por entorno y SQLite persistido.

## Palabras clave ATS

Python, Flask, REST API, SQLAlchemy, SQLite, JavaScript, Socket.IO, WebSockets, pytest, GitHub Actions, Docker, Docker Compose, Q-Learning, Reinforcement Learning, Monte Carlo Simulation, Probability Estimation, Card Counting, Hi-Lo, Object-Oriented Programming, Software Architecture, App Factory, Blueprints, CSRF, Authentication, JSON, CI/CD, Unit Testing.

## Habilidades reforzadas

| Habilidad | Como se refuerza |
| --- | --- |
| Backend Python | Proyecto con rutas, sesiones, extensiones Flask y persistencia. |
| Algoritmos aplicados | Simulacion y aprendizaje reforzado conectados a una decision de usuario. |
| Testing | Pruebas unitarias del dominio y algoritmos, no solo smoke tests. |
| Documentacion tecnica | Evidencia, matriz de cumplimiento y roadmap priorizado. |

## Limites que no deben exagerarse

| Area | Limite |
| --- | --- |
| IA | No demuestra deep learning, embeddings, modelos generativos ni entrenamiento a gran escala. |
| Ciencia de datos | No hay notebooks, analisis exploratorio ni pipeline de datos. |
| DevOps | CI/Docker son basicos; no hay despliegue cloud verificado. |
| Arquitectura distribuida | Estado de juego en sesion y singletons de proceso; no demuestra escalado horizontal. |
| Frontend | UI amplia, pero con deuda de funciones globales y heatmap mock. |
