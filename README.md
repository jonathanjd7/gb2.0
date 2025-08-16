# 🤖 WhatsApp Sender Pro - GO BARAJAS

## 📋 Descripción
Aplicación automatizada para envío masivo de mensajes de WhatsApp desde archivos Excel, específicamente diseñada para GO BARAJAS. Permite enviar recordatorios de reservas de manera eficiente y personalizada.

## ✨ Características Principales

### 🔗 **Nueva Funcionalidad: Consolidación de Reservas Duplicadas**
- **Agrupación automática**: Detecta automáticamente múltiples reservas del mismo cliente para la misma fecha
- **Mensaje unificado**: Envía un solo mensaje consolidado con todas las matrículas y ocupantes
- **Configuración flexible**: Opción para habilitar/deshabilitar la consolidación
- **Estadísticas detalladas**: Muestra información sobre contactos consolidados y reservas totales

### 📊 **Procesamiento Inteligente de Datos**
- Soporte para múltiples formatos de archivos Excel
- Validación automática de números de teléfono (españoles e internacionales)
- Filtrado automático de tipos de plaza excluidos (PREMIUM, SUPERIOR)
- Extracción de fecha y hora de entrada

### 🎨 **Interfaz Moderna y Responsiva**
- Diseño limpio y profesional
- Vista previa de datos en tiempo real
- Log detallado de eventos
- Estadísticas de consolidación
- Redimensionamiento automático

### 📝 **Sistema de Plantillas Avanzado**
- Editor de plantillas integrado
- Variables dinámicas: `{nombre}`, `{matricula}`, `{hora}`, `{ocupantes}`, etc.
- Soporte completo para emojis y caracteres Unicode
- Plantilla específica para múltiples vehículos (`CitaMultiple`)

### 🤖 **Automatización Robusta**
- Envío automático con Selenium
- Persistencia de sesión de WhatsApp Web
- Manejo de errores y reintentos
- Sistema de progreso guardado
- Delays configurables entre mensajes

## 🚀 Instalación y Uso

### Requisitos
```bash
pip install -r requirements.txt
```

### Ejecución
```bash
python gobarajasmasivo.py
```

## 📁 Estructura de Archivos

```
GBPRUEBAS2.0/
├── gobarajasmasivo.py          # Aplicación principal
├── plantillas_mensajes.py      # Plantillas de mensajes
├── requirements.txt            # Dependencias
├── README.md                   # Documentación
├── archivos_excel/            # Carpeta para archivos Excel
└── whatsapp_session/          # Sesión persistente de WhatsApp
```

## ⚙️ Configuración

### Consolidación de Duplicados
- **Habilitado por defecto**: Agrupa automáticamente reservas del mismo cliente
- **Criterios de agrupación**: Teléfono + Fecha de entrada
- **Información consolidada**: 
  - Todas las matrículas en un solo mensaje
  - Total de ocupantes sumado
  - Número de reservas agrupadas

### Formatos de Archivo Soportados
1. **Formato Normal**: Columnas separadas de Excel
2. **Formato Especial**: Todas las columnas en una sola columna separada por tabs

### Variables de Plantilla Disponibles
- `{nombre}`: Nombre del cliente
- `{matricula}`: Matrícula(s) del vehículo
- `{hora}`: Hora de la reserva
- `{fecha_actual}`: Fecha actual
- `{ocupantes}`: Número de ocupantes
- `{reservas_count}`: Número de reservas (consolidados)

## 📊 Estadísticas y Monitoreo

### Vista Previa de Datos
- Muestra los primeros 20 contactos
- Indica contactos consolidados con 🔗
- Información de matrículas múltiples
- Total de ocupantes por contacto

### Log de Eventos
- Timestamps precisos
- Niveles de logging configurables
- Información detallada de consolidación
- Errores y advertencias

### Estadísticas en Tiempo Real
- Total de contactos
- Contactos consolidados
- Total de reservas procesadas

## 🔧 Funciones Avanzadas

### Gestión de Sesión
- **Verificación automática**: Detecta sesión persistente al iniciar
- **Limpieza de sesión**: Opción para eliminar sesión guardada
- **Reconexión automática**: Manejo robusto de desconexiones

### Sistema de Progreso
- **Guardado automático**: Progreso guardado en archivo JSON
- **Reanudación**: Continuar desde donde se quedó
- **Información detallada**: Fecha y contacto del último envío

### Validación de Datos
- **Números españoles**: 9 dígitos (6xxx, 7xxx) o 11 dígitos (34xxx)
- **Números internacionales**: 10-15 dígitos con códigos de país
- **Filtrado automático**: Tipos de plaza excluidos
- **Limpieza de datos**: Caracteres problemáticos removidos

## 📱 Plantillas de Mensaje

### Plantilla Principal (RecordatorioCita)
Mensaje estándar para recordatorios de reserva individual.

### Plantilla Múltiple (CitaMultiple)
Específica para contactos consolidados con múltiples vehículos.

### Plantillas de Recogida
- **RecogidaMañana**: Para recogidas matutinas
- **RecogidaTardes**: Para recogidas vespertinas

### Plantilla Premium
Para servicios premium con recogida en terminal.

## 🛠️ Solución de Problemas

### Errores Comunes
1. **Chrome no inicia**: Verificar instalación de Chrome y ChromeDriver
2. **QR no se escanea**: Asegurar que el teléfono esté conectado
3. **Mensajes no se envían**: Verificar conexión a internet y estado de WhatsApp

### Logs y Debugging
- Nivel de logging configurable (DEBUG, INFO, WARNING, ERROR)
- Logging a archivo opcional
- Información detallada de errores

## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## 🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias y mejoras.

---

**Desarrollado para GO BARAJAS** 🚗✈️ 