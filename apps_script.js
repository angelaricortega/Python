/**
 * ════════════════════════════════════════════════════════════════════════════
 *  INTEGRACIÓN: Google Forms → API Encuestas Poblacionales
 *  Archivo: apps_script.js
 * ════════════════════════════════════════════════════════════════════════════
 *
 *  INSTRUCCIONES DE INSTALACIÓN (5 pasos):
 *  ──────────────────────────────────────────────────────────────────────────
 *  1. Abre tu Google Form en el navegador.
 *  2. Haz clic en los 3 puntos ⋮ (arriba a la derecha) → "Editor de scripts".
 *  3. Borra todo el contenido que aparece y pega este archivo completo.
 *  4. Cambia API_URL (línea 34) por la URL pública de tu servidor.
 *     ⚠️  localhost NO funciona desde Google Scripts — necesitas ngrok o
 *         desplegar en la nube (Render, Railway).
 *  5. Configura el disparador automático:
 *       Menú "Activadores" (ícono del reloj) → "+ Agregar activador"
 *       Función a ejecutar : onFormSubmit
 *       Origen del evento  : Del formulario
 *       Tipo de evento     : Al enviar el formulario
 *       → Guardar → Autorizar permisos cuando Google lo pida.
 *  ──────────────────────────────────────────────────────────────────────────
 *
 *  ESTRUCTURA REQUERIDA EN EL FORMULARIO:
 *  Cada pregunta debe tener EXACTAMENTE este título (respeta tildes):
 *
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │ SECCIÓN 1 — Datos demográficos                                      │
 *  │  • "Nombre completo"          → Respuesta corta                     │
 *  │  • "Edad"                     → Respuesta corta (número)            │
 *  │  • "Género"                   → Opción múltiple                     │
 *  │      Opciones: Masculino / Femenino / No binario / Prefiero no decir│
 *  │  • "Estrato socioeconómico"   → Desplegable                         │
 *  │      Opciones: 1 - Bajo-bajo / 2 - Bajo / 3 - Medio-bajo /         │
 *  │                4 - Medio / 5 - Medio-alto / 6 - Alto                │
 *  │  • "Departamento"             → Desplegable (33 departamentos DANE) │
 *  │  • "Municipio"                → Respuesta corta                     │
 *  │  • "Nivel educativo"          → Opción múltiple                     │
 *  │      Opciones: Ninguno / Primaria / Secundaria / Técnico /          │
 *  │                Universitario / Posgrado                             │
 *  │  • "Ocupación"                → Respuesta corta (opcional)          │
 *  │                                                                     │
 *  │ SECCIÓN 2 — Preguntas de encuesta                                   │
 *  │  • "Satisfacción con el servicio de salud en su municipio"          │
 *  │      → Escala lineal 1 a 5                                          │
 *  │  • "Nivel de confianza en las instituciones colombianas (%)"        │
 *  │      → Respuesta corta (número 0-100)                               │
 *  │  • "¿Ha utilizado servicios digitales del Estado en el último mes?" │
 *  │      → Opción múltiple: Sí / No                                     │
 *  │  • "Observaciones adicionales"                                      │
 *  │      → Párrafo (texto largo, opcional)                              │
 *  └─────────────────────────────────────────────────────────────────────┘
 * ════════════════════════════════════════════════════════════════════════════
 */

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  ⚙️  CONFIGURACIÓN — Edita solo esta sección                            ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/** URL del endpoint webhook de tu servidor.
 *  Para desarrollo local usa ngrok: https://xxxx.ngrok-free.app/encuestas/google-forms/
 *  Para producción usa tu dominio:  https://tu-app.onrender.com/encuestas/google-forms/
 */
var API_URL = 'https://TU-SERVIDOR.com/encuestas/google-forms/';

/** Correo para alertas de error (opcional — descomenta en producción). */
// var EMAIL_ALERTAS = 'admin@tudominio.com';


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  🗺️  TABLAS DE NORMALIZACIÓN                                             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

var MAPA_GENERO = {
  'masculino':          'masculino',
  'femenino':           'femenino',
  'no binario':         'no_binario',
  'no_binario':         'no_binario',
  'prefiero no decir':  'prefiero_no_decir',
  'prefiero_no_decir':  'prefiero_no_decir',
};

