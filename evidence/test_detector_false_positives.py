"""Falsos positivos medidos en PRs publicos reales (2026-09-04).

Procedencia
-----------
Estas lineas NO son inventadas. Salen de un barrido de 249 pull requests
abiertos y publicos (`tools/field_scan_full.py`), donde el detector marcaba
150 hallazgos, 79 de ellos CRITICOS. Al revisarlos uno a uno, la inmensa
mayoria eran falsos. Cada caso de abajo lleva el repositorio donde se observo.

Por que este fichero importa mas que cualquier otra prueba
----------------------------------------------------------
El producto comenta en el pull request de otra persona. Un CRITICO falso no es
un fallo cosmetico: destruye justo lo unico que vendemos, que es que el aviso
merezca leerse. Un detector que se equivoca es peor que no tener detector.

La segunda clase de prueba es igual de necesaria: las lineas que SI deben
seguir saltando. Silenciar el ruido bajando la sensibilidad hasta no detectar
nada seria pasar la prueba rompiendo el producto.
"""

import pytest

from src.github_app.detector import audit_diff


def _diff(path: str, *lines: str) -> str:
    cuerpo = "".join(f"+{l}\n" for l in lines)
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            f"@@ -1,0 +1,{len(lines)} @@\n{cuerpo}")


def _reglas(path: str, *lines: str) -> set:
    return {f["rule_id"] for f in audit_diff(_diff(path, *lines))["findings"]}


class TestFalsosPositivosMedidosEnAbierto:
    """Cada caso se observo en un PR publico real."""

    def test_exec_de_una_expresion_regular_no_es_ejecucion_dinamica(self):
        # apache/hugegraph-doc#472 — se marcaba CRITICAL
        assert "VULN-EVAL" not in _reglas(
            "assets/js/kapa-adapter.js",
            "var match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(color);")

    def test_metodo_eval_de_un_modelo_no_es_ejecucion_dinamica(self):
        assert "VULN-EVAL" not in _reglas("train.py", "model.eval()")

    def test_un_comentario_que_menciona_eval_no_es_un_hallazgo(self):
        # unslothai/unsloth#10113 — dos CRITICAL sobre lineas de comentario
        assert "VULN-EVAL" not in _reglas(
            "scripts/lint_exec_literals.py",
            "# Obfuscation: large single-line base64-ish blob behind Function()/ eval().")

    def test_bundle_minificado_no_produce_hallazgos_de_codigo(self):
        # ArgusLabs-ai/ARGUS#71 — un build de Next.js dentro del PR
        assert _reglas(
            "src/argus/ui_dist/_next/static/chunks/287-f935e880e41fe755.js",
            '"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push('
            '[[287],{7648:function(e,t,n){return eval(r)}}]);') == set()

    def test_la_palabra_update_en_un_mensaje_no_es_sql_injection(self):
        # michaeljabbour/addteam#33 — tres HIGH sobre texto de consola
        assert "VULN-SQLI-FSTRING" not in _reglas(
            "src/addteam/app.py",
            'results.append((u, "would", f"update - {current_perm} -> {collab.permission}"))')

    def test_texto_de_version_con_flecha_no_es_sql_injection(self):
        assert "VULN-SQLI-FSTRING" not in _reglas(
            "src/addteam/ui.py",
            'print(f"  update available: {__version__} -> {latest}")')

    def test_nombre_de_variable_de_entorno_no_es_un_secreto(self):
        # dreadnought-foundry/bureau-pipeline#263 — tres HIGH
        assert "SECRET-GENERIC" not in _reglas(
            "scripts/push_rescue.py",
            'RETRY_TOKEN_ENV = "PUSH_RESCUE_RETRY"',
            'TOKEN_SOURCE_ENV = "PUSH_TOKEN_SOURCE"')

    def test_sk_dentro_de_una_palabra_corriente_no_es_una_clave(self):
        # weni-ai/retail-setup#567 — "task-..." contiene "sk-"
        assert "SECRET-OPENAI" not in _reglas(
            "retail/settings.py",
            'CELERY_BEAT_SCHEDULE = {"task-retail-back-in-stock-status-check": {}}')

    def test_prompt_con_dato_interno_no_es_inyeccion_de_prompt(self):
        # rarescos-pixel/ripple-agentic-plan-repair#7
        assert "VULN-LLM-INJECT" not in _reglas(
            "src/ripple/presentation/repair_card.py",
            'decision_prompt = f"Approve the {repair_cost} repair?"')


