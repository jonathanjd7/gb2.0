# 📞 Configuración de Columnas para Plantillas de Recogida

## 🎯 Funcionalidad Implementada

Se ha implementado una funcionalidad especial para las **plantillas de recogida** que permite buscar los números de teléfono de los clientes en la columna **"Nº Vuelo VUELTA"** en lugar de la columna "NIF" estándar.

## 📋 Plantillas Afectadas

Las siguientes plantillas utilizan esta nueva funcionalidad:

- **RecogidaTardes**: Para recogidas vespertinas
- **RecogidaMañana**: Para recogidas matutinas

## 🔧 Cómo Funciona

### Para Plantillas de Recogida:
1. **Columna Principal**: Busca automáticamente columnas que contengan "VUELTA" o "VUELO" en el nombre
2. **Extracción de Números**: Extrae solo los dígitos del campo encontrado
3. **Validación**: Requiere mínimo 9 dígitos para ser considerado un número válido
4. **Respaldo**: Si no encuentra columna de vuelo o el número no es válido, usa la columna "NIF"

### Para Otras Plantillas:
- **Columna Principal**: Usa la columna "NIF" estándar
- **Comportamiento**: Mantiene la funcionalidad original

## 📊 Formato de Archivo Excel

### Formato Normal (Columnas Separadas):
```
| Cliente | NIF | Nº Vuelo VUELTA | Matricula | Hora entrada | Fecha entrada |
|---------|-----|-----------------|-----------|--------------|---------------|
| Juan    | 123 | 612345678       | ABC123    | 14:30        | 2024-01-15    |
```

### Formato Especial (Todas las Columnas en Una):
```
Agencia	Cliente	NIF	Matricula	Vehículo	Ocup.	...	Nº Vuelo VUELTA	...
GOB	Juan	123	ABC123	Ford	2	...	612345678	...
```

## 🎮 Uso en la Interfaz

### 1. Seleccionar Plantilla de Recogida
- En el selector de plantillas, elegir "RecogidaTardes" o "RecogidaMañana"
- El sistema automáticamente detectará que debe buscar en columnas de vuelo

### 2. Analizar Datos
- Al hacer clic en "🔍 Analizar Datos", el sistema:
  - Buscará columnas que contengan "VUELTA" o "VUELO"
  - Mostrará información sobre las columnas encontradas
  - Extraerá números de teléfono de la columna apropiada

### 3. Información de Columnas
- Usar el botón "📋 Info Columnas" para ver:
  - Configuración actual según la plantilla
  - Columnas disponibles en el archivo
  - Estado de las columnas de vuelo y NIF

## 📝 Logs y Mensajes

### Mensajes Informativos:
```
📞 Plantilla de recogida detectada: Buscando números en columna 'Nº Vuelo VUELTA'
📋 Columnas de vuelo encontradas: Nº Vuelo VUELTA, Vuelo Ida
📞 Número encontrado en columna 'Nº Vuelo VUELTA': 612345678
```

### Mensajes de Advertencia:
```
⚠️ No se encontraron columnas con 'VUELTA' o 'VUELO'
🔄 Se usará la columna 'NIF' como respaldo
⚠️ Campo 'Nº Vuelo VUELTA' no contiene número válido: Vuelo123
```

## 🔍 Detección de Columnas

### Criterios de Búsqueda:
- **Contiene "VUELTA"**: Cualquier columna con "VUELTA" en el nombre
- **Contiene "VUELO"**: Cualquier columna con "VUELO" en el nombre
- **No distingue mayúsculas/minúsculas**: "vuelta", "VUELTA", "Vuelta" son válidos

### Ejemplos de Nombres de Columnas Válidos:
- "Nº Vuelo VUELTA"
- "Vuelo Ida"
- "Número Vuelo"
- "VUELTA"
- "Vuelo de Regreso"

## ⚠️ Consideraciones Importantes

### Validación de Números:
- **Mínimo 9 dígitos**: Para ser considerado un número de teléfono válido
- **Solo dígitos**: Se extraen únicamente los números del campo
- **Formato flexible**: Acepta números con o sin espacios, guiones, etc.

### Respaldo Automático:
- Si no se encuentra columna de vuelo → Usa columna "NIF"
- Si la columna de vuelo no contiene número válido → Usa columna "NIF"
- Si ninguna columna tiene número válido → Contacto descartado

### Compatibilidad:
- **Formato Normal**: Funciona con columnas separadas de Excel
- **Formato Especial**: Funciona con todas las columnas en una sola separadas por tabs
- **Retrocompatibilidad**: Las plantillas no-recogida mantienen comportamiento original

## 🧪 Pruebas y Verificación

### 1. Verificar Configuración:
- Usar botón "📋 Info Columnas" para ver configuración actual
- Verificar que se detecten las columnas correctas

### 2. Probar Extracción:
- Analizar datos y revisar logs
- Verificar que se extraigan números de la columna correcta
- Confirmar que los números sean válidos

### 3. Verificar Respaldo:
- Probar con archivo sin columnas de vuelo
- Confirmar que use columna "NIF" como respaldo

## 📞 Soporte

Si tienes problemas con esta funcionalidad:

1. **Verificar nombres de columnas**: Asegurar que contengan "VUELTA" o "VUELO"
2. **Revisar formato de números**: Los números deben tener al menos 9 dígitos
3. **Usar botón "Info Columnas"**: Para diagnosticar problemas de configuración
4. **Revisar logs**: Para información detallada sobre el proceso

---

**Desarrollado para GO BARAJAS** 🚗✈️
