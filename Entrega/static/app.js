/**
 * RiskAPI - Interactividad y Visualización 🌸
 * Sistema de Análisis de Riesgo Crediticio
 */

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Parsea un string con formato numérico colombiano/internacional a float
 * Soporta: "1.500.000", "1,500,000", "1.500.000,50", "$1.500.000"
 */
function parseNumber(value) {
    if (!value) return 0;
    if (typeof value === 'number') return value;
    
    // Convertir a string y limpiar
    let str = value.toString().trim();
    
    // Quitar símbolos de moneda y espacios
    str = str.replace(/[$\s]/g, '');
    
    // Si está vacío después de limpiar
    if (!str) return 0;
    
    // Detectar formato
    const tieneComa = str.includes(',');
    const tienePunto = str.includes('.');
    
    if (tieneComa && tienePunto) {
        // Ambos presentes: el último es el decimal
        const lastComma = str.lastIndexOf(',');
        const lastDot = str.lastIndexOf('.');
        
        if (lastComma > lastDot) {
            // Formato EU: 1.234.567,89
            str = str.replace(/\./g, '').replace(',', '.');
        } else {
            // Formato US: 1,234,567.89
            str = str.replace(/,/g, '');
        }
    } else if (tieneComa) {
        // Solo comas: verificar si es decimal o miles
        const parts = str.split(',');
        if (parts.length === 2 && parts[1].length <= 2) {
            // Probable decimal: 1234,56
            str = str.replace(',', '.');
        } else {
            // Probable miles: 1,234,567
            str = str.replace(/,/g, '');
        }
    } else if (tienePunto) {
        // Solo puntos: verificar si es decimal o miles
        const parts = str.split('.');
        if (parts.length === 2 && parts[1].length <= 2) {
            // Probable decimal: 1234.56
            // Ya está en formato correcto
        } else {
            // Probable miles: 1.234.567
            str = str.replace(/\./g, '');
        }
    }
    
    const result = parseFloat(str);
    return isNaN(result) ? 0 : result;
}

