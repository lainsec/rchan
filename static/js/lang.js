// Función para cargar el archivo de traducción según el idioma seleccionado
function loadTranslations(language) {
    const filePath = `/lang/${language}.json`;

    // Intentar cargar traducciones desde localStorage
    const storedTranslations = localStorage.getItem(`translations_${language}`);
    
    if (storedTranslations) {
        // Si se encuentran traducciones almacenadas, aplicarlas directamente
        applyTranslations(JSON.parse(storedTranslations));
        console.log("Cargando traducciones desde localStorage.");
    } else {
        // Si no hay traducciones almacenadas, cargarlas desde el archivo
        fetch(filePath)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error al cargar el archivo de traducción: ${filePath}`);
                }
                return response.json();
            })
            .then(translations => {
                // Almacenar las traducciones en localStorage
                localStorage.setItem(`translations_${language}`, JSON.stringify(translations));
                // Aplicar las traducciones
                applyTranslations(translations);
                console.log("Cargando traducciones desde el archivo.");
            })
            .catch(error => {
                console.error("Error al cargar las traducciones:", error);
            });
    }
}

// Función para aplicar las traducciones al HTML
function applyTranslations(translations) {
    // Asignar el texto traducido a los elementos del navbar
    for (const key in translations.navbar) {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = translations.navbar[key];
        }
    }
}

// Función para cambiar el idioma
function changeLanguage(selectedLanguage) {
    localStorage.setItem('selectedLanguage', selectedLanguage); // Guardar idioma en localStorage
    loadTranslations(selectedLanguage); // Cargar y aplicar la traducción correspondiente
}

// Detectar cambio de idioma en el selector
document.getElementById('languageSelector').addEventListener('change', function () {
    const selectedLanguage = this.value; // Obtener el valor seleccionado en el <select>
    changeLanguage(selectedLanguage); // Cambiar el idioma
});

// Esperar a que el DOM esté completamente cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', () => {
    // Cargar el idioma seleccionado previamente o por defecto (por ejemplo, Portugués)
    const savedLanguage = localStorage.getItem('selectedLanguage') || 'pt'; // Usar el idioma guardado o 'pt' como predeterminado
    document.getElementById('languageSelector').value = savedLanguage; // Establecer el valor del selector
    loadTranslations(savedLanguage); // Cargar las traducciones
});