import Fuse from 'https://cdn.jsdelivr.net/npm/fuse.js@6.6.2/dist/fuse.esm.js';
import { SearchBox } from './searchbox.js';

// Dark mode toggle
const darkSwitch = document.getElementById('dark-switch');
if (darkSwitch) {
  darkSwitch.checked = document.documentElement.getAttribute('data-theme') === 'forest';
  darkSwitch.addEventListener('change', () => {
    const theme = darkSwitch.checked ? 'forest' : 'emerald';
    document.documentElement.setAttribute('data-theme', theme);
    
    if (darkSwitch.checked) {
        document.body.classList.add("dark");
    } else {
        document.body.classList.remove("dark");
    }

    localStorage.setItem('sunalyze-theme', theme);
  });
}

// Variables globales
let panels = [];
let inverters = [];
let fusePanels;
let fuseInverters;
let noPanels;
let results_data;
let currentDiagram;

// Instancias de SearchBox
let panelSearchBox;
let inverterSearchBox;

// Elementos del DOM
const necesidadValue = document.getElementById("necesidad-value");
const selectAutoconsumo = document.getElementById("select-autoconsumo");
const latitudValue = document.getElementById("latitud-value");
const longitudValue = document.getElementById("longitud-value");
const inclinacionValue = document.getElementById("inclinacion-value");
const azimutValue = document.getElementById("azimut-value");
const chk = document.getElementById("chk-coplanar");
const group = document.getElementById("coplanar-group");
const siguientePaso1 = document.getElementById("siguiente-paso-1");
const siguientePaso3 = document.getElementById("siguiente-paso-3");
const printUpdateBtn = document.getElementById("print-update-btn");

// Contenedores de pasos
const step2Content = document.getElementById("step2-content");
const step2Hr = document.getElementById("step2-hr");
const step2Container = document.getElementById("step2-container");

const deviceInverterSection = document.getElementById("device-inverter-section");
const deviceSubmitSection = document.getElementById("device-submit-section");

const step4Content = document.getElementById("step4-content");
const step4Hr = document.getElementById("step4-hr");
const step4Container = document.getElementById("step4-container");

const step5Content = document.getElementById("step5-content");
const step5Hr = document.getElementById("step5-hr");
const step5Container = document.getElementById("step5-container");

// Secciones de resultados
const calculosSection = document.getElementById("calculos-section");
const errorMessage = document.getElementById("error-message");

const MAX_VOLTAGE_DROP_RATIO = 0.015;
const COPPER_RESISTIVITY = 0.01724;

const FUSE_CONFIG = {
    panels: {
        keys: [
            { name: 'nombre', weight: 0.7 },
            { name: 'power', weight: 0.2 },
            { name: 'voc', weight: 0.05 },
            { name: 'vmp', weight: 0.05 }
        ],
        threshold: 0.3,
        includeScore: true,
        minMatchCharLength: 2,
        ignoreLocation: true,
        shouldSort: true
    },
    inverters: {
        keys: [
            { name: 'nombre', weight: 0.7 },
            { name: 'power', weight: 0.2 },
            { name: 'vmax', weight: 0.1 }
        ],
        threshold: 0.4,
        includeScore: true,
        minMatchCharLength: 2,
        ignoreLocation: true,
        shouldSort: true
    }
};

// Event Listeners
chk?.addEventListener("change", e => {
    group?.classList.toggle("hidden", !e.target.checked);
});

siguientePaso1?.addEventListener("click", e => {
    showStep2Content();
});

siguientePaso3?.addEventListener("click", handleCompleteAnalysis);

document.getElementById('chk-show-all-inverters')?.addEventListener('change', () => {
    if (getSelectedPanel()) handlePanelAnalysis();
});