var MAPA_NIVEL = {
  'ninguno':       'ninguno',
  'primaria':      'primaria',
  'secundaria':    'secundaria',
  'tecnico':       'tecnico',
  'técnico':       'tecnico',
  'universitario': 'universitario',
  'posgrado':      'posgrado',
};


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  🚀  FUNCIÓN PRINCIPAL — disparador onFormSubmit                         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Se ejecuta automáticamente cada vez que alguien envía el formulario.
 * @param {Object} e - Evento de envío de Google Forms.
 */
function onFormSubmit(e) {
  try {
    var itemResponses = e.response.getItemResponses();

    // Construir mapa: título (lowercase) → valor de respuesta
    var form = {};
    for (var i = 0; i < itemResponses.length; i++) {
      var titulo = itemResponses[i].getItem().getTitle().trim().toLowerCase();
      form[titulo] = itemResponses[i].getResponse();
    }

    Logger.log('[INFO] Respuestas capturadas: ' + JSON.stringify(form));

    // ── Construir payload para la API ────────────────────────────────────
    var payload = {
      nombre:          limpiar(obtener(form, ['nombre completo', 'nombre'])),
      edad:            parseInt(obtener(form, ['edad']) || '0'),
      genero:          mapearGenero(obtener(form, ['género', 'genero', 'sexo'])),
      estrato:         extraerEstrato(obtener(form, ['estrato socioeconómico', 'estrato socieconomico', 'estrato'])),
      departamento:    limpiar(obtener(form, ['departamento'])),
      municipio:       limpiar(obtener(form, ['municipio', 'ciudad'])),
      nivel_educativo: mapearNivel(obtener(form, ['nivel educativo', 'nivel_educativo', 'escolaridad'])),
      ocupacion:       obtener(form, ['ocupación', 'ocupacion', 'profesion', 'profesión']) || null,
      respuestas: [
        buildRespuesta(
          1,
          'Satisfacción con el servicio de salud en su municipio',
          'likert',
          parseInt(obtener(form, [
            'satisfacción con el servicio de salud en su municipio',
            'satisfaccion con el servicio de salud en su municipio',
            'satisfacción con el servicio de salud',
            'satisfaccion con el servicio de salud'
          ]) || '3')
        ),
        buildRespuesta(
          2,
          'Nivel de confianza en las instituciones colombianas (%)',
          'porcentaje',
          parseFloat(obtener(form, [
            'nivel de confianza en las instituciones colombianas (%)',
            'nivel de confianza en las instituciones',
            'nivel de confianza'
          ]) || '50')
        ),
        buildRespuesta(
          3,
          '¿Ha utilizado servicios digitales del Estado en el último mes?',
          'si_no',
          normalizarSiNo(obtener(form, [
            '¿ha utilizado servicios digitales del estado en el último mes?',
            '¿ha utilizado servicios digitales del estado?',
            '¿ha utilizado servicios digitales'
          ]))
        ),
      ],
      observaciones_generales: obtener(form, [
        'observaciones adicionales', 'observaciones', 'comentarios', 'comentario'
      ]) || null,
      fuente: 'google_forms',
    };

    Logger.log('[INFO] Payload construido: ' + JSON.stringify(payload));

    var resultado = enviarAAPI(payload);

    if (resultado) {
      Logger.log('[OK] Encuesta registrada. ID: ' + resultado.id_encuesta +
                 ' | Encuestado: ' + resultado.encuestado.nombre);
    } else {
      Logger.log('[WARN] La API no retornó datos — revisa el log de errores.');
    }

  } catch (err) {
    Logger.log('[ERROR] onFormSubmit falló: ' + err.toString());
    // Descomenta para recibir alertas por email cuando falle:
    // MailApp.sendEmail(EMAIL_ALERTAS, '⚠️ Error Webhook Encuestas', err.toString());
  }
}


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  🔧  HELPERS DE NORMALIZACIÓN                                            ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Busca el primer valor no vacío entre varias claves posibles.
 * Necesario porque los títulos con tildes pueden variar según el teclado.
 */
function obtener(data, claves) {
  for (var i = 0; i < claves.length; i++) {
    var val = data[claves[i]];
    if (val !== undefined && val !== null && val !== '') return val;
  }
  return null;
}

/** Limpia espacios extras y normaliza el texto. */
function limpiar(texto) {
  if (!texto) return '';
  return texto.toString().trim().replace(/\s+/g, ' ');
}

/** Normaliza el género al formato que acepta la API. */
function mapearGenero(valor) {
  if (!valor) return 'prefiero_no_decir';
  var key = valor.toString().toLowerCase().trim();
  return MAPA_GENERO[key] || 'prefiero_no_decir';
}