class TestSegundaRondaDeFalsosPositivos:
    """Casos que sobrevivieron a la primera correccion, en el mismo barrido."""

    def test_exec_no_es_un_builtin_en_typescript(self):
        # happytomatoe/fedora-speech-to-text#157 — seis CRITICAL sobre un
        # ayudante `exec()` escrito por el propio autor
        assert "VULN-EVAL" not in _reglas(
            "e2e/lib/transport.ts",
            "  async exec(command: string, timeoutMs = 30000): Promise<ExecResult> {")

    def test_llamar_a_un_exec_propio_en_typescript_no_es_ejecucion_dinamica(self):
        assert "VULN-EVAL" not in _reglas(
            "e2e/e2e.ts",
            "const cwd = (await exec(`readlink /proc/${svcPid}/cwd`)).stdout.trim();")

    def test_definir_una_funcion_llamada_exec_no_es_ejecutarla(self):
        # Luecx/OpenCAE-Studio#48 — CRITICAL sobre `def exec(self):`
        assert "VULN-EVAL" not in _reglas("tests/test_ui.py", "    def exec(self):")

    def test_una_tabla_de_markdown_no_es_una_plantilla(self):
        # ousui/sdlc-ai-spec#10 — el texto "| safe automated execution |"
        # casaba con el filtro `|safe` de Jinja
        assert "VULN-LLM-XSS" not in _reglas(
            "docs/08-TRACEABILITY.md",
            "| safe automated/manual/hybrid execution | Design; Architecture |")

    def test_se_respeta_una_supresion_de_seguridad_explicita(self):
        # full-chaos/dev-health-ops#2224 — el autor ya marco `# noqa: S608`
        assert "VULN-SQLI-FSTRING" not in _reglas(
            "tests/test_migration.py",
            'sql = f"UPDATE daily_metrics_runs SET {column} = {value} "  # noqa: S608')

    def test_pero_un_noqa_de_estilo_no_silencia_nada(self):
        """`# noqa: E501` es longitud de linea. No autoriza nada de seguridad."""
        assert "VULN-SQLI-FSTRING" in _reglas(
            "q.py", 'sql = f"UPDATE usuarios SET x = {v} WHERE id = {i}"  # noqa: E501')


class TestTerceraRondaDeFalsosPositivos:
    """Casos de la segunda medicion, ya con el detector corregido una vez."""

    def test_vaciar_un_nodo_no_es_xss(self):
        # MilBia/Suchar-Overflow#316
        assert "VULN-LLM-XSS" not in _reglas(
            "tests/js/theme_spam.test.js", 'document.body.innerHTML = "";')

    def test_html_constante_no_es_xss(self):
        # colehurwitz/remote-factory#8 — literal fijo, no lo controla nadie
        assert "VULN-LLM-XSS" not in _reglas(
            "app.js", "panel.innerHTML = '<div>Waiting for games...</div>';")

    def test_marcador_de_token_de_slack_en_un_readme_no_es_una_filtracion(self):
        # pydantic/pydantic-ai-harness#794
        assert "SECRET-SLACK" not in _reglas(
            "docs/channels.md", "export SLACK_BOT_TOKEN='xoxb-your-token'")

    def test_comentario_de_plantilla_jinja_no_es_un_hallazgo(self):
        # ClankJake/Painel-Plex#23
        assert "VULN-LLM-XSS" not in _reglas(
            "app/templates/invite.html",
            "   `|safe` final solo libera el <strong> que escribimos nosotros. #}")


class TestCuartaRondaDeFalsosPositivos:
    def test_una_consulta_parametrizada_no_es_inyeccion_sql(self):
        """El peor falso positivo posible: marcar como vulnerable la forma
        CORRECTA de escribir la consulta. ContextualWisdomLab/pg-llm-batch#323."""
        assert "VULN-SQLI" not in _reglas(
            "token_counter.py",
            'cur.execute("SELECT tiktoken_count(%s, %s)", (tiktoken_name, text))')

    def test_referencia_a_una_variable_de_entorno_no_es_un_secreto(self):
        # darkmatter/centaur#54 — PGPASSWORD="$CENTAUR_DB_PASSWORD"
        assert "SECRET-GENERIC" not in _reglas(
            ".github/workflows/ci.yml", 'PGPASSWORD="$CENTAUR_DB_PASSWORD" createdb')

    def test_no_se_cruza_el_limite_de_una_cadena(self):
        # uzkba/nexusflow#24 — capturaba trozos de codigo como si fueran el valor
        assert "SECRET-GENERIC" not in _reglas(
            "backend/tests/test_auth_login.py",
            'token_puro = cabecera.split("refresh_token=")[1].split(";")[0]')

    def test_sql_construido_con_el_operador_de_formato_si_salta(self):
        assert "VULN-SQLI" in _reglas(
            "db.py", 'cur.execute("SELECT * FROM t WHERE id = %s" % uid)')

    def test_sql_concatenado_si_salta(self):
        assert "VULN-SQLI" in _reglas("db.py", 'cur.execute("SELECT * FROM " + tabla)')

    def test_sql_con_format_si_salta(self):
        assert "VULN-SQLI" in _reglas(
            "db.py", 'cur.execute("SELECT * FROM {}".format(tabla))')