// Funciones principales
async function loadEquipmentData() {
    try {
        const panelsResponse = await fetch('/api/panels');
        if (!panelsResponse.ok) throw new Error('Error cargando paneles');
        panels = await panelsResponse.json();

        const invertersResponse = await fetch('/api/inverters');
        if (!invertersResponse.ok) throw new Error('Error cargando inversores');
        inverters = await invertersResponse.json();

        // Inicializar Fuse.js
        initializeFuse();

        // Inicializar SearchBoxes
        initializeSearchBoxes();

    } catch (error) {
        console.error('Error cargando datos:', error);
        showError('Error cargando los datos del equipo');
    }
}

function initializeFuse() {
    fusePanels = new Fuse(panels, FUSE_CONFIG.panels);
    fuseInverters = new Fuse(inverters, FUSE_CONFIG.inverters);
}

function initializeSearchBoxes() {
    // SearchBox para paneles (paso 2)
    panelSearchBox = new SearchBox({
        containerId: 'panel-search-container',
        inputId: 'panel-search-input',
        resultsId: 'panel-results',
        dropdownId: 'panel-dropdown',
        selectId: 'select-placas',
        placeholder: 'Buscar panel (nombre, potencia...)',
        fuseInstance: fusePanels,
        data: panels,
        onSelect: (item) => {
            handlePanelAnalysis();
        }
    });

    // SearchBox para inversores (paso 3) - se inicializa vacío
    inverterSearchBox = new SearchBox({
        containerId: 'inverter-search-container',
        inputId: 'inverter-search-input',
        resultsId: 'inverter-results',
        dropdownId: 'inverter-dropdown',
        selectId: 'select-inversores',
        placeholder: 'Buscar inversor compatible...',
        fuseInstance: fuseInverters,
        data: [], // Inicialmente vacío
        onSelect: (item) => {}
    });

    panelSearchBox.init();
    inverterSearchBox.init();
}

