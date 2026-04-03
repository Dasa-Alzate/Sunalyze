export class SearchBox {
    constructor(config) {
        this.config = config;
        this.selectedItem = null;
        
        // Elementos del DOM
        this.container = null;
        this.input = null;
        this.results = null;
        this.dropdown = null;
        this.select = null;
        
        // Estado
        this.isInitialized = false;
    }

    init() {
        try {
            // Obtener elementos del DOM
            this.container = document.getElementById(this.config.containerId);
            this.input = document.getElementById(this.config.inputId);
            this.results = document.getElementById(this.config.resultsId);
            this.dropdown = document.getElementById(this.config.dropdownId);
            this.select = document.getElementById(this.config.selectId);

            if (!this.container || !this.input || !this.results || !this.dropdown || !this.select) {
                throw new Error('Elementos del DOM no encontrados para SearchBox');
            }

            // Configurar placeholder
            if (this.config.placeholder) {
                this.input.placeholder = this.config.placeholder;
            }

            // Inicializar eventos
            this.initializeEvents();
            
            // Poblar select oculto
            this.populateSelect();
            
            this.isInitialized = true;
            console.log(`SearchBox ${this.config.containerId} inicializado correctamente`);
            
        } catch (error) {
            console.error(`Error inicializando SearchBox ${this.config.containerId}:`, error);
        }
    }

    initializeEvents() {
        // Evento focus para mostrar dropdown
        this.input.addEventListener('focus', () => {
            // Si no hay resultados mostrados, poblar con todos los elementos
            if (this.results.children.length === 0) {
                this.populateResults(this.config.data);
            }
            this.showDropdown();
        });
        
        // Evento input para búsqueda
        this.input.addEventListener('input', (e) => {
            const searchTerm = e.target.value.trim();
            this.performSearch(searchTerm);
        });

        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });

        // Navegación con teclado
        this.input.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
    }

    performSearch(searchTerm) {
        if (searchTerm.length === 0) {
            // Mostrar todos los elementos
            this.populateResults(this.config.data);
            this.showDropdown();
        } else {
            // Búsqueda con Fuse.js
            const results = this.config.fuseInstance.search(searchTerm);
            const filteredItems = results.map(result => result.item);
            
            if (filteredItems.length === 0) {
                this.showNoResults();
            } else {
                this.populateResults(filteredItems);
                this.showDropdown();
            }
        }
    }

    populateResults(data) {
        this.results.innerHTML = '';
        
        data.forEach(item => {
            const resultItem = this.createResultItem(item);
            this.results.appendChild(resultItem);
        });
    }

    createResultItem(item) {
        const resultItem = document.createElement('div');
        resultItem.className = 'flex p-2 rounded-md cursor-pointer transition-colors duration-200 bg-base-100 hover:bg-primary/10 hover:border-primary/30 focus:bg-primary/15 focus:border-primary/50 active:bg-primary/20 active:border-primary/60 border border-transparent';
        resultItem.tabIndex = 0;

        const displayText = this.formatDisplayText(item);

        // Crear elemento p con createElement
        const textElement = document.createElement('p');
        textElement.className = 'text-base-content font-medium';
        textElement.textContent = displayText;
        
        // Agregar el p al resultItem
        resultItem.appendChild(textElement);
        
        // Event listeners para el item
        this.attachItemEvents(resultItem, item);
        
        return resultItem;
    }

    attachItemEvents(resultItem, item) {
        resultItem.addEventListener('click', () => {
            this.selectItem(item);
        });
        
        resultItem.addEventListener('mouseenter', () => {
            resultItem.classList.add('bg-primary/10', 'border-primary/30');
        });

        resultItem.addEventListener('mouseleave', () => {
            if (!resultItem.classList.contains('bg-primary/15')) {
                resultItem.classList.remove('bg-primary/10', 'border-primary/30');
            }
        });

        resultItem.addEventListener('focus', () => {
            resultItem.classList.add('bg-primary/15', 'border-primary/50');
        });

        resultItem.addEventListener('blur', () => {
            resultItem.classList.remove('bg-primary/15', 'border-primary/50');
        });
        
        resultItem.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.selectItem(item);
            }
        });
    }

    selectItem(item) {
        // Actualizar el select oculto
        this.select.value = item.id;
        
        // Actualizar el input
        this.input.value = this.formatDisplayText(item);
        
        // Guardar la selección
        this.selectedItem = item;
        
        // Ejecutar callback si existe
        if (this.config.onSelect) {
            this.config.onSelect(item);
        }
        
        // Ocultar dropdown
        this.hideDropdown();
        
        console.log('Item seleccionado:', item.nombre);
    }

    formatDisplayText(item) {
        if (item.power) {
            if (item.power > 1000) {
                // Es inversor (kW)
                const powerMax = item.power_max || item.power;
                return `${item.nombre} (${(item.power/1000).toFixed(1)}kW / ${(powerMax/1000).toFixed(1)}kW)`;
            } else {
                // Es panel (W)
                return `${item.nombre} (${item.power}W)`;
            }
        }
        return item.nombre;
    }

    showNoResults() {
        this.results.innerHTML = '';
        
        const noResultsDiv = document.createElement('div');
        noResultsDiv.className = 'flex p-2 text-base-content/50 text-sm';
        noResultsDiv.textContent = 'No se encontraron resultados';
        
        this.results.appendChild(noResultsDiv);
        this.showDropdown();
    }

    showDropdown() {
        if (this.results.children.length > 0) {
            this.dropdown.classList.remove('hidden');
        }
    }

    hideDropdown() {
        this.dropdown.classList.add('hidden');
    }

    handleKeyboardNavigation(e) {
        const items = this.results.children;
        if (items.length === 0) return;
        
        const currentFocus = document.activeElement;
        let currentIndex = -1;
        
        // Encontrar el índice del elemento actualmente enfocado
        for (let i = 0; i < items.length; i++) {
            if (items[i] === currentFocus) {
                currentIndex = i;
                break;
            }
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                items[nextIndex].focus();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                items[prevIndex].focus();
                break;
                
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }

    populateSelect() {
        this.select.innerHTML = '';
        this.config.data.forEach(item => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = this.formatDisplayText(item);
            this.select.appendChild(option);
        });
    }

    getSelectedItem() {
        return this.selectedItem;
    }

    setData(newData) {
        this.config.data = newData;
        this.populateSelect();
    }

    // Método para limpiar la selección
    clear() {
        this.input.value = '';
        this.selectedItem = null;
        this.select.value = '';
        this.hideDropdown();
    }
}