class TestSoloSeAuditaCodigo:
    """haddocking/haddock3#1686, encontrado el 2026-09-05 preparando expedientes
    de clientes: 581 hallazgos graves, casi todos sobre ficheros `.canonical` de
    datos de prueba que contienen la palabra eval."""

    def test_un_fichero_de_datos_no_se_audita_como_codigo(self):
        assert _reglas("tests/golden_data/cgtoaa.canonical",
                       "  eval( $atom_name )") == set()

    def test_ni_un_csv_ni_un_log(self):
        assert _reglas("data/muestras.csv", 'id,expr\n1,"eval(x)"') == set()
        assert _reglas("salida.log", "DEBUG llamada a eval(payload)") == set()

    def test_pero_el_codigo_de_verdad_si(self):
        assert "VULN-EVAL" in _reglas("src/app.py", "eval(peticion.body)")

    def test_un_dockerfile_es_codigo(self):
        assert "VULN-SHELL" in _reglas(
            "Dockerfile", "RUN subprocess.run(cmd, shell=True)")

    def test_una_credencial_en_un_fichero_de_datos_si_se_marca(self):
        """La lista blanca es solo para reglas de CODIGO. Una clave filtrada
        lo esta igual dentro de un .txt."""
        assert "SECRET-AWS" in _reglas("notas.txt", 'key = "AKIAZ9Y8X7W6V5U4T3S2"')


class TestMencionarNoEsEjecutar:
    """haddocking/haddock3#1686: una expresion regular que reconoce la palabra
    eval en ficheros ajenos se marcaba como ejecucion dinamica CRITICA."""

    def test_una_regex_que_menciona_eval_no_lo_ejecuta(self):
        assert "VULN-EVAL" not in _reglas(
            "src/haddock/libs/libcnscanonical.py",
            r'PATRON = r"eval(?:uate)?\s*\(\s*\$(?P<name>[A-Za-z0-9_]+)\s*=\s*"')

    def test_una_cadena_normal_que_menciona_eval_tampoco(self):
        assert "VULN-EVAL" not in _reglas(
            "app.py", 'log.warning("no uses eval(x) aqui")')

    def test_pero_eval_de_verdad_junto_a_una_cadena_si_salta(self):
        assert "VULN-EVAL" in _reglas("app.py", 'resultado = eval(peticion["expr"])')

    def test_exec_con_compile_sigue_saltando(self):
        assert "VULN-EVAL" in _reglas(
            "tests/t.py", 'exec(compile(modulo, str(RUTA), "exec"), espacio)')


class TestGravedadSegunDondeVive:
    def test_en_produccion_mantiene_la_gravedad(self):
        f = audit_diff(_diff("app/db.py",
                             'sql = f"select {c} from usuarios where id = {i}"'))["findings"][0]
        assert f["severity"] == "HIGH"

    def test_en_una_prueba_baja_un_nivel(self):
        f = audit_diff(_diff("tests/test_db.py",
                             'sql = f"select {c} from usuarios where id = {i}"'))["findings"][0]
        assert f["severity"] == "MEDIUM" and f["confidence"] == "medium"

    def test_pero_se_sigue_informando(self):
        assert "VULN-SQLI-FSTRING" in _reglas(
            "tests/test_db.py", 'sql = f"select {c} from usuarios where id = {i}"')