// Funciones para mostrar pasos
function showStep2Content() {
    // Mostrar el HR con transición
    step2Hr.classList.remove('hidden');
    step2Hr.classList.add('opacity-0');
    
    // Agregar padding al contenedor
    step2Container.classList.add('p-4');
    
    // Mostrar el contenido
    step2Content.classList.remove('hidden');
    
    // Animaciones escalonadas con Tailwind
    setTimeout(() => {
        // Animación del HR
        step2Hr.classList.remove('opacity-0');
        step2Hr.classList.add('opacity-100', 'transition-opacity', 'duration-300');
    }, 50);
    
    setTimeout(() => {
        // Animación del contenido principal
        step2Content.classList.remove('opacity-0', 'translate-y-4');
        step2Content.classList.add('opacity-100', 'translate-y-0');
        (step2Content.closest('.card') || step2Content).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
}


function showStep4Content() {
    step4Hr.classList.remove('hidden');
    step4Hr.classList.add('opacity-0');
    step4Container.classList.add('p-4');
    step4Content.classList.remove('hidden');
    
    setTimeout(() => {
        step4Hr.classList.remove('opacity-0');
        step4Hr.classList.add('opacity-100', 'transition-opacity', 'duration-300');
    }, 50);
    
    setTimeout(() => {
        step4Content.classList.remove('opacity-0', 'translate-y-4');
        step4Content.classList.add('opacity-100', 'translate-y-0');
        (step4Content.closest('.card') || step4Content).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
}

function toggleAdvancedOptions() {
    const optionsContainer = document.getElementById('advanced-options');
    const arrow = document.getElementById('advanced-arrow');
    
    if (optionsContainer.classList.contains('max-h-0')) {
        // Mostrar opciones
        optionsContainer.classList.remove('max-h-0', 'opacity-0');
        optionsContainer.classList.add('max-h-96', 'opacity-100');
        arrow.classList.add('rotate-180');
    } else {
        // Ocultar opciones
        optionsContainer.classList.remove('max-h-96', 'opacity-100');
        optionsContainer.classList.add('max-h-0', 'opacity-0');
        arrow.classList.remove('rotate-180');
    }
}

let updateWireQueue = Promise.resolve();

function updateWire(e, a) {
    updateWireQueue = updateWireQueue
        .catch(() => {})
        .then(() => runWireUpdate(e, a));
    return updateWireQueue;
}

async function runWireUpdate(e, a) {
    try {
        // Validar que los elementos existen
        const input_a = document.getElementById("input-length-" + a);
        const b = a === 1 ? 2 : 1
        if (!input_a) {
            throw new Error(`Input para tramo ${a} no encontrado`);
        }

        // Paso 1: Calcular sección del tramo A
        await calculateWireSection(a);

        // Pequeña pausa para asegurar que el DOM se actualice
        await new Promise(resolve => setTimeout(resolve, 50));

        // Paso 2: Calcular longitud del tramo B basado en A
        await calculateLengthByLength(a);

        // Pequeña pausa para asegurar que el DOM se actualice
        await new Promise(resolve => setTimeout(resolve, 50));

        // Paso 3: Calcular sección del tramo B
        await calculateWireSection(b);

    } catch (error) {
        console.error(`❌ Error en updateWire para tramo ${a}:`, error);
        // Puedes mostrar un mensaje al usuario si lo deseas
    }
}

function buildAnalysisBody(extra) {
    const selectedPanel = getSelectedPanel();
    return {
        latitud: latitudValue.value,
        longitud: longitudValue.value,
        coplanar: chk.checked,
        inclinacion: chk.checked ? inclinacionValue.value : 0,
        azimut: chk.checked ? 180 + parseFloat(azimutValue.value) : 180,
        panel_id: selectedPanel.id,
        autoconsumo: selectAutoconsumo.value,
        necesidad: necesidadValue.value,
        ...extra
    };
}

async function handlePanelAnalysis() {
    clearErrors();
    const selectedPanel = getSelectedPanel();

    if (!selectedPanel) {
        showError('Por favor selecciona un panel');
        return;
    }

    const loading = showLoading('step2');

    try {
        const res = await fetch('/api/panel-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildAnalysisBody({
                show_all_inverters: document.getElementById('chk-show-all-inverters')?.checked || false
            }))
        });

        if (!res.ok) {
            throw new Error(await readErrorMessage(res, 'Error en el análisis de paneles'));
        }
        
        const data = await res.json();

        // Hidratar el searchbox de inversores con los compatibles
        if (data.compatible_inverters && data.compatible_inverters.length > 0) {
            inverterSearchBox.setData(data.compatible_inverters);
            deviceInverterSection.classList.remove("hidden");
            deviceSubmitSection.classList.remove("hidden");
            setTimeout(() => {
                deviceInverterSection.classList.remove("opacity-0", "translate-y-4");
                deviceInverterSection.classList.add("opacity-100", "translate-y-0");
            }, 50);
        } else {
            deviceInverterSection.classList.add("hidden");
            deviceSubmitSection.classList.add("hidden");
            showError('No se encontraron inversores compatibles para esta configuración');
        }
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading(loading);
    }
}

async function handleCompleteAnalysis() {
    clearErrors();
    showStep4Content();

    const selectedPanel = getSelectedPanel();
    const selectedInverter = getSelectedInverter();

    if (!selectedPanel || !selectedInverter) {
        showError('Por favor selecciona un panel y un inversor');
        return;
    }

    const loading = showLoading('step4');

    try {
        const res = await fetch('/api/panel-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildAnalysisBody({
                inverter_id: selectedInverter.id
            }))
        });

        if (!res.ok) {
            throw new Error(await readErrorMessage(res, 'Error en el análisis completo'));
        }
        
        const data = await res.json();
        results_data = { ...results_data, ...data };

        displayCompleteResults(data);

        noPanels = Math.ceil(data.cell_amount);

        await loadAndRenderDiagram(data, selectedPanel, selectedInverter);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading(loading);
    }
}

function safeFixed(value, digits) {
    const num = Number(value);
    return Number.isFinite(num) ? num.toFixed(digits) : null;
}