/**
 * Extrae el número del estrato aunque Google Forms envíe "3 - Medio-bajo".
 * Toma el primer dígito del string.
 */
function extraerEstrato(valor) {
  if (!valor) return 3;
  var match = valor.toString().match(/^(\d)/);
  if (match) return parseInt(match[1]);
  return parseInt(valor) || 3;
}

/** Normaliza el nivel educativo sin tildes. */
function mapearNivel(valor) {
  if (!valor) return 'universitario';
  var key = valor.toString().toLowerCase().trim()
    .replace(/á/g, 'a').replace(/é/g, 'e')
    .replace(/í/g, 'i').replace(/ó/g, 'o').replace(/ú/g, 'u');
  return MAPA_NIVEL[key] || 'universitario';
}

/**
 * Normaliza respuestas Sí/No de Google Forms.
 * Google Forms puede enviar "Sí", "Si", "Yes", "1", etc.
 */
function normalizarSiNo(valor) {
  if (!valor) return 'no';
  var v = valor.toString().toLowerCase().trim()
    .replace(/sí/g, 'si')
    .replace(/yes/g, 'si')
    .replace(/true/g, 'si')
    .replace(/1/g, 'si');
  return (v === 'si') ? 'si' : 'no';
}

/** Construye un objeto de respuesta para el array 'respuestas'. */
function buildRespuesta(id, enunciado, tipo, valor) {
  return {
    pregunta_id:   id,
    enunciado:     enunciado,
    tipo_pregunta: tipo,
    valor:         valor,
  };
}


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  📡  ENVÍO HTTP A LA API                                                 ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Envía el payload JSON al endpoint de la API usando UrlFetchApp.
 * @param {Object} payload - Objeto JavaScript a enviar como JSON.
 * @returns {Object|null} Respuesta JSON de la API o null en caso de error.
 */
function enviarAAPI(payload) {
  var opciones = {
    method:             'post',
    contentType:        'application/json',
    payload:            JSON.stringify(payload),
    muteHttpExceptions: true,   // Evita que errores HTTP rompan el script
  };

  try {
    var respuesta = UrlFetchApp.fetch(API_URL, opciones);
    var codigo    = respuesta.getResponseCode();
    var cuerpo    = respuesta.getContentText();

    if (codigo === 201) {
      Logger.log('[OK] HTTP 201 — Encuesta creada exitosamente');
      return JSON.parse(cuerpo);
    } else {
      Logger.log('[ERROR] HTTP ' + codigo + ' — Respuesta: ' + cuerpo);
      return null;
    }
  } catch (err) {
    Logger.log('[ERROR] Conexión fallida con la API: ' + err.toString());
    throw err;
  }
}


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  🧪  FUNCIÓN DE PRUEBA — Ejecútala manualmente para verificar           ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Prueba el webhook sin necesitar enviar el formulario.
 *
 * CÓMO USAR:
 *  1. Selecciona esta función en el menú desplegable del editor.
 *  2. Haz clic en "Ejecutar" (▶).
 *  3. Revisa el panel "Registros de ejecución" abajo.
 *  Si ves "[OK] Test exitoso", la integración funciona.
 */
function probarWebhook() {
  var testPayload = {
    nombre:          'Usuario de Prueba Google Forms',
    edad:            30,
    genero:          'femenino',
    estrato:         3,
    departamento:    'Cundinamarca',
    municipio:       'Bogota',
    nivel_educativo: 'universitario',
    ocupacion:       'Desarrolladora',
    respuestas: [
      {
        pregunta_id:   1,
        enunciado:     'Satisfacción con el servicio de salud en su municipio',
        tipo_pregunta: 'likert',
        valor:         4,
      },
      {
        pregunta_id:   2,
        enunciado:     'Nivel de confianza en las instituciones colombianas (%)',
        tipo_pregunta: 'porcentaje',
        valor:         70.0,
      },
      {
        pregunta_id:   3,
        enunciado:     '¿Ha utilizado servicios digitales del Estado en el último mes?',
        tipo_pregunta: 'si_no',
        valor:         'si',
      },
    ],
    observaciones_generales: 'Prueba de integración desde Apps Script',
    fuente: 'google_forms',
  };

  Logger.log('[TEST] Enviando payload de prueba a: ' + API_URL);
  var resultado = enviarAAPI(testPayload);

  if (resultado) {
    Logger.log('[TEST OK] ✅ Encuesta registrada. ID: ' + resultado.id_encuesta);
  } else {
    Logger.log('[TEST FALLIDO] ❌ Revisa API_URL y los logs anteriores.');
  }
}