class TestLoQueDebeSeguirSaltando:
    """Sin esta clase, la correccion anterior se podria 'aprobar' apagando todo."""

    def test_eval_de_verdad_sigue_siendo_critico(self):
        assert "VULN-EVAL" in _reglas("app.py", "resultado = eval(peticion.body)")

    def test_exec_de_verdad_en_python_sigue_saltando(self):
        assert "VULN-EVAL" in _reglas("app.py", "exec(codigo_del_usuario)")

    def test_eval_en_javascript_sigue_saltando(self):
        """`eval` SI es un builtin en JS, a diferencia de `exec`."""
        assert "VULN-EVAL" in _reglas("app.js", "const r = eval(req.body.expr);")

    def test_sql_real_interpolado_sigue_saltando(self):
        # dbt-labs/dbt-adapters#2147 — este SI era correcto
        assert "VULN-SQLI-FSTRING" in _reglas(
            "test_create_or_alter.py",
            'project.run_sql(f"drop schema if exists {project.test_schema} cascade")')

    def test_select_from_interpolado_sigue_saltando(self):
        assert "VULN-SQLI-FSTRING" in _reglas(
            "q.py", 'sql = f"select {cols} from usuarios where id = {uid}"')

    def test_update_set_interpolado_sigue_saltando(self):
        assert "VULN-SQLI-FSTRING" in _reglas(
            "q.py", 'sql = f"UPDATE usuarios SET nombre = {nombre} WHERE id = {uid}"')

    def test_reindex_interpolado_sigue_saltando(self):
        # Mu-L/prefect#712 — correcto, aunque el riesgo practico sea bajo
        assert "VULN-SQLI-FSTRING" in _reglas(
            "migracion.py", 'op.execute(f"REINDEX INDEX CONCURRENTLY {index[0]}")')

    def test_pickle_sigue_saltando(self):
        # papayasamosa/Media-Mix-Lab#351 — correcto
        assert "VULN-PICKLE" in _reglas(
            "fit_job_service.py", "return cast(dict, pickle.load(handle))")

    def test_clave_de_openai_de_verdad_sigue_saltando(self):
        assert "SECRET-OPENAI" in _reglas(
            "config.py", 'OPENAI_KEY = "sk-proj-Ab3xZ9kQ2mN7pR4tV6wY8uI0oP1aS5dF"')

    def test_clave_de_aws_sigue_saltando(self):
        assert "SECRET-AWS" in _reglas("config.py", 'key = "AKIAZ9Y8X7W6V5U4T3S2"')

    def test_prompt_con_entrada_de_usuario_sigue_saltando(self):
        assert "VULN-LLM-INJECT" in _reglas(
            "chat.py", 'prompt = f"Responde a esto: {user_message}"')

    def test_shell_true_sigue_saltando(self):
        assert "VULN-SHELL" in _reglas(
            "run.py", "subprocess.run(cmd, shell=True)")

    def test_un_secreto_dentro_de_un_bundle_sigue_saltando(self):
        """El silencio de ficheros generados es solo para reglas de CODIGO.
        Una credencial real publicada en un bundle es una filtracion real."""
        assert "SECRET-AWS" in _reglas(
            "dist/app.min.js", 'var k="AKIAZ9Y8X7W6V5U4T3S2";')


class TestCredencialesDeEjemploDeLaDocumentacion:
    """Ronda 9 del ciclo adversarial, 2026-09-09.

    El primer escaneo inicial contra un repositorio real (el nuestro) devolvio
    3 hallazgos, y 2 eran `AKIAIOSFODNN7EXAMPLE`: la clave que AWS publica en su
    propia documentacion. Aparece en tutoriales, plantillas y fixtures por todo
    GitHub. Como primer informe a un cliente, es exactamente el ruido que hace
    que desinstalen.

    `SECRET-AWS` es una regla `strict`, asi que el filtro de marcadores no la
    tocaba. Esta exclusion se aplica tambien a las estrictas porque aqui no hay
    ambiguedad: es la cadena literal del fabricante.
    """

    def test_no_marca_la_clave_de_ejemplo_de_aws(self):
        assert "SECRET-AWS" not in _reglas(
            "config.py", 'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"')

    def test_tampoco_su_clave_secreta(self):
        assert not _reglas(
            "config.py",
            'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"')

    def test_ni_en_un_fichero_de_entorno(self):
        assert "SECRET-AWS" not in _reglas(
            ".env.example", "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")

    def test_una_variante_con_example_dentro_tampoco(self):
        assert "SECRET-AWS" not in _reglas(
            "docs/guia.md", 'key = "AKIAEXAMPLEKEY1234XY"')

    def test_pero_una_clave_con_forma_valida_si(self):
        """El corte no puede ser 'cualquier cosa que huela a demo'."""
        assert "SECRET-AWS" in _reglas("config.py", 'key = "AKIAZ9Y8X7W6V5U4T3S2"')

    def test_ni_apaga_las_demas_reglas(self):
        assert "SECRET-OPENAI" in _reglas(
            "config.py", 'OPENAI_KEY = "sk-proj-Ab3xZ9kQ2mN7pR4tV6wY8uI0oP1aS5dF"')