document.addEventListener('DOMContentLoaded', () => {
    // Referencias al DOM
    const form = document.getElementById('analysis-form');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultsContainer = document.getElementById('results-container');
    const emptyState = document.getElementById('empty-state');
    const historyTableBody = document.getElementById('history-table-body');
    const filterRiesgo = document.getElementById('filter-riesgo');
    const btnClearHistory = document.getElementById('btn-clear-history');
    
    // Charts
    let composicionChart = null;
    let nivelChart = null;
    let historyChart = null;

    // ═══════════════════════════════════════════════════════════════════════════
    // CARGA INICIAL
    // ═══════════════════════════════════════════════════════════════════════════
    
    loadHistory();

    // ═══════════════════════════════════════════════════════════════════════════
    // MANEJO DEL FORMULARIO
    // ═══════════════════════════════════════════════════════════════════════════
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            municipio: document.getElementById('municipio').value.trim(),
            cartera_a: parseNumber(document.getElementById('cartera_a').value),
            cartera_b: parseNumber(document.getElementById('cartera_b').value),
            cartera_c: parseNumber(document.getElementById('cartera_c').value),
            cartera_d: parseNumber(document.getElementById('cartera_d').value),
            cartera_e: parseNumber(document.getElementById('cartera_e').value),
            total_cartera: parseNumber(document.getElementById('total_cartera').value),
            total_captaciones: parseNumber(document.getElementById('total_captaciones').value) || null
        };
        
        // Validar coherencia
        const sumaCarteras = payload.cartera_a + payload.cartera_b + payload.cartera_c + payload.cartera_d + payload.cartera_e;
        if (Math.abs(sumaCarteras - payload.total_cartera) > payload.total_cartera * 0.01) {
            Swal.fire({
                icon: 'warning',
                title: '⚠️ Inconsistencia detectada',
                html: `La suma de las categorías (${formatNumber(sumaCarteras)}) no coincide con el total (${formatNumber(payload.total_cartera)}).<br><br>
                       <small>¿Deseas continuar de todas formas?</small>`,
                showCancelButton: true,
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Corregir'
            }).then((result) => {
                if (result.isConfirmed) {
                    submitAnalysis(payload);
                }
            });
        } else {
            submitAnalysis(payload);
        }
    });

    async function submitAnalysis(payload) {
        const btn = form.querySelector('.btn-submit');
        const btnText = document.getElementById('btn-text');
        const loader = document.getElementById('btn-loader');
        
        // Mostrar loading
        btn.disabled = true;
        btnText.innerHTML = '<div class="loader" style="display:inline-block"></div> Procesando...';
        loader.style.display = 'inline-block';
        
        try {
            const response = await fetch('/analizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const data = await response.json();
                showResults(data);
                loadHistory();
                form.reset();
                
                // Scroll a resultados
                document.getElementById('resultados').scrollIntoView({ behavior: 'smooth' });
                
                Swal.fire({
                    icon: 'success',
                    title: '✅ Análisis completado',
                    text: `Municipio: ${data.municipio} | NPL: ${(data.indice_riesgo * 100).toFixed(2)}%`,
                    timer: 3000,
                    showConfirmButton: false
                });
            } else {
                const error = await response.json();
                Swal.fire({
                    icon: 'error',
                    title: '❌ Error',
                    text: error.detail || 'Error al procesar el análisis'
                });
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: '❌ Error de conexión',
                text: 'No se pudo conectar con el servidor'
            });
        } finally {
            btn.disabled = false;
            btnText.innerHTML = '<i class="fas fa-magic"></i> Ejecutar Análisis';
            loader.style.display = 'none';
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MOSTRAR RESULTADOS
    // ═══════════════════════════════════════════════════════════════════════════
    
    function showResults(data) {
        console.log('=== showResults llamado ===');
        console.log('Datos recibidos:', data);
        console.log('indice_riesgo:', data.indice_riesgo);
        console.log('nivel_riesgo:', data.nivel_riesgo);
        
        // Ocultar empty state, mostrar resultados
        if (emptyState) emptyState.style.display = 'none';
        if (resultsContainer) resultsContainer.style.display = 'block';

        // KPIs - verificar que los elementos existen
        const kpiNpl = document.getElementById('kpi-npl');
        const kpiNplDesc = document.getElementById('kpi-npl-desc');
        const kpiSana = document.getElementById('kpi-sana');
        const kpiMora = document.getElementById('kpi-mora');
        const kpiLiquidez = document.getElementById('kpi-liquidez');
        
        console.log('Elementos KPI:', { kpiNpl, kpiNplDesc, kpiSana, kpiMora, kpiLiquidez });

        if (kpiNpl) kpiNpl.textContent = (data.indice_riesgo * 100).toFixed(2) + '%';
        if (kpiNplDesc) kpiNplDesc.textContent = getRiskDescription(data.nivel_riesgo);
        if (kpiSana) kpiSana.textContent = (data.pct_cartera_sana || 0).toFixed(1) + '%';
        if (kpiMora) kpiMora.textContent = (data.pct_cartera_mora || 0).toFixed(1) + '%';
        if (kpiLiquidez) kpiLiquidez.textContent = data.ratio_liquidez ? data.ratio_liquidez.toFixed(2) : 'N/A';

        // Detalle
        const detailMunicipio = document.getElementById('detail-municipio');
        const detailNivel = document.getElementById('detail-nivel');
        const detailConcentracion = document.getElementById('detail-concentracion');
        const detailHhi = document.getElementById('detail-hhi');
        const resultadoMensajeSpan = document.querySelector('#resultado-mensaje span');
        
        console.log('Elementos Detalle:', { detailMunicipio, detailNivel, detailConcentracion, detailHhi, resultadoMensajeSpan });

        if (detailMunicipio) detailMunicipio.textContent = data.municipio || '-';
        if (detailNivel) detailNivel.textContent = formatRiskLevel(data.nivel_riesgo || 'sin_riesgo');
        if (detailConcentracion) detailConcentracion.textContent = (data.concentracion_riesgo || 0).toFixed(1) + '%';
        if (detailHhi) detailHhi.textContent = (data.hhi || 0).toFixed(4);
        if (resultadoMensajeSpan) resultadoMensajeSpan.textContent = data.mensaje || '-';

        // Estadísticos - mostrar si están disponibles
        const statMedia = document.getElementById('stat-media');
        const statVarianza = document.getElementById('stat-varianza');
        const statStd = document.getElementById('stat-std');
        const statCv = document.getElementById('stat-cv');

        if (statMedia) statMedia.textContent = data.media_cartera ? (data.media_cartera * 100).toFixed(2) + '%' : 'N/A';
        if (statVarianza) statVarianza.textContent = data.var_cartera ? data.var_cartera.toFixed(6) : 'N/A';
        if (statStd) statStd.textContent = data.std_cartera ? (data.std_cartera * 100).toFixed(2) + '%' : 'N/A';
        if (statCv) statCv.textContent = data.cv_cartera ? data.cv_cartera.toFixed(2) + '%' : 'N/A';

        // Actualizar color del mensaje según riesgo
        const mensajeBox = document.getElementById('resultado-mensaje');
        if (mensajeBox) {
            mensajeBox.className = 'mensaje-box';
            if (data.nivel_riesgo && data.nivel_riesgo.includes('critico')) {
                mensajeBox.style.borderLeftColor = '#DC3545';
                mensajeBox.style.background = 'linear-gradient(135deg, #F8D7DA, #FFE5E6)';
            } else if (data.nivel_riesgo && data.nivel_riesgo.includes('alto')) {
                mensajeBox.style.borderLeftColor = '#FD7E14';
                mensajeBox.style.background = 'linear-gradient(135deg, #FFE5D0, #FFF0E6)';
            } else if (data.nivel_riesgo && data.nivel_riesgo.includes('moderado')) {
                mensajeBox.style.borderLeftColor = '#FFC107';
                mensajeBox.style.background = 'linear-gradient(135deg, #FFF3CD, #FFF9E6)';
            } else {
                mensajeBox.style.borderLeftColor = '#28A745';
                mensajeBox.style.background = 'linear-gradient(135deg, #D4EDDA, #E8F5E9)';
            }
        }

        // Gráfico de composición (Pie Chart)
        createComposicionChart(data);

        // Gráfico de nivel (Bar Chart)
        createNivelChart(data);
        
        console.log('=== showResults finalizado ===');
    }

    function getRiskDescription(nivel) {
        const descriptions = {
            'sin_riesgo': 'Cartera perfectamente sana',
            'riesgo_bajo': 'Cartera sana, monitoreo routine',
            'riesgo_moderado': 'Alerta temprana, revisar',
            'riesgo_alto': 'Deterioro, acción requerida',
            'riesgo_critico': 'Crítico, intervención inmediata'
        };
        return descriptions[nivel] || 'Análisis completado';
    }

    function formatRiskLevel(nivel) {
        return nivel.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // GRÁFICOS
    // ═══════════════════════════════════════════════════════════════════════════
    
    function createComposicionChart(data) {
        const ctx = document.getElementById('composicion-chart').getContext('2d');

        if (composicionChart) {
            composicionChart.destroy();
        }

        // Calcular composición REAL basada en los datos del API
        // data.pct_cartera_sana = porcentaje de A
        // data.pct_cartera_mora = porcentaje de C+D+E
        // data.concentracion_riesgo = porcentaje de D+E dentro de la mora
        
        const pctA = data.pct_cartera_sana || 0;
        const pctMoraTotal = data.pct_cartera_mora || 0;
        const concentracion = (data.concentracion_riesgo || 0) / 100;
        
        // B lo estimamos como 10% de la mora no severa
        const pctMoraNoSevera = pctMoraTotal * (1 - concentracion);
        const pctB = Math.min(pctMoraNoSevera * 0.2, 5);
        const pctC = pctMoraNoSevera - pctB;
        
        // Mora severa (D+E) distribuida 60/40
        const pctMoraSevera = pctMoraTotal * concentracion;
        const pctD = pctMoraSevera * 0.6;
        const pctE = pctMoraSevera * 0.4;

        composicionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['A (Normal)', 'B (Obs)', 'C (Sub)', 'D (Dud)', 'E (Perd)'],
                datasets: [{
                    data: [pctA, pctB, pctC, pctD, pctE],
                    backgroundColor: [
                        '#28A745',  // Verde - A
                        '#17A2B8',  // Cyan - B
                        '#FFC107',  // Amarillo - C
                        '#FD7E14',  // Naranja - D
                        '#DC3545'   // Rojo - E
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                cutout: '55%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 12,
                            font: { family: 'Poppins', size: 9 },
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? (value / total * 100) : 0;
                                return `${context.label}: ${value.toFixed(1)}% (${pct.toFixed(1)}% del total)`;
                            }
                        }
                    }
                }
            }
        });
    }

    function createNivelChart(data) {
        const ctx = document.getElementById('nivel-chart').getContext('2d');

        if (nivelChart) {
            nivelChart.destroy();
        }

        // Crear distribución basada en el nivel ACTUAL del municipio
        // Mostramos en qué nivel cayó ESTE municipio específico
        const nivelActual = data.nivel_riesgo;
        
        const distribution = {
            'sin_riesgo': nivelActual === 'sin_riesgo' ? 100 : 0,
            'riesgo_bajo': nivelActual === 'riesgo_bajo' ? 100 : 0,
            'riesgo_moderado': nivelActual === 'riesgo_moderado' ? 100 : 0,
            'riesgo_alto': nivelActual === 'riesgo_alto' ? 100 : 0,
            'riesgo_critico': nivelActual === 'riesgo_critico' ? 100 : 0
        };

        nivelChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Sin Riesgo', 'Riesgo Bajo', 'Moderado', 'Riesgo Alto', 'Crítico'],
                datasets: [{
                    label: 'Nivel de Riesgo del Municipio',
                    data: Object.values(distribution),
                    backgroundColor: [
                        '#28A745',
                        '#17A2B8',
                        '#FFC107',
                        '#FD7E14',
                        '#DC3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF',
                    borderRadius: 8,
                    barThickness: 50
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                indexAxis: 'y',  // Barras horizontales para mejor visualización
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 105, 180, 0.1)' },
                        ticks: {
                            callback: (value) => value + '%',
                            font: { family: 'Poppins', size: 9 }
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: 'Poppins', size: 9 } }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                if (context.parsed.x === 100) {
                                    return '✓ ESTE es el nivel de riesgo del municipio';
                                }
                                return 'No aplica';
                            }
                        }
                    }
                }
            }
        });
    }

    function createHistoryChart(historyData) {
        const ctx = document.getElementById('history-chart').getContext('2d');

        if (historyChart) {
            historyChart.destroy();
        }

        // Limitar a los últimos 10 registros para que el gráfico no se haga "eterno"
        const maxRegistros = Math.min(historyData.length, 10);
        const limitedData = historyData.slice(0, maxRegistros);

        // Calcular el NPL máximo para dimensionar correctamente el eje Y
        const nplValues = limitedData.map(h => h.indice_riesgo * 100);
        const maxNPL = Math.max(...nplValues, 5);  // Mínimo 5% para que no se vea tan alto
        const suggestedMax = Math.ceil(maxNPL * 1.3);  // 30% más del máximo para espacio

        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: limitedData.map((item, i) => {
                    // Mostrar nombre corto del municipio en lugar de "#1", "#2"...
                    const nombre = item.municipio || `#${i + 1}`;
                    return nombre.length > 15 ? nombre.substring(0, 15) + '...' : nombre;
                }),
                datasets: [{
                    label: 'Índice NPL (%)',
                    data: nplValues,
                    borderColor: '#FF69B4',
                    backgroundColor: 'rgba(255, 105, 180, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,  // Menos curvatura para que se vea más natural
                    pointBackgroundColor: '#FFFFFF',
                    pointBorderColor: '#FF69B4',
                    pointBorderWidth: 3,
                    pointRadius: 7,
                    pointHoverRadius: 9,
                    pointHitRadius: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,  // Más ancho que alto
                scales: {
                    y: {
                        beginAtZero: true,
                        max: suggestedMax,  // Dimensionado dinámico
                        grid: { color: 'rgba(255, 105, 180, 0.15)' },
                        ticks: {
                            callback: (value) => value.toFixed(1) + '%',
                            font: { family: 'Poppins', size: 10 }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { 
                            font: { family: 'Poppins', size: 8 },
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 10
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#FF69B4',
                        borderWidth: 2,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            title: (context) => {
                                const item = limitedData[context[0].dataIndex];
                                return item.municipio || `Análisis #${context[0].dataIndex + 1}`;
                            },
                            label: (context) => {
                                const npl = context.parsed.y;
                                const nivel = limitedData[context.dataIndex].nivel_riesgo || '';
                                return [
                                    `NPL: ${npl.toFixed(2)}%`,
                                    `Nivel: ${nivel.replace('_', ' ').toUpperCase()}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CARGAR HISTORIAL
    // ═══════════════════════════════════════════════════════════════════════════
    
    async function loadHistory() {
        try {
            const response = await fetch('/historial');
            const data = await response.json();
            
            renderHistoryTable(data);
            createHistoryChart(data);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    function renderHistoryTable(data) {
        const filter = filterRiesgo.value;
        const filteredData = filter ? data.filter(item => item.nivel_riesgo === filter) : data;
        
        historyTableBody.innerHTML = '';
        
        if (filteredData.length === 0) {
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: var(--gris);">
                        <i class="fas fa-inbox" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
                        No hay análisis para mostrar
                    </td>
                </tr>
            `;
            return;
        }
        
        filteredData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td><strong>${item.municipio}</strong></td>
                <td>${(item.indice_riesgo * 100).toFixed(2)}%</td>
                <td><span class="badge badge-${item.nivel_riesgo}">${formatRiskLevel(item.nivel_riesgo)}</span></td>
                <td>${formatDate(item.fecha_analisis)}</td>
                <td>
                    <button class="btn-small btn-view" onclick="viewAnalysis(${item.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-small btn-delete" onclick="deleteAnalysis(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            historyTableBody.appendChild(row);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UPLOAD DE ARCHIVOS
    // ═══════════════════════════════════════════════════════════════════════════

    // Click para seleccionar archivo
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag & Drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('drop-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('drop-active');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) handleUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleUpload(e.target.files[0]);
    });

    async function handleUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        const originalText = dropZone.querySelector('.drop-text').textContent;
        dropZone.querySelector('.drop-text').textContent = '⏳ Procesando...';
        dropZone.style.opacity = '0.6';
        dropZone.style.pointerEvents = 'none';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: '✅ Archivo procesado',
                    html: `<b>${result.mensaje}</b><br>
                           ${result.ids_creados ? `IDs creados: ${result.ids_creados.join(', ')}` : ''}`,
                    timer: 4000,
                    showConfirmButton: false
                });
                loadHistory();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: '❌ Error',
                    text: result.detail || 'Error al procesar el archivo'
                });
            }
        } catch (error) {
            console.error('Upload error:', error);
            Swal.fire({
                icon: 'error',
                title: '❌ Error de conexión',
                text: 'No se pudo conectar con el servidor'
            });
        } finally {
            dropZone.querySelector('.drop-text').textContent = originalText;
            dropZone.style.opacity = '1';
            dropZone.style.pointerEvents = 'auto';
            fileInput.value = '';
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UPLOAD DE ARCHIVOS - DATOS.GOV.CO
    // ═══════════════════════════════════════════════════════════════════════════

    const dropZoneGov = document.getElementById('drop-zone-gov');
    const fileInputGov = document.getElementById('file-input-gov');
    const btnCargarGov = document.getElementById('btn-cargar-gov');

    if (dropZoneGov && fileInputGov && btnCargarGov) {
        // Click para seleccionar archivo
        dropZoneGov.addEventListener('click', () => fileInputGov.click());
        btnCargarGov.addEventListener('click', () => fileInputGov.click());

        // Drag & Drop
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZoneGov.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneGov.classList.add('drop-active');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZoneGov.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneGov.classList.remove('drop-active');
            }, false);
        });

        dropZoneGov.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) handleUploadGov(files[0]);
        });

        fileInputGov.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleUploadGov(e.target.files[0]);
        });
    }

    async function handleUploadGov(file) {
        // Validar que sea CSV
        if (!file.name.endsWith('.csv')) {
            Swal.fire({
                icon: 'warning',
                title: '⚠️ Archivo no válido',
                text: 'Por favor selecciona un archivo CSV (.csv)'
            });
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Mostrar loading en el botón
        const originalText = btnCargarGov.innerHTML;
        btnCargarGov.disabled = true;
        btnCargarGov.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

        try {
            const response = await fetch('/datos-gov/cargar', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: '✅ Archivo de Datos.gov.co procesado',
                    html: `
                        <b>${result.mensaje}</b><br><br>
                        <div style="text-align: left; font-size: 0.9rem;">
                            <p><strong>📊 Resumen:</strong></p>
                            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                <li>Total filas: ${result.total_filas || 0}</li>
                                <li>Municipios procesados: ${result.ids_creados ? result.ids_creados.length : 0}</li>
                                <li>Errores: ${result.errores || 0}</li>
                            </ul>
                        </div>
                    `,
                    showConfirmButton: true,
                    confirmButtonText: 'Ver historial',
                    showCancelButton: true,
                    cancelButtonText: 'Cerrar'
                }).then((swalResult) => {
                    if (swalResult.isConfirmed) {
                        document.getElementById('historial').scrollIntoView({ behavior: 'smooth' });
                        loadHistory();
                    }
                });
                loadHistory();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: '❌ Error',
                    text: result.detail || 'Error al procesar el archivo'
                });
            }
        } catch (error) {
            console.error('Upload error:', error);
            Swal.fire({
                icon: 'error',
                title: '❌ Error de conexión',
                text: 'No se pudo conectar con el servidor'
            });
        } finally {
            btnCargarGov.disabled = false;
            btnCargarGov.innerHTML = originalText;
            fileInputGov.value = '';
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // FILTROS Y ACCIONES
    // ═══════════════════════════════════════════════════════════════════════════
    
    filterRiesgo.addEventListener('change', () => {
        loadHistory();
    });

    btnClearHistory.addEventListener('click', async () => {
        const result = await Swal.fire({
            icon: 'warning',
            title: '¿Estás seguro?',
            text: 'Esta acción eliminará todos los análisis del historial',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar todo',
            cancelButtonText: 'Cancelar'
        });
        
        if (result.isConfirmed) {
            // Eliminar uno por uno (la API no tiene endpoint para borrar todo)
            const response = await fetch('/historial');
            const data = await response.json();
            
            for (const item of data) {
                await fetch(`/historial/${item.id}`, { method: 'DELETE' });
            }
            
            loadHistory();
            emptyState.style.display = 'block';
            resultsContainer.style.display = 'none';
            
            Swal.fire({
                icon: 'success',
                title: 'Historial limpiado',
                timer: 2000,
                showConfirmButton: false
            });
        }
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // FUNCIONES GLOBALES
    // ═══════════════════════════════════════════════════════════════════════════
    
    window.viewAnalysis = async (id) => {
        try {
            console.log('Cargando análisis ID:', id);

            const response = await fetch(`/historial/${id}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Datos recibidos:', data);

            // La API devuelve: { id, municipio, request, resultados, fecha_analisis }
            // Los campos que showResults necesita están en 'resultados' o en la raíz
            const resultadosCompletos = {
                // Primero los campos de la raíz
                id: data.id,
                municipio: data.municipio,
                fecha_analisis: data.fecha_analisis,
                // Luego los campos de 'resultados' (los que showResults necesita)
                ...(data.resultados || {}),
                // Y finalmente los campos directos por si la API los devuelve así
                indice_riesgo: data.indice_riesgo || (data.resultados && data.resultados.indice_riesgo) || 0,
                nivel_riesgo: data.nivel_riesgo || (data.resultados && data.resultados.nivel_riesgo) || 'sin_riesgo',
                pct_cartera_sana: data.pct_cartera_sana || (data.resultados && data.resultados.pct_cartera_sana) || 0,
                pct_cartera_mora: data.pct_cartera_mora || (data.resultados && data.resultados.pct_cartera_mora) || 0,
                ratio_liquidez: data.ratio_liquidez || (data.resultados && data.resultados.ratio_liquidez) || 0,
                concentracion_riesgo: data.concentracion_riesgo || (data.resultados && data.resultados.concentracion_riesgo) || 0,
                hhi: data.hhi || (data.resultados && data.resultados.hhi) || 0,
                mensaje: data.mensaje || (data.resultados && data.resultados.mensaje) || ''
            };

            console.log('Mostrando resultados:', resultadosCompletos);

            // Mostrar resultados con los datos CORRECTOS
            showResults(resultadosCompletos);

            // Scroll suave a resultados
            const resultadosSection = document.getElementById('resultados');
            if (resultadosSection) {
                resultadosSection.scrollIntoView({ behavior: 'smooth' });
            }

            // Mostrar mensaje
            Swal.fire({
                icon: 'success',
                title: 'Análisis cargado',
                text: `Municipio: ${resultadosCompletos.municipio} | NPL: ${(resultadosCompletos.indice_riesgo * 100).toFixed(2)}%`,
                timer: 2500,
                showConfirmButton: false
            });

        } catch (error) {
            console.error('Error al cargar análisis:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                html: `Error al cargar el análisis:<br><small>${error.message}</small>`
            });
        }
    };

    window.deleteAnalysis = async (id) => {
        const result = await Swal.fire({
            icon: 'warning',
            title: '¿Eliminar análisis?',
            text: 'Esta acción no se puede deshacer',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });
        
        if (result.isConfirmed) {
            try {
                const response = await fetch(`/historial/${id}`, { method: 'DELETE' });
                if (response.ok) {
                    loadHistory();
                    Swal.fire({
                        icon: 'success',
                        title: 'Eliminado',
                        timer: 1500,
                        showConfirmButton: false
                    });
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═══════════════════════════════════════════════════════════════════════════
    
    function formatNumber(num) {
        return new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(num);
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('es-CO', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
});