async function readErrorMessage(res, fallback) {
    try {
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            const err = await res.json();
            return err.error || fallback;
        }
    } catch (parseError) {
        console.warn('No se pudo interpretar el cuerpo de error', parseError);
    }
    return res.statusText || fallback;
}

function displayCompleteResults(data) {
    calculosSection.innerHTML = '';
    calculosSection.classList.remove("hidden");

    const irradiancia = data.annual_irradiance_kWh_m2;
    const unidadIrradiancia = data.meta?.outputs?.hourly?.variables?.["Gb(i)"]?.units || '';

    // Irradiancia
    const nombre = document.createElement('p');
    nombre.textContent = 'Irradiancia del lugar';
    nombre.className = 'text-base-content font-medium pt-2 pb-1 ps-2';

    const valor = document.createElement('p');
    valor.textContent = `${irradiancia} ${unidadIrradiancia}`;
    valor.className = 'text-accent font-semibold pt-2 pb-1';

    calculosSection.appendChild(nombre);
    calculosSection.appendChild(valor);

    // Resultados completos
    const candidateItems = [
        { label: 'Beta óptimo', value: safeFixed(data.beta_optimal, 1), suffix: "º" },
        { label: 'Energía a convertir (primaria)', value: safeFixed(data.sec_net_energy, 2), suffix: " MWh" },
        { label: 'Energía a producir (secundaria)', value: safeFixed(data.sec_energy, 1), suffix: " MWh" },
        { label: 'Superficie necesaria', value: safeFixed(data.cell_area, 2), suffix: " m²" },
        { label: 'Cantidad de paneles', value: Number.isFinite(Number(data.cell_amount)) ? safeFixed(data.cell_amount, 2) + " ≈ " + Math.ceil(Number(data.cell_amount)) + " placas" : null, suffix: "" },
        { label: 'Potencia pico de campo', value: safeFixed(data.total_field_power, 2), suffix: " kW" },
        { label: 'Paneles máximos por cadena', value: Number.isFinite(Number(data.max_cell_amount)) ? Math.floor(Number(data.max_cell_amount)) + " placas" : null, suffix: "" },
        { label: 'Eficiencia total del sistema', value: safeFixed(Number(data.total_y) * 100, 1), suffix: "%" },
    ];

    const items = candidateItems
        .filter(item => item.value !== null)
        .map(item => ({ label: item.label, value: item.value + item.suffix }));

    items.forEach((item, i) => {
        const lbl = document.createElement('p');
        const colorClass = i % 2 === 0 ? "bg-base-300" : "";
        lbl.textContent = item.label;
        lbl.className = 'text-base-content font-medium pt-2 pb-1 ps-2 ' + colorClass;

        const val = document.createElement('p');
        val.textContent = item.value;
        val.className = 'text-accent font-semibold pt-2 pb-1 ' + colorClass;

        calculosSection.appendChild(lbl);
        calculosSection.appendChild(val);
    });

    if (data.selected_inverter) {
        const inverterHeader = document.createElement('p');
        inverterHeader.textContent = 'Inversor seleccionado';
        inverterHeader.className = 'bg-base-300 font-medium text-base-content pt-2 pb-1 ps-2 mt-3';

        const inverterName = document.createElement('p');
        inverterName.textContent = data.selected_inverter.nombre;
        inverterName.className = 'text-accent font-semibold bg-base-300 pt-2 pb-1 mt-3';

        calculosSection.appendChild(inverterHeader);
        calculosSection.appendChild(inverterName);
    }

    const imprimirMemoriaBtn = document.createElement('button');

    imprimirMemoriaBtn.id = 'imprimir-memoria-btn';
    imprimirMemoriaBtn.className = 'btn btn-primary mt-2 col-span-2';
    imprimirMemoriaBtn.textContent = 'Abrir formulario de memoria de cálculo';

    imprimirMemoriaBtn.addEventListener('click', function() {
        step5Content.classList.remove("hidden", "opacity-0");
        step5Hr.classList.remove("hidden");
        (step5Content.closest('.card') || step5Content).scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    calculosSection.appendChild(imprimirMemoriaBtn);
}

printUpdateBtn?.addEventListener('click', function() {
    const errorEl = document.getElementById('memoria-validation-error');
    errorEl.classList.add('hidden');
    errorEl.textContent = '';

    const selectedPanel = getSelectedPanel();
    const selectedInverter = getSelectedInverter();

    if (!selectedPanel || !selectedInverter || !results_data) {
        errorEl.textContent = 'Debes completar los pasos 1-3 antes de generar la memoria.';
        errorEl.classList.remove('hidden');
        return;
    }

    const inclinacionValue = document.getElementById("inclinacion-value").value;
    const azimutValue = document.getElementById("azimut-value").value;
    const FSystemObjective = document.getElementById("f-system-objective");
    const FBatteries = document.getElementById("f-batteries");
    const FPanelsDisposition = document.getElementById("f-panels-disposition");

    const disposition = FPanelsDisposition.value;

    // Campos del formulario que requieren validación
    const requiredFields = [
        { id: 'f-location', label: 'Localidad' },
        { id: 'f-client-name', label: 'Nombre del Cliente' },
        { id: 'f-address', label: 'Dirección' },
        { id: 'f-zipcode', label: 'Código Postal' },
        { id: 'f-catastral-reference', label: 'Referencia Catastral' },
        { id: 'f-energy-company-cups', label: 'CUPS' },
        { id: 'f-hired-power-kw', label: 'Potencia Contratada' },
        { id: 'f-input-v', label: 'Voltaje de Entrada' },
        { id: 'f-wire-ground-length', label: 'Longitud Cable Tierra' },
        { id: 'f-protections-dc-thermal-v-max', label: 'Voltaje Máximo Protección DC' },
        { id: 'f-protections-dc-breaker-i', label: 'Corriente Fusibles DC' },
        { id: 'f-protections-ac-thermal-i', label: 'Corriente Magnetotérmico AC' },
        { id: 'f-protections-ac-diff-i', label: 'Corriente Diferencial AC' },
        { id: 'f-protections-ac-transitory-surge-model', label: 'Modelo Protección Sobretensión AC' },
        { id: 'f-mppt-inputs', label: 'Entradas MPPT' },
    ];

    const missing = [];
    for (const field of requiredFields) {
        const el = document.getElementById(field.id);
        if (!el || !el.value.trim()) {
            missing.push(field.label);
            el?.classList.add('border-red-500');
        } else {
            el.classList.remove('border-red-500');
        }
    }

    if (missing.length > 0) {
        errorEl.textContent = `Campos obligatorios vacíos: ${missing.join(', ')}`;
        errorEl.classList.remove('hidden');
        errorEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    const formData = {
        panel_id: selectedPanel.id,
        inverter_id: selectedInverter.id,
        location: document.getElementById("f-location").value.trim(),
        client_name: document.getElementById("f-client-name").value.trim(),
        address: document.getElementById("f-address").value.trim(),
        zipcode: document.getElementById("f-zipcode").value.trim(),
        catastral_reference: document.getElementById("f-catastral-reference").value.trim(),
        energy_company_name: document.getElementById("f-energy-company-name").value,
        energy_company_cups: document.getElementById("f-energy-company-cups").value.trim(),
        hired_power_kw: document.getElementById("f-hired-power-kw").value,
        input_v: document.getElementById("f-input-v").value,
        input_v_type: document.getElementById("f-input-v-type").value,
        inyection_type: FSystemObjective.value === "1" ? "con" : "sin",
        panels_inclination_verbosed: !inclinacionValue ? "Inclinación nula" : `una inclinación de ${inclinacionValue}º con respecto al horizonte`,
        panels_azimut_verbosed: !azimutValue ? "la mejor orientación sur posible" : `una orientación de ${azimutValue}º con respecto al sur`,
        panels_peak_power_kw: results_data.total_field_power,
        panels_number: Math.ceil(results_data.cell_amount),
        panels_place: document.getElementById("f-panels-place").value,
        panels_disposition: disposition,
        panels_surface: results_data.cell_area ? results_data.cell_area.toFixed(2) : '',
        panels_inclination: inclinacionValue || '0',
        panels_azimut: azimutValue || '0',
        orientation_loss_verbosed: results_data.irradiance_factor_loss <= 0.5 ? "de 0%" : `de alrededor de ${((1 - results_data.irradiance_factor_loss)*100).toFixed(0)}%`,
        shadows_loss_verbosed: "0%",
        panel_temp_min_limit: results_data.coldest_temperature,
        panel_temp_max_limit: 75,
        inverter_place: document.getElementById("f-inverter-place").value,
        inverter_phases: "monofásico",
        anti_pouring_verbosed: FSystemObjective.value === "1"
            ? "La instalación transmitirá automáticamente la potencia sobrante del sistema a la red pública"
            : "La instalación contará con un sistema anti vertido, que ajustará la potencia activa de equipo de transformación de DC-AC y evitará que se viertan excedentes de energía a la red pública",
        batteries_verbosed: FBatteries.value === "1"
            ? "El proyecto contará con baterías que almacenarán energía que será suministrada al inversor cuando los paneles no puedan abastecer la totalidad de la demanda"
            : "El proyecto no cuenta con baterías, así no se prevé ningún tipo de acumulación eléctrica. Si bien que en el futuro se plantearía la instalación de las mismas",
        wire_dc_length: results_data.wire_length_1 || (document.getElementById('input-length-1')?.value) || '',
        wire_dc_section: results_data.wire_section_1 || (document.getElementById('txt-section-1')?.textContent) || '',
        wire_ac_length: results_data.wire_length_2 || (document.getElementById('input-length-2')?.value) || '',
        wire_ac_section: Math.max(6, parseFloat(results_data.wire_section_2 || document.getElementById('txt-section-2')?.textContent || '6')).toString(),
        wire_ground_length: document.getElementById("f-wire-ground-length").value,
        wire_ground_section: Math.max(6, parseFloat(results_data.wire_section_2 || document.getElementById('txt-section-2')?.textContent || '6')).toString(),
        protections_dc_thermal_v_max: document.getElementById("f-protections-dc-thermal-v-max").value,
        protections_dc_breaker_i: document.getElementById("f-protections-dc-breaker-i").value,
        protections_ac_thermal_i: document.getElementById("f-protections-ac-thermal-i").value,
        protections_ac_diff_i: document.getElementById("f-protections-ac-diff-i").value,
        protections_ac_transitory_surge_model: document.getElementById("f-protections-ac-transitory-surge-model").value.trim(),
        mppt_inputs: document.getElementById("f-mppt-inputs").value.trim(),
        panels_output_i_max_expected: results_data.total_field_power,
        panels_output_i_max_oversized: (results_data.total_field_power * 1.25).toFixed(2),
        inverter_output_i_max_expected: selectedInverter.I_max_output,
        latitude: document.getElementById("latitud-value").value,
        longitude: document.getElementById("longitud-value").value,
        altitude: results_data.altitude || '',
        annual_irradiance: results_data.annual_irradiance_kWh_m2 || '',
        annual_production: results_data.annual_production || '',
        is_coplanar: chk.checked ? '1' : '0',
        monthly_production: JSON.stringify(results_data.monthly_production || []),
        monthly_irradiance: JSON.stringify(results_data.monthly_irradiance || []),
        annual_consumption: necesidadValue.value,
        date: new Date().toLocaleDateString('es-ES'),
    };

    // Crear form oculto y enviarlo en nueva pestaña
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/imprimir/memoria-pdf';
    form.target = '_blank';

    for (const [key, value] of Object.entries(formData)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value ?? '';
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
});


async function loadAndRenderDiagram(analysisData, selectedPanel, selectedInverter) {
    try {
        // Preparar datos para el endpoint del diagrama
        const diagramData = {
            panel_id: selectedPanel.id,
            inverter_id: selectedInverter.id,
            field_power: analysisData.total_field_power || '0',
            panel_amount: Math.ceil(analysisData.cell_amount) || '0',
            needed_surface: analysisData.cell_area ? analysisData.cell_area.toFixed(2) : '0',
            beta_optimal: analysisData.beta_optimal ? analysisData.beta_optimal.toFixed(2) : '0',
            max_panels_per_string: analysisData.max_cell_amount ? Math.round(analysisData.max_cell_amount) : '0',
            total_yield: analysisData.total_y ? Math.round(analysisData.total_y * 100) : '0',
            first_section: '6',
            second_section: '6',
            first_length: '10',
            second_length: '15',
            panel_protection_v: safeFixed(analysisData.panel_protection_v, 2) ?? '0',
            panel_protection_i: safeFixed(analysisData.panel_protection_i, 2) ?? '0',
        };

        const diagramResponse = await fetch('/api/diagrama-completo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(diagramData)
        });

        if (!diagramResponse.ok) {
            throw new Error('Error al cargar el diagrama');
        }

        // Obtener el HTML del diagrama
        const diagramHTML = await diagramResponse.text();
        
        const diagram = document.createElement("div");
        diagram.innerHTML = diagramHTML;

        if (currentDiagram && currentDiagram.parentNode) {
            currentDiagram.parentNode.removeChild(currentDiagram);
        }
        step4Content.appendChild(diagram);
        currentDiagram = diagram;

        const advancedOptionsBtn = document.getElementById("advanced-options-btn");
        if (advancedOptionsBtn) {
            advancedOptionsBtn.addEventListener('click', toggleAdvancedOptions);
        }

        const firstLengthInput = document.getElementById('input-length-1');
        const secondLengthInput = document.getElementById('input-length-2');
        
        if (firstLengthInput) {
            firstLengthInput.addEventListener('change', function(e) {
                updateWire(e, 1);
            });
        }
        
        if (secondLengthInput) {
            secondLengthInput.addEventListener('change', function(e) {
                updateWire(e, 2);
            });
        }

    } catch (error) {
        console.error('❌ Error cargando el diagrama:', error);
        // No mostramos error al usuario para no confundir, solo log
    }
}

// Loading
function showLoading(step) {
    const loading = document.createElement("div");
    loading.className = "h-full w-full flex justify-center";
    
    const spinner = document.createElement("span");
    spinner.className = "loading loading-spinner loading-lg text-primary m-6";
    
    loading.appendChild(spinner);
    
    // Agregar al contenedor correcto según el paso
    if (step === 'step2') {
        step2Content.appendChild(loading);
    } else if (step === 'step4') {
        step4Content.appendChild(loading);
    }
    
    return loading;
}

function hideLoading(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
        loadingElement.parentNode.removeChild(loadingElement);
    }
}

function showError(message) {
    calculosSection.classList.add("hidden");
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function clearErrors() {
    errorMessage.textContent = '';
    errorMessage.classList.add('hidden');
    calculosSection.classList.add("hidden");
}

async function calculateWireSection(n) {
    try {
        // Obtener valores de los selects avanzados
        const installationType = document.getElementById('select-installation').value;
        const material = document.getElementById('select-material').value;
        const conductors = document.getElementById('select-conductors').value;
        const input = document.getElementById("input-length-" + n);
        const length = input.value;
        
        // Calcular i_section según el valor de n
        let i_section;
        if (n === 1) {
            i_section = getSelectedPanel().imp;
        } else if (n === 2) {
            i_section = getSelectedInverter().I_max_output;
        } else {
            throw new Error('Valor de n no válido. Debe ser 1 o 2.');
        }
        
        // Hacer request al endpoint
        const response = await fetch('/api/wires/calculate-section', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tipo: installationType,
                material: material,
                no_conductores: parseInt(conductors),
                i_section: parseFloat(i_section)
            })
        });

        if (!response.ok) {
            throw new Error(await readErrorMessage(response, 'Error al calcular la sección'));
        }

        const data = await response.json();
        
        // Renderizar el resultado
        const sectionElement = document.getElementById(`txt-section-${n}`);
        const noConductores1 = document.getElementById(`txt-no-conductors-1`);
        const noConductores2 = document.getElementById(`txt-no-conductors-2`);
        noConductores1.innerText = parseInt(conductors)
        noConductores2.innerText = parseInt(conductors)

        if (sectionElement) {
            sectionElement.textContent = `${data.seccion}`;
            results_data[`wire_section_${n}`] = data.seccion;
        } else {
            console.warn(`Elemento txt-section-${n} no encontrado`);
        }
        
        return data.seccion;
        
    } catch (error) {
        console.error(`❌ Error calculando sección para tramo ${n}:`, error);
        
        // Mostrar error en el elemento
        const sectionElement = document.getElementById(`txt-section-${n}`);
        if (sectionElement) {
            sectionElement.textContent = 'Error';
            sectionElement.classList.add('text-red-500');
        }
        
        throw error;
    }
}