class TestRuidoGlobal:
    def test_un_pr_normal_no_produce_ningun_hallazgo(self):
        reglas = _reglas(
            "src/util.py",
            "def suma(a, b):",
            "    # suma dos numeros",
            "    return a + b",
            "",
            "class Cliente:",
            '    nombre: str',
            '    def saludar(self):',
            '        print(f"Hola {self.nombre}")')
        assert reglas == set(), f"ruido en codigo inocuo: {reglas}"


class TestUnaVariableVaciadaEsLaCorreccionNoElFallo:
    """Encontrado el 2026-09-10 verificando a mano el PRIMER expediente de
    divulgación real antes de enviarlo, en `liminalvillage/holons`.

    La línea marcada era exactamente el arreglo del fallo: fuerzan la clave a
    cadena vacía en cada build de producción, y lo explican en un comentario de
    seis líneas. El aviso le habría dicho a un equipo que entiende el problema
    mejor que nosotros que tiene el bug que ellos arreglaron.

    La puerta humana de precisión existe para esto, y esta vez sirvió.
    """

    def test_el_caso_exacto_del_mundo_real(self):
        assert "VULN-CLIENT-SECRET" not in _reglas(
            "apps/kiosk/vite.config.ts",
            '''      ? { "import.meta.env.VITE_OPENAI_API_KEY": '""' }''')

    @pytest.mark.parametrize("linea", [
        'NEXT_PUBLIC_OPENAI_API_KEY=',
        'NEXT_PUBLIC_STRIPE_SECRET_KEY=""',
        "VITE_OPENAI_API_KEY=''",
        '"import.meta.env.VITE_OPENAI_API_KEY": ""',
        'VITE_OPENAI_API_KEY: undefined',
        'NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY: null',
    ])
    def test_otras_formas_de_vaciarla(self, linea):
        assert "VULN-CLIENT-SECRET" not in _reglas("vite.config.ts", linea)

    @pytest.mark.parametrize("fichero,linea", [
        (".env.local", 'NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiJ9.real'),
        # Ojo con la ruta: leer del entorno en un `*.config.*` corre en Node y
        # está silenciado a propósito (ver la clase de más abajo). Para probar
        # que una LECTURA sigue saltando hace falta código de cliente.
        ("src/lib/db.ts", 'const k = process.env.NEXT_PUBLIC_OPENAI_API_KEY;'),
        (".env", 'VITE_OPENAI_API_KEY=sk-proj-Ab3xZ9kQ2mN7pR4tV6wY8uI0oP1aS5dF'),
        ("vite.config.ts", 'NEXT_PUBLIC_STRIPE_SECRET_KEY="cambiame"'),
    ])
    def test_pero_lo_que_NO_esta_vacio_sigue_saltando(self, fichero, linea):
        """La regla se queda estrecha a propósito: no se puede saber si una
        cadena no vacía es un marcador o una clave real, y ante la duda se avisa."""
        assert "VULN-CLIENT-SECRET" in _reglas(fichero, linea)


class TestLeerUnaVariableEnNodeNoEsPublicarlaEnElNavegador:
    """Segundo falso positivo encontrado verificando a mano un expediente de
    divulgación antes de enviarlo, en `nips-live/nips-live-ai-platform`.

    El fichero es la configuración de Transmart, una herramienta de traducción
    que corre en Node en tiempo de build. El prefijo `VITE_` engaña: leer la
    variable en Node no la publica. Lo que la publicaría es que exista con un
    valor real y que el cliente la referencie, y eso no se ve en esa línea.
    """

    def test_el_caso_exacto_del_mundo_real(self):
        assert "VULN-CLIENT-SECRET" not in _reglas(
            "frontend/transmart.config.js",
            "  openAIApiKey: process.env.VITE_OPENAI_API_KEY,")

    @pytest.mark.parametrize("fichero", [
        "vite.config.ts", "next.config.mjs", "astro.config.mjs",
        "apps/web/nuxt.config.ts", "tailwind.config.cjs",
    ])
    def test_cualquier_fichero_de_configuracion(self, fichero):
        assert "VULN-CLIENT-SECRET" not in _reglas(
            fichero, "  key: process.env.NEXT_PUBLIC_OPENAI_API_KEY,")

    def test_pero_el_codigo_de_CLIENTE_sigue_saltando(self):
        """`src/` no es configuración: eso sí acaba en el bundle."""
        assert "VULN-CLIENT-SECRET" in _reglas(
            "src/lib/db.ts",
            "const c = createClient(process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY);")

    def test_y_una_asignacion_directa_en_un_env_tambien(self):
        """Ahí no hay `process.env` de por medio: es el valor, no una lectura."""
        assert "VULN-CLIENT-SECRET" in _reglas(
            ".env.local", "NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiJ9.real")

    def test_un_config_que_asigna_un_valor_literal_no_se_libra(self):
        """La excusa es LEER del entorno. Escribir la clave a pelo en el
        config es otra cosa y sigue siendo un hallazgo."""
        assert "VULN-CLIENT-SECRET" in _reglas(
            "vite.config.ts", '  "VITE_OPENAI_API_KEY": "sk-proj-Ab3xZ9kQ2mN7pR4tV6"')


