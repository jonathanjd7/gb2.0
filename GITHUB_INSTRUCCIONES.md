# 📋 Guía para Subir el Proyecto a GitHub

## 🚀 Pasos para Subir a GitHub

### 1. Crear Repositorio en GitHub

1. Ve a [GitHub.com](https://github.com)
2. Haz clic en "New repository"
3. **IMPORTANTE**: Marca el repositorio como **PRIVADO**
4. Nombre sugerido: `whatsapp-sender-pro`
5. **NO** inicialices con README (ya tenemos uno)

### 2. Inicializar Git Localmente

```bash
# En la carpeta del proyecto
git init
git add .
git commit -m "Initial commit: WhatsApp Sender Pro"
```

### 3. Conectar con GitHub

```bash
git remote add origin https://github.com/TU_USUARIO/whatsapp-sender-pro.git
git branch -M main
git push -u origin main
```

## 📁 Archivos y Carpetas a SUBIR ✅

### Archivos Principales (OBLIGATORIOS)
```
✅ whatsapp_sender_gui_mejorado.py    # Programa principal
✅ plantillas_mensajes.py             # Sistema de plantillas
✅ requirements.txt                   # Dependencias
✅ README.md                          # Documentación
✅ .gitignore                         # Archivos a ignorar
✅ LICENSE                            # Licencia MIT
✅ GITHUB_INSTRUCCIONES.md           # Esta guía
```

### Archivos de Configuración
```
✅ ejemplo_datos.xlsx                # Ejemplo de estructura (sin datos reales)
```

## 🚫 Archivos y Carpetas a NO SUBIR ❌

### Datos Sensibles (CRÍTICO)
```
❌ archivos_excel/                    # Carpeta con datos reales
❌ archivos_excel/*.xlsx             # Archivos Excel con clientes
❌ archivos_excel/*.xls              # Archivos Excel con clientes
❌ progreso.json                     # Datos de progreso temporal
```

### Sesiones y Datos Temporales
```
❌ whatsapp_session/                 # Sesión de WhatsApp Web
❌ whatsapp_session/*               # Todos los archivos de sesión
❌ *.log                            # Archivos de log
❌ debug.log                        # Logs de debug
```

### Archivos del Sistema
```
❌ __pycache__/                     # Cache de Python
❌ *.pyc                           # Bytecode de Python
❌ .DS_Store                        # Archivos de macOS
❌ Thumbs.db                        # Archivos de Windows
❌ .vscode/                         # Configuración de VS Code
❌ .idea/                           # Configuración de PyCharm
```

## 🔒 Seguridad y Privacidad

### ✅ Lo que SÍ es Seguro Subir
- Código fuente del programa
- Plantillas de mensajes (sin datos personales)
- Documentación y README
- Archivos de configuración (sin datos sensibles)
- Ejemplos de estructura (sin datos reales)

### ❌ Lo que NO es Seguro Subir
- Números de teléfono de clientes
- Nombres reales de clientes
- Datos de reservas
- Sesiones de WhatsApp Web
- Archivos de progreso con datos temporales

## 📋 Checklist Antes de Subir

### ✅ Verificaciones de Seguridad
- [ ] No hay archivos Excel con datos reales
- [ ] No hay números de teléfono en el código
- [ ] No hay nombres de clientes reales
- [ ] La carpeta `whatsapp_session` está en `.gitignore`
- [ ] El archivo `progreso.json` está en `.gitignore`
- [ ] El repositorio está marcado como PRIVADO

### ✅ Verificaciones de Contenido
- [ ] README.md está completo y actualizado
- [ ] requirements.txt contiene todas las dependencias
- [ ] .gitignore está configurado correctamente
- [ ] LICENSE está incluido
- [ ] Código está comentado y documentado

### ✅ Verificaciones Técnicas
- [ ] El programa funciona correctamente
- [ ] No hay errores de sintaxis
- [ ] Todas las importaciones están en requirements.txt
- [ ] Los archivos de ejemplo están incluidos

## 🚀 Comandos Git Completos

```bash
# 1. Verificar estado
git status

# 2. Ver qué archivos se van a subir
git add -n .

# 3. Agregar archivos (respetando .gitignore)
git add .

# 4. Verificar qué se va a commitear
git status

# 5. Hacer commit
git commit -m "Initial commit: WhatsApp Sender Pro v2.0"

# 6. Subir a GitHub
git push -u origin main
```

## 🔍 Verificar que Todo Esté Correcto

### Después de subir, verifica en GitHub:

1. **Archivos subidos**: Solo deben aparecer los archivos seguros
2. **Archivos NO subidos**: Verifica que no estén los archivos sensibles
3. **README**: Se muestra correctamente
4. **Privacidad**: El repositorio está marcado como privado

### Archivos que DEBEN aparecer en GitHub:
```
✅ whatsapp_sender_gui_mejorado.py
✅ plantillas_mensajes.py
✅ requirements.txt
✅ README.md
✅ .gitignore
✅ LICENSE
✅ GITHUB_INSTRUCCIONES.md
✅ ejemplo_datos.xlsx
```

### Archivos que NO deben aparecer en GitHub:
```
❌ archivos_excel/
❌ whatsapp_session/
❌ progreso.json
❌ *.log
❌ __pycache__/
```

## 🆘 Si Algo Sale Mal

### Si subiste archivos sensibles por accidente:

1. **NO hagas commit** de más cambios
2. **Elimina los archivos** del repositorio:
   ```bash
   git rm --cached archivos_excel/*
   git rm --cached progreso.json
   git rm --cached whatsapp_session/*
   git commit -m "Remove sensitive files"
   git push
   ```

3. **Verifica en GitHub** que los archivos se eliminaron

### Si necesitas actualizar .gitignore:

1. Edita `.gitignore`
2. Agrega los archivos que faltan
3. Haz commit y push:
   ```bash
   git add .gitignore
   git commit -m "Update .gitignore"
   git push
   ```

## 📞 Soporte

Si tienes problemas:
1. Revisa esta guía
2. Verifica el `.gitignore`
3. Consulta la documentación de Git
4. Contacta al equipo de desarrollo

---

**¡Recuerda: La seguridad de los datos de los clientes es lo más importante!** 🔒