async function calculateLengthByLength(a) {
    try {
        const input_a = document.getElementById("input-length-" + a);
        
        // Obtener los valores como números
        const section_a_text = document.getElementById("txt-section-" + a).textContent;
        const section_a = parseFloat(section_a_text.replace('mm²', ''));
        
        const b = a === 1 ? 2 : 1;
        const input_b = document.getElementById("input-length-" + b);

        const section_b_text = document.getElementById("txt-section-" + b).textContent;
        const section_b = parseFloat(section_b_text.replace('mm²', ''));

        const current_a = getSelectedPanel().imp;
        const current_b = getSelectedInverter().I_max_output;
        const vmp = getSelectedPanel().vmp;

        const length_a = parseFloat(input_a.value);

        const length_b = (((vmp * noPanels * MAX_VOLTAGE_DROP_RATIO) / (2 * COPPER_RESISTIVITY)) - (length_a * current_a / section_a)) * section_b / current_b;

        input_b.value = length_b.toFixed(2);
        results_data[`wire_length_${b}`] = length_b.toFixed(2);

    } catch (error) {
        console.error(`❌ Error en calculateLengthByLength para tramo ${a}:`, error);
        throw error; // Propagar el error para que updateWire lo capture
    }
}

// Getters
function getSelectedPanel() {
    return panelSearchBox ? panelSearchBox.getSelectedItem() : null;
}