# ══════════════════════════════════════════════════════════════════════════
# Auditoria Red Team del 2026-09-17
#
# Corpus nuevo y distinto a todo lo anterior: 6.000 ficheros de LIBRERIAS YA
# PUBLICADAS e instaladas en un entorno real -- google-auth, numba, torch,
# numpy, kubernetes, transformers, shapely, ccxt. Codigo revisado, usado por
# mucha gente y en produccion: cualquier cosa que marquemos ahi es, por
# construccion, ruido que un cliente veria sobre codigo suyo correcto.
#
# Las poblaciones anteriores eran diffs de pull request. Esta es codigo ya
# escrito, que es justo lo que mira el escaneo al instalar -- el primer
# contacto de un cliente con el producto. Sobre esa poblacion el detector
# pasaba de 4 hallazgos (los 4 falsos) a 0.
#
# La procedencia se cita por libreria y ruta, no como `owner/repo#PR`, porque
# no salen de un pull request y no vamos a inflar ese recuento.
# ══════════════════════════════════════════════════════════════════════════


class TestLaCabeceraPemCitadaNoEsUnaClave:
    """Los UNICOS 4 hallazgos del escaneo de instalacion sobre 6.000 ficheros
    reales, y los 4 falsos. Todos de la misma familia: alguien NOMBRA el
    formato PEM sin que haya ninguna clave.

    La senal que los separa es estructural, no de intencion: una clave real
    nunca es una cadena cerrada que contiene solo la cabecera, porque la
    cabecera sin cuerpo no es una clave.
    """

    @pytest.mark.parametrize("linea", [
        # google-auth · google/auth/transport/_mtls_helper.py:37-40
        '# "-----BEGIN PRIVATE KEY-----...",',
        '# "-----BEGIN EC PRIVATE KEY-----...",',
        '# "-----BEGIN RSA PRIVATE KEY-----..."',
        '# "-----BEGIN ENCRYPTED PRIVATE KEY-----"',
        # ccxt · ccxt/static_dependencies/ecdsa/keys.py:200
        "privkey_pem = string[string.index(b'-----BEGIN PRIVATE KEY-----'):]",
        # Describir el formato en una constante es lo normal en codigo de crypto
        'MARCADOR = "-----BEGIN PRIVATE KEY-----"',
        'PATRON = re.compile(r"-----BEGIN RSA PRIVATE KEY-----.+")',
    ])
    def test_no_dispara(self, linea):
        assert _reglas("src/app.py", linea) == set()

    @pytest.mark.parametrize("linea", [
        # Lo que SI tiene que seguir disparando, para no cambiar ruido por ceguera
        'KEY = "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEA7Xk9wS2vQ8fK"',
        'PRIVATE = """-----BEGIN PRIVATE KEY-----',
        "# -----BEGIN RSA PRIVATE KEY-----MIIEpAIBAAKCAQEA7Xk9wS2vQ8",
    ])
    def test_una_clave_de_verdad_sigue_saltando(self, linea):
        assert _reglas("src/app.py", linea), "silenciar una clave real es peor que el ruido"


class TestUnaUrlUnaRutaOUnaFraseNoSonUnaCredencial:
    """La entropia por caracter de una URL supera cualquier umbral razonable,
    asi que -- igual que con los nombres de variable de entorno en su dia --
    hacia falta un filtro estructural y no estadistico.

    Las cuatro llevan `token` en el nombre, que es justo lo que la regla busca.
    """

    @pytest.mark.parametrize("linea", [
        # google-auth · google/auth/downscoped.py:64-69
        '_STS_REQUESTED_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"',
        '_STS_TOKEN_URL_PATTERN = "https://sts.{}/v1/token"',
        # kubernetes · kubernetes/aio/config/incluster_config.py:24
        'SERVICE_TOKEN_FILENAME = "/var/run/secrets/kubernetes.io/serviceaccount/token"',
        # microsoft-teams · microsoft_teams/api/auth/cloud_environment.py:38
        'token_service_url="https://login.microsoftonline.com/common"',
        # nltk · nltk/test/unit/test_corenlp.py:725
        'input_tokens = "Rami Eid is studying at Stony Brook University in NY".split()',
        # Rutas relativas, mismo caso
        'token_path = "./config/secrets/token.json"',
    ])
    def test_no_dispara(self, linea):
        assert _reglas("src/app.py", linea) == set()

    def test_un_secreto_de_verdad_en_la_misma_forma_sigue_saltando(self):
        assert _reglas("src/app.py", 'api_token = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"')


class TestDebugTrueNoEsSiempreModoDepuracion:
    """11 apariciones sobre codigo real, cero ciertas. `debug=True` como
    argumento de cualquier llamada es un parametro corriente; lo que si es la
    vulnerabilidad es la constante de configuracion de un servidor web."""

    @pytest.mark.parametrize("linea", [
        # numba · numba/cuda/tests/cudapy/test_exception.py:25,37
        "safe_foo = cuda.jit(debug=True, opt=False)(foo)",
        "@cuda.jit(debug=True)",
        # numba · numba/tests/gdb/test_pretty_print.py:18
        "@njit(debug=True)",
        # nltk · nltk/classify/rte_classify.py:98 -- un parametro por defecto
        "def hyp_extra(self, toktype, debug=True):",
        # numba · numba/cuda/decorators.py:80 -- texto dentro de una cadena
        'msg = ("debug=True with opt=True (the default) "',
    ])
    def test_no_dispara(self, linea):
        assert _reglas("src/app.py", linea) == set()

    @pytest.mark.parametrize("linea", [
        "DEBUG = True",
        "app.run(host='0.0.0.0', debug=True)",
        "settings.DEBUG = True",
    ])
    def test_el_modo_depuracion_de_verdad_sigue_saltando(self, linea):
        assert _reglas("src/app.py", linea)


class TestUnViajeDeIdaYVueltaConPickleNoEsUnRiesgo:
    """`pickle.loads(pickle.dumps(x))` deserializa lo que uno mismo acaba de
    serializar: no hay entrada de un tercero, que es lo unico que hace
    peligroso a pickle. Era el patron mas repetido del corpus."""

    @pytest.mark.parametrize("linea", [
        # arch · arch/tests/univariate/test_recursions.py:271
        "gu = pickle.loads(pickle.dumps(gu))",
        "assert pickle.loads(pickle.dumps(obj)) == obj",
    ])
    def test_no_dispara(self, linea):
        assert _reglas("src/app.py", linea) == set()

    def test_deserializar_algo_que_llega_de_fuera_sigue_saltando(self):
        assert _reglas("src/app.py", "datos = pickle.loads(request.body)")


# ══════════════════════════════════════════════════════════════════════════
# Barrido de pull requests reales — 2026-09-17, 117 PRs publicos
#
# Poblacion CORRECTA para las reglas VULN: lineas que alguien acaba de
# escribir, no ficheros enteros. 3 PRs con hallazgo (2,6 %), 16 hallazgos.
# Revisados uno a uno, que es donde esta la medicion.
# ══════════════════════════════════════════════════════════════════════════


class TestElSufijoSpecEsCodigoDePrueba:
    """En JS/TS una prueba no vive en `tests/`, se llama `algo.spec.ts`. La
    regla solo reconocia `spec` como SEGMENTO de ruta, asi que un token de
    fixture salia como HIGH sobre codigo que nadie ejecuta en produccion."""

    @pytest.mark.parametrize("ruta", [
        # Neonity2020/hermes-agent#601
        "apps/desktop/e2e/group-create-gate-remote-roster.spec.ts",
        "src/components/Boton.test.tsx",
        "cypress/integration/login.js",
        "src/__tests__/api.js",
        "playwright/checkout.e2e.ts",
    ])
    def test_baja_la_gravedad_en_vez_de_alarmar(self, ruta):
        hall = audit_diff(_diff(ruta, "const REMOTE_TOKEN = 'e2e-abcdefghijklmnopqrstuvwx'"))
        for f in hall["findings"]:
            assert f["severity"] != "HIGH", \
                f"{ruta} es codigo de prueba: avisar si, alarmar no"

    def test_el_mismo_token_en_produccion_si_alarma(self):
        hall = audit_diff(_diff("src/api/cliente.ts",
                                "const REMOTE_TOKEN = 'e2e-abcdefghijklmnopqrstuvwx'"))
        assert any(f["severity"] == "HIGH" for f in hall["findings"])