function getSelectedInverter() {
    return inverterSearchBox ? inverterSearchBox.getSelectedItem() : null;
}

// Inicializar la aplicación
document.addEventListener('DOMContentLoaded', function() {
    loadEquipmentData();
});

window.updateWire = updateWire;

// Sticky header shrink effect
(function() {
    const headers = document.querySelectorAll('.sticky.top-16');
    const stickyOffset = 64; // top-16 = 4rem
    const zone = 30; // px de transición antes del punto sticky

    const items = Array.from(headers).map(el => ({
        el,
        number: el.querySelector('p'),
        subtitle: el.querySelector('span'),
    }));

    let ticking = false;

    function lerp(from, to, t) {
        return from + (to - from) * t;
    }

    function update() {
        items.forEach(({ el, number, subtitle }) => {
            const dist = el.getBoundingClientRect().top - stickyOffset;
            const t = Math.max(0, Math.min(1, 1 - dist / zone));

            if (t === 0) {
                number.style.fontSize = '';
                subtitle.style.fontSize = '';
                el.style.paddingBlock = '';
                return;
            }

            number.style.fontSize = `${lerp(3, 1.875, t)}rem`;
            subtitle.style.fontSize = `${lerp(1.875, 1.25, t)}rem`;
            el.style.paddingBlock = `${lerp(1, 0.5, t)}rem`;
        });
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(update);
            ticking = true;
        }
    }, { passive: true });
})();