class TestNoSePuedeInyectarPorUnaConstante:
    """El peor tipo de falso positivo: castigar a quien lo esta haciendo bien.

    Neonity2020/hermes-agent#601 parametrizaba correctamente el dato del
    usuario con `?` y solo interpolaba el nombre de tabla, que es una constante
    de modulo. Lo marcamos como inyeccion SQL.
    """

    @pytest.mark.parametrize("linea", [
        'cur.execute(f"SELECT 1 FROM {MARKER_TABLE} WHERE source=?", (SOURCE_NAME,))',
        'cur.execute(f"CREATE TABLE IF NOT EXISTS {MARKER_TABLE} (source TEXT PRIMARY KEY)")',
        'db.execute(f"DELETE FROM {TABLA_CACHE} WHERE id=?", (pk,))',
    ])
    def test_no_dispara(self, linea):
        assert not [r for r in _reglas("gateway/rooms.py", linea) if r.startswith("VULN-SQLI")]

    @pytest.mark.parametrize("linea", [
        'cur.execute(f"SELECT * FROM users WHERE name={nombre}")',
        'cur.execute(f"PRAGMA table_info({name})")',
        'conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")',
    ])
    def test_una_variable_de_verdad_sigue_saltando(self, linea):
        assert [r for r in _reglas("gateway/rooms.py", linea) if r.startswith("VULN-SQLI")]


class TestElMismoProblemaNoSeCuentaDosVeces:
    """VULN-SQLI y VULN-SQLI-FSTRING senalaban a la vez la misma linea. El
    cliente veia el mismo problema dos veces con dos nombres, que es la forma
    mas rapida de que deje de leernos."""

    def test_una_sola_regla_por_linea_y_debilidad(self):
        # Neonity2020/hermes-agent#601 · gateway/hosted_rooms.py:367
        reglas = _reglas("gateway/hosted_rooms.py",
                         'conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")')
        sqli = [r for r in reglas if r.startswith("VULN-SQLI")]
        assert len(sqli) == 1, f"un problema, un aviso: {sqli}"

    def test_sobrevive_la_que_dice_que_arreglar(self):
        reglas = _reglas("m.py", 'op.execute(f"REINDEX INDEX CONCURRENTLY {index[0]}")')
        assert "VULN-SQLI-FSTRING" in reglas

    def test_dos_debilidades_distintas_en_una_linea_siguen_siendo_dos(self):
        reglas = _reglas("app.py", 'eval(requests.get(url, verify=False).text)')
        assert len(reglas) >= 2, "esto si son dos problemas diferentes"


class TestRespetamosLoQueElEquipoYaHabiaDeclarado:
    """AndreyDeveloper84/beautygo_backend#501 tenia esto:

        PASSWORD = "Sup3rS3cr42"  # pragma: allowlist secret

    Ese `pragma` es el marcador estandar de detect-secrets. El equipo ya habia
    declarado, con la anotacion que usa el ecosistema, que esa linea no es un
    secreto -- y pasabamos por encima y lo reportabamos igual.

    Respetarlos mata una familia entera de falsos positivos sin inventar
    heuristicas, y le ahorra a quien venga de otro escaner tener que anotar su
    codigo dos veces.
    """

    @pytest.mark.parametrize("linea", [
        'PASSWORD = "Sup3rS3cr42xyz"  # pragma: allowlist secret',      # detect-secrets
        'subprocess.call(cmd, shell=True)  # nosec',                     # bandit
        'token = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6"  # gitleaks:allow',       # gitleaks
        'eval(expr)  # nosemgrep',                                        # semgrep
        'api_key = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"  # NOSONAR',        # sonarqube
        'clave = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"  # trufflehog:ignore',
        'api_key = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"  # magaudit: ignore',
        'api_key = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"  // magaudit:ignorar',
    ])
    def test_una_linea_ya_revisada_no_se_vuelve_a_mirar(self, linea):
        assert _reglas("src/app.py", linea) == set()

    def test_la_misma_linea_sin_marcador_si_se_reporta(self):
        assert _reglas("src/app.py",
                       'api_key = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"') != set()

    def test_el_marcador_solo_vale_para_SU_linea(self):
        """Un `# nosec` no puede apagar el fichero entero: eso convertiria una
        anotacion puntual en una puerta trasera."""
        reglas = _reglas("src/app.py",
                         'a = "hQ7bZp2LxV9nR4mKdT8wYcF3gJ6sA1eU"  # nosec',
                         'api_key = "zR4mKdT8wYcF3gJ6sA1eUhQ7bZp2L"')
        assert reglas != set()
