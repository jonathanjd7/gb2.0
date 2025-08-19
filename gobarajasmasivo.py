import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import pandas as pd
import random
import os
import json
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote

# Imports de Selenium (se importan cuando se necesitan para evitar errores si no están instalados)
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from webdriver_manager.chrome import ChromeDriverManager

from plantillas_mensajes import PLANTILLAS_DISPONIBLES, obtener_plantilla, listar_plantillas

# Constantes para gestión de progreso y sesión
PROGRESO_FILE = "progreso.json"
SESSION_DIR = os.path.join(os.getcwd(), "whatsapp_session")

# Constantes de configuración
DEFAULT_DELAY_MIN = 3
DEFAULT_DELAY_MAX = 5
DEFAULT_PLANTILLA = "RecordatorioCita"

# Constantes de tiempo (en segundos)
TIMEOUT_WHATSAPP_CONNECTION = 30
TIMEOUT_QR_SCAN = 120
TIMEOUT_FIELD_SEARCH = 15
TIMEOUT_FIRST_CONTACT = 15
TIMEOUT_BETWEEN_MESSAGES_MIN = 20
TIMEOUT_BETWEEN_MESSAGES_MAX = 25

# Constantes de filtros
TIPOS_PLAZA_EXCLUIDOS = ['PREMIUM', 'SUPERIOR']
MIN_COLUMNAS_FORMATO_ESPECIAL = 6

# Constantes para consolidación de contactos
CONSOLIDAR_DUPLICADOS = True  # Habilitar consolidación por defecto

# Constantes de rangos Unicode para emojis
EMOJI_RANGES = [
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
    (0x2600, 0x26FF),    # Miscellaneous Symbols
    (0x2700, 0x27BF)     # Dingbats
]

# Clases de excepción específicas
class WhatsAppSenderError(Exception):
    """Excepción base para errores del WhatsApp Sender"""
    pass

class ChromeInitializationError(WhatsAppSenderError):
    """Error al inicializar Chrome"""
    pass

class WhatsAppConnectionError(WhatsAppSenderError):
    """Error al conectar con WhatsApp Web"""
    pass

class MessageSendError(WhatsAppSenderError):
    """Error al enviar mensaje"""
    pass

class FileProcessingError(WhatsAppSenderError):
    """Error al procesar archivo Excel"""
    pass

class TemplateError(WhatsAppSenderError):
    """Error en plantilla de mensaje"""
    pass

class ElementNotFoundError(WhatsAppSenderError):
    """Error al encontrar elemento en WhatsApp Web"""
    pass

class WhatsAppSenderGUIMejorado:
    """
    Clase principal para la aplicación WhatsApp Sender Pro.
    
    Esta clase maneja toda la funcionalidad de la aplicación, incluyendo:
    - Interfaz gráfica de usuario
    - Procesamiento de archivos Excel
    - Envío automático de mensajes por WhatsApp Web
    - Gestión de plantillas de mensajes
    - Sistema de logging y manejo de errores
    
    Attributes:
        root: Ventana principal de Tkinter
        excel_path: Ruta del archivo Excel seleccionado
        driver: Instancia del WebDriver de Selenium
        is_running: Estado del proceso de envío
        contactos: Lista de contactos procesados
        plantilla_actual: Plantilla de mensaje seleccionada
        delay_min/max: Delays para envío de mensajes
        numeros_extranjeros: Configuración para números extranjeros
        _element_cache: Cache para elementos de WhatsApp Web
        _log_level: Nivel de logging actual
        _log_to_file: Si el logging a archivo está activado
        _log_file: Nombre del archivo de log
    """
    
    def __init__(self, root):
        """
        Inicializar la aplicación WhatsApp Sender Pro.
        
        Args:
            root: Ventana principal de Tkinter
        """
        self.root = root
        self.root.title("🤖 WhatsApp Sender Pro - GO BARAJAS")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f2f5")
        
        # Variables
        self.excel_path = tk.StringVar()
        self.driver = None
        self.is_running = False
        self.contactos = []
        self.plantilla_actual = tk.StringVar(value=DEFAULT_PLANTILLA)
        self.delay_min = tk.IntVar(value=DEFAULT_DELAY_MIN)
        self.delay_max = tk.IntVar(value=DEFAULT_DELAY_MAX)
        self.numeros_extranjeros = tk.BooleanVar(value=True)  # Habilitar por defecto
        self.consolidar_duplicados = tk.BooleanVar(value=CONSOLIDAR_DUPLICADOS)  # Consolidar duplicados por defecto
        
        # Cache para elementos de WhatsApp Web
        self._element_cache = {}
        
        # Configuración de logging
        self._log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR
        self._log_to_file = False
        self._log_file = "whatsapp_sender.log"
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_interface()
        
        # Verificar sesión persistente al iniciar
        self.verificar_sesion_whatsapp()
        
        # Verificar progreso guardado
        self.progreso_guardado = self.cargar_progreso()
        if self.progreso_guardado > 0:
            self.log_message(f"📋 Progreso guardado detectado: {self.progreso_guardado} contactos procesados")
        
    def setup_styles(self):
        """Configurar estilos modernos"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores modernos
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 24, 'bold'), 
                       foreground='#1a73e8',
                       background='#f0f2f5')
        
        style.configure('Section.TLabelframe', 
                       font=('Segoe UI', 12, 'bold'),
                       foreground='#1a73e8',
                       background='#ffffff')
        
        style.configure('Section.TLabelframe.Label', 
                       font=('Segoe UI', 12, 'bold'),
                       foreground='#1a73e8',
                       background='#ffffff')
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background='#34a853',
                       foreground='white')
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background='#1a73e8',
                       foreground='white')
        
        style.configure('Warning.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background='#ea4335',
                       foreground='white')
        
    def create_interface(self):
        """Crear interfaz mejorada con redimensionamiento"""
        
        # Configurar redimensionamiento de la ventana principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal que se expande
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configurar grid del frame principal
        main_frame.grid_rowconfigure(0, weight=1)  # Fila del contenido
        main_frame.grid_columnconfigure(0, weight=1)  # Columna principal
        
        # Contenedor principal con paneles (fila 0)
        container = tk.Frame(main_frame, bg="#f0f0f0")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configurar grid del contenedor con pesos para mejor distribución
        container.grid_rowconfigure(0, weight=1)  # Para que los paneles crezcan verticalmente
        container.grid_columnconfigure(0, weight=1)  # Panel izquierdo
        container.grid_columnconfigure(1, weight=2)  # Panel derecho - más espacio
        
        # Panel izquierdo
        left_panel = tk.Frame(container, bg="#ffffff", relief="flat", bd=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        # Panel derecho
        right_panel = tk.Frame(container, bg="#ffffff", relief="flat", bd=1)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        
        # Crear secciones
        self.create_file_section(left_panel)
        self.create_template_section(left_panel)
        self.create_config_section(left_panel)
        self.create_controls_section(left_panel)
        
        self.create_preview_section(right_panel)
        self.create_log_section(right_panel)
        self.create_stats_section(right_panel)
        
    def create_file_section(self, parent):
        """Sección de archivo Excel"""
        file_frame = ttk.LabelFrame(parent, text="📁 Archivo Excel", style='Section.TLabelframe')
        file_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 8))
        parent.grid_columnconfigure(0, weight=1)
        
        # Selección de archivo
        file_entry_frame = tk.Frame(file_frame, bg="#ffffff")
        file_entry_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        file_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(file_entry_frame, text="Archivo:", font=("Segoe UI", 10, "bold"), 
                bg="#ffffff", fg="#202124").grid(row=0, column=0, sticky="w")
        
        entry_frame = tk.Frame(file_entry_frame, bg="#ffffff")
        entry_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        file_entry_frame.grid_columnconfigure(0, weight=1)
        
        self.file_entry = tk.Entry(entry_frame, textvariable=self.excel_path, 
                                  font=("Segoe UI", 10), bg="#ffffff", fg="#202124",
                                  relief="solid", bd=1)
        self.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        entry_frame.grid_columnconfigure(0, weight=1)
        
        browse_btn = tk.Button(entry_frame, text="📂 Buscar", command=self.browse_file,
                              font=("Segoe UI", 10, "bold"), bg="#1a73e8", fg="white",
                              relief="flat", bd=0, padx=20, pady=8)
        browse_btn.grid(row=0, column=1)
        
        # Botón analizar
        analyze_btn = tk.Button(file_frame, text="🔍 Analizar Datos", command=self.analyze_data,
                               font=("Segoe UI", 10, "bold"), bg="#34a853", fg="white",
                               relief="flat", bd=0, padx=20, pady=8)
        analyze_btn.grid(row=1, column=0, pady=(0, 15))
        
    def create_template_section(self, parent):
        """Sección de plantillas"""
        template_frame = ttk.LabelFrame(parent, text="📝 Editor de Plantillas", style='Section.TLabelframe')
        template_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=8)
        parent.grid_rowconfigure(1, weight=1)
        
        # Selector de plantillas
        template_select_frame = tk.Frame(template_frame, bg="#ffffff")
        template_select_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        template_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(template_select_frame, text="Plantillas predefinidas:", 
                font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#202124").grid(row=0, column=0, sticky="w")
        
        select_frame = tk.Frame(template_select_frame, bg="#ffffff")
        select_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        template_select_frame.grid_columnconfigure(0, weight=1)
        
        self.template_combo = ttk.Combobox(select_frame, textvariable=self.plantilla_actual,
                                          values=listar_plantillas(), state="readonly",
                                          font=("Segoe UI", 10))
        self.template_combo.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        select_frame.grid_columnconfigure(0, weight=1)
        self.template_combo.bind('<<ComboboxSelected>>', self.load_template)
        
        load_btn = tk.Button(select_frame, text="📥 Cargar", command=self.load_template,
                            font=("Segoe UI", 9, "bold"), bg="#1a73e8", fg="white",
                            relief="flat", bd=0, padx=15, pady=5)
        load_btn.grid(row=0, column=1)
        
        # Variables disponibles
        vars_frame = tk.Frame(template_frame, bg="#ffffff")
        vars_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        tk.Label(vars_frame, text="Variables disponibles:", 
                font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#202124").grid(row=0, column=0, sticky="w")
        
        # Obtener variables dinámicamente desde plantillas_mensajes
        from plantillas_mensajes import obtener_variables
        variables = obtener_variables()
        vars_text_str = ", ".join(variables.keys())
        
        vars_text = tk.Label(vars_frame, text=vars_text_str,
                            font=("Segoe UI", 9), bg="#e8f0fe", fg="#1a73e8",
                            relief="solid", bd=1, padx=10, pady=5)
        vars_text.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Editor de texto
        editor_frame = tk.Frame(template_frame, bg="#ffffff")
        editor_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 10))
        template_frame.grid_rowconfigure(2, weight=1)
        
        self.template_text = scrolledtext.ScrolledText(editor_frame, height=18,
                                                      font=("Segoe UI", 10),
                                                      bg="#ffffff", fg="#202124",
                                                      relief="solid", bd=1,
                                                      wrap=tk.WORD)
        self.template_text.grid(row=0, column=0, sticky="nsew")
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        
        # Botones de plantilla
        btn_frame = tk.Frame(template_frame, bg="#ffffff")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        tk.Button(btn_frame, text="🔄 Restaurar", command=self.restore_template,
                 font=("Segoe UI", 9, "bold"), bg="#fbbc04", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=0, padx=(0, 10))
        
        tk.Button(btn_frame, text="👁️ Vista Previa", command=self.preview_message,
                 font=("Segoe UI", 9, "bold"), bg="#1a73e8", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=1, padx=(0, 10))
        
        tk.Button(btn_frame, text="📋 Ver Todas", command=self.show_templates,
                 font=("Segoe UI", 9, "bold"), bg="#9c27b0", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=2, padx=(0, 10))
        
        tk.Button(btn_frame, text="🧪 Probar Formato", command=self.probar_formato_plantilla,
                 font=("Segoe UI", 9, "bold"), bg="#ff9800", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=3, padx=(0, 10))
        
        tk.Button(btn_frame, text="😊 Probar Emojis", command=self.probar_emojis,
                 font=("Segoe UI", 9, "bold"), bg="#e91e63", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=4)
        
        # Botón para mostrar información de configuración de columnas
        tk.Button(btn_frame, text="📋 Info Columnas", command=self.mostrar_info_columnas,
                 font=("Segoe UI", 9, "bold"), bg="#607d8b", fg="white",
                 relief="flat", bd=0, padx=15, pady=5).grid(row=0, column=5)
    
    def create_config_section(self, parent):
        """Sección de configuración"""
        config_frame = ttk.LabelFrame(parent, text="⚙️ Configuración", style='Section.TLabelframe')
        config_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=8)
        
        # Frame principal más compacto
        main_config_frame = tk.Frame(config_frame, bg="#ffffff")
        main_config_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        config_frame.grid_columnconfigure(0, weight=1)
        
        # Delays en una sola fila
        delay_frame = tk.Frame(main_config_frame, bg="#ffffff")
        delay_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        main_config_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(delay_frame, text="Delay (seg):", 
                font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#202124").grid(row=0, column=0, sticky="w")
        
        tk.Label(delay_frame, text="Mín:", 
                font=("Segoe UI", 9), bg="#ffffff", fg="#5f6368").grid(row=0, column=1, sticky="w", padx=(15, 5))
        
        min_delay = tk.Entry(delay_frame, textvariable=self.delay_min,
                            font=("Segoe UI", 9), bg="#ffffff", fg="#202124",
                            relief="solid", bd=1, width=8)
        min_delay.grid(row=0, column=2, sticky="w", padx=(0, 10))
        
        tk.Label(delay_frame, text="Máx:", 
                font=("Segoe UI", 9), bg="#ffffff", fg="#5f6368").grid(row=0, column=3, sticky="w", padx=(0, 5))
        
        max_delay = tk.Entry(delay_frame, textvariable=self.delay_max,
                            font=("Segoe UI", 9), bg="#ffffff", fg="#202124",
                            relief="solid", bd=1, width=8)
        max_delay.grid(row=0, column=4, sticky="w")
        
        # Opciones en una sola fila
        options_frame = tk.Frame(main_config_frame, bg="#ffffff")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        # Opción para números extranjeros
        extranjeros_check = tk.Checkbutton(options_frame, 
                                          text="🌍 Números extranjeros",
                                          variable=self.numeros_extranjeros,
                                          font=("Segoe UI", 9, "bold"),
                                          bg="#ffffff", fg="#202124",
                                          selectcolor="#e8f0fe",
                                          activebackground="#ffffff",
                                          activeforeground="#202124")
        extranjeros_check.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        # Opción para consolidar duplicados
        consolidar_check = tk.Checkbutton(options_frame, 
                                         text="🔗 Consolidar duplicados",
                                         variable=self.consolidar_duplicados,
                                         font=("Segoe UI", 9, "bold"),
                                         bg="#ffffff", fg="#202124",
                                         selectcolor="#e8f0fe",
                                         activebackground="#ffffff",
                                         activeforeground="#202124")
        consolidar_check.grid(row=0, column=1, sticky="w")
        
        # Información compacta
        info_frame = tk.Frame(main_config_frame, bg="#ffffff")
        info_frame.grid(row=2, column=0, sticky="ew")
        
        info_label = tk.Label(info_frame,
                             text="💡 Números extranjeros: 10-15 dígitos | Consolidar: Agrupa reservas del mismo cliente",
                             font=("Segoe UI", 8), bg="#ffffff", fg="#5f6368")
        info_label.grid(row=0, column=0, sticky="w")
    
    def create_controls_section(self, parent):
        """Sección de controles"""
        control_frame = ttk.LabelFrame(parent, text="🎮 Controles", style='Section.TLabelframe')
        control_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=8)
        
        # Botones principales
        btn_frame = tk.Frame(control_frame, bg="#ffffff")
        btn_frame.grid(row=0, column=0, pady=10)
        control_frame.grid_columnconfigure(0, weight=1)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Iniciar Envío Automático", command=self.start_sending,
                                  font=("Segoe UI", 10, "bold"), bg="#34a853", fg="white",
                                  relief="flat", bd=0, padx=20, pady=8, width=12)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Detener", command=self.stop_sending,
                                 font=("Segoe UI", 10, "bold"), bg="#ea4335", fg="white",
                                 relief="flat", bd=0, padx=20, pady=8, width=12,
                                 state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        clear_btn = tk.Button(btn_frame, text="🧹 Limpiar Log", command=self.clear_log,
                             font=("Segoe UI", 10, "bold"), bg="#5f6368", fg="white",
                             relief="flat", bd=0, padx=20, pady=8, width=12)
        clear_btn.grid(row=0, column=2)
        
        # Botón para limpiar sesión de WhatsApp
        session_btn = tk.Button(btn_frame, text="🗑️ Limpiar Sesión", command=self.limpiar_sesion_whatsapp,
                               font=("Segoe UI", 10, "bold"), bg="#ff6b35", fg="white",
                               relief="flat", bd=0, padx=20, pady=8, width=12)
        session_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Botón para borrar progreso
        progress_btn = tk.Button(btn_frame, text="📋 Borrar Progreso", command=self.borrar_progreso,
                                font=("Segoe UI", 10, "bold"), bg="#9c27b0", fg="white",
                                relief="flat", bd=0, padx=20, pady=8, width=12)
        progress_btn.grid(row=0, column=4, padx=(10, 0))
        
        # Botón para mostrar información del progreso
        info_btn = tk.Button(btn_frame, text="ℹ️ Info Progreso", command=self.mostrar_info_progreso,
                            font=("Segoe UI", 10, "bold"), bg="#2196f3", fg="white",
                            relief="flat", bd=0, padx=20, pady=8, width=12)
        info_btn.grid(row=0, column=5, padx=(10, 0))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(control_frame, mode='determinate', length=300)
        self.progress.grid(row=1, column=0, pady=(10, 15))
        
    def create_preview_section(self, parent):
        """Sección de vista previa"""
        preview_frame = ttk.LabelFrame(parent, text="📊 Vista Previa de Datos", style='Section.TLabelframe')
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 10))
        parent.grid_rowconfigure(0, weight=1)
        
        # Crear Treeview
        columns = ('Nombre', 'Teléfono', 'Matrícula', 'Hora', 'Tipo Plaza', 'Ocupantes')
        self.tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        # Configurar columnas
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        
        # Scrollbar para la tabla
        tree_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(15, 0), pady=15)
        tree_scroll.grid(row=0, column=1, sticky="ns", pady=15)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
    def create_log_section(self, parent):
        """Sección de log"""
        log_frame = ttk.LabelFrame(parent, text="📝 Log de Eventos", style='Section.TLabelframe')
        log_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        parent.grid_rowconfigure(1, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12,
                                                 font=("Consolas", 9),
                                                 bg="#1e1e1e", fg="#ffffff",
                                                 relief="flat", bd=0)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
    def create_stats_section(self, parent):
        """Sección de estadísticas"""
        stats_frame = ttk.LabelFrame(parent, text="📈 Estadísticas", style='Section.TLabelframe')
        stats_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        
        # Estadísticas en tiempo real
        stats_container = tk.Frame(stats_frame, bg="#ffffff")
        stats_container.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        stats_frame.grid_columnconfigure(0, weight=1)
        
        # Estadísticas simplificadas
        total_frame = tk.Frame(stats_container, bg="#ffffff")
        total_frame.grid(row=0, column=0, padx=(0, 20))
        
        total_label = tk.Label(total_frame, text="📊 Total de Contactos:", 
                              font=("Segoe UI", 10, "bold"),
                              bg="#ffffff", fg="#202124")
        total_label.grid(row=0, column=0, sticky="w")
        
        self.total_value_label = tk.Label(total_frame, text="0", 
                                         font=("Segoe UI", 12, "bold"),
                                         bg="#ffffff", fg="#1a73e8")
        self.total_value_label.grid(row=1, column=0, sticky="w")
        
        # Estadísticas de consolidación
        consolidacion_frame = tk.Frame(stats_container, bg="#ffffff")
        consolidacion_frame.grid(row=0, column=1, padx=(0, 20))
        
        consolidacion_label = tk.Label(consolidacion_frame, text="🔗 Consolidados:", 
                                      font=("Segoe UI", 10, "bold"),
                                      bg="#ffffff", fg="#202124")
        consolidacion_label.grid(row=0, column=0, sticky="w")
        
        self.consolidacion_value_label = tk.Label(consolidacion_frame, text="0", 
                                                 font=("Segoe UI", 12, "bold"),
                                                 bg="#ffffff", fg="#34a853")
        self.consolidacion_value_label.grid(row=1, column=0, sticky="w")
        
        # Estadísticas de reservas totales
        reservas_frame = tk.Frame(stats_container, bg="#ffffff")
        reservas_frame.grid(row=0, column=2)
        
        reservas_label = tk.Label(reservas_frame, text="📋 Total Reservas:", 
                                 font=("Segoe UI", 10, "bold"),
                                 bg="#ffffff", fg="#202124")
        reservas_label.grid(row=0, column=0, sticky="w")
        
        self.reservas_value_label = tk.Label(reservas_frame, text="0", 
                                            font=("Segoe UI", 12, "bold"),
                                            bg="#ffffff", fg="#ff6b35")
        self.reservas_value_label.grid(row=1, column=0, sticky="w")
    
    # Métodos de funcionalidad (simplificados para el ejemplo)
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.excel_path.set(filename)
            self.log_message(f"📁 Archivo seleccionado: {os.path.basename(filename)}")
    
    def analyze_data(self):
        if not self.excel_path.get():
            messagebox.showerror("Error", "Por favor selecciona un archivo Excel")
            return
        
        try:
            self.log_message("🔍 Analizando archivo Excel...")
            
            # Verificar si es una plantilla de recogida y mostrar información de columnas
            plantilla_actual = self.plantilla_actual.get()
            if plantilla_actual == "Recogidas":
                self._mostrar_info_columnas_vuelo()
            
            self.contactos = self.obtener_contactos_con_telefono()
            
            if len(self.contactos) == 0:
                messagebox.showwarning("Advertencia", "No se encontraron contactos con teléfono válido")
                return
            
            # Actualizar vista previa
            self.update_preview()
            
            # Actualizar estadísticas
            self.total_value_label.config(text=str(len(self.contactos)))
            
            # Calcular estadísticas de consolidación
            contactos_consolidados = sum(1 for c in self.contactos if c.get('consolidado', False))
            total_reservas = sum(c.get('reservas_count', 1) for c in self.contactos)
            
            self.consolidacion_value_label.config(text=str(contactos_consolidados))
            self.reservas_value_label.config(text=str(total_reservas))
            
            self.log_message(f"✅ Análisis completado: {len(self.contactos)} contactos válidos")
            if contactos_consolidados > 0:
                self.log_message(f"🔗 {contactos_consolidados} contactos consolidados de {total_reservas} reservas totales")
            messagebox.showinfo("Éxito", f"Se encontraron {len(self.contactos)} contactos válidos")
            
        except Exception as e:
            self.log_message(f"❌ Error analizando datos: {str(e)}")
            messagebox.showerror("Error", f"Error analizando datos: {str(e)}")
    
    def _mostrar_info_columnas_vuelo(self):
        """Mostrar información sobre las columnas de vuelo disponibles"""
        try:
            df = pd.read_excel(self.excel_path.get())
            
            # Buscar columnas que contengan "VUELTA" o "VUELO"
            columnas_vuelo = [col for col in df.columns if "VUELTA" in col.upper() or "VUELO" in col.upper()]
            
            if columnas_vuelo:
                self.log_message(f"📋 Columnas de vuelo encontradas: {', '.join(columnas_vuelo)}")
                
                # Mostrar algunos ejemplos de valores
                for columna in columnas_vuelo[:2]:  # Solo las primeras 2 columnas
                    valores_ejemplo = df[columna].dropna().head(3).tolist()
                    self.log_message(f"    📊 Ejemplos en '{columna}': {valores_ejemplo}")
            else:
                self.log_message("⚠️ No se encontraron columnas con 'VUELTA' o 'VUELO'")
                self.log_message("    🔄 Se usará la columna 'NIF' como respaldo")
                
        except Exception as e:
            self.log_message(f"⚠️ Error analizando columnas de vuelo: {str(e)}")
    
    def obtener_contactos_con_telefono(self):
        """
        Extrae solo los contactos que tienen teléfono válido del archivo Excel.
        
        Esta función procesa el archivo Excel y extrae los contactos que cumplen
        con los criterios de validación de teléfono. Soporta dos formatos:
        - Formato especial: Todas las columnas en una sola columna separada por tabs
        - Formato normal: Columnas separadas de Excel
        
        Si la consolidación de duplicados está habilitada, agrupa múltiples
        reservas del mismo cliente por día en un solo contacto consolidado.
        
        Returns:
            list: Lista de diccionarios con información de contactos válidos
                Cada contacto contiene: nombre, telefono, matricula, hora_entrada,
                tipo_plaza, ocupantes, fecha_entrada
                Si está consolidado: matriculas (lista), ocupantes_total, reservas_count
                
        Raises:
            FileProcessingError: Si hay error al procesar el archivo Excel
        """
        try:
            df = pd.read_excel(self.excel_path.get())
            contactos = []
            
            self.log_message(f"📊 Procesando {len(df)} filas...")
            self._log_configuracion_numeros()
            
            # Procesar según el formato del archivo
            if len(df.columns) == 1:
                self.log_message("📋 Detectado formato especial de archivo...")
                contactos = self._procesar_formato_especial(df)
            else:
                self.log_message("📋 Detectado formato normal de Excel...")
                contactos = self._procesar_formato_normal(df)
            
            # Aplicar consolidación de duplicados si está habilitada
            if self.consolidar_duplicados.get() and contactos:
                self.log_message("🔗 Aplicando consolidación de reservas duplicadas...")
                contactos_originales = len(contactos)
                contactos = self._consolidar_contactos_duplicados(contactos)
                contactos_consolidados = len(contactos)
                self.log_message(f"✅ Consolidación completada: {contactos_originales} → {contactos_consolidados} contactos")
            
            return contactos
            
        except FileNotFoundError:
            self.log_message(f"❌ No se encontró el archivo: {self.excel_path.get()}")
            raise FileProcessingError(f"Archivo no encontrado: {self.excel_path.get()}")
        except Exception as e:
            self.log_message(f"❌ Error leyendo Excel: {e}")
            raise FileProcessingError(f"Error procesando archivo Excel: {str(e)}")
    
    def _log_configuracion_numeros(self):
        """Registrar configuración de números en el log"""
        plantilla_actual = self.plantilla_actual.get()
        
        if self.numeros_extranjeros.get():
            self.log_message("🌍 Reconocimiento de números extranjeros: HABILITADO")
        else:
            self.log_message("🇪🇸 Solo números españoles: HABILITADO")
        
        # Informar sobre la columna de teléfono según la plantilla
        if plantilla_actual == "Recogidas":
            self.log_message("📞 Plantilla de recogida detectada: Buscando números en columna 'Nº Vuelo VUELTA'")
        else:
            self.log_message("📞 Plantilla normal: Buscando números en columna 'NIF'")
    
    def _procesar_formato_especial(self, df):
        """Procesar archivo con formato especial (todas las columnas en una sola)"""
        contactos = []
        
        for index in range(1, len(df)):  # Empezar desde 1 para saltar la fila de encabezados
            try:
                contacto = self._extraer_contacto_formato_especial(df, index)
                if contacto:
                    contactos.append(contacto)
            except Exception as e:
                continue  # Saltar filas con errores
        
        return contactos
    
    def _procesar_formato_normal(self, df):
        """Procesar archivo con formato normal de Excel"""
        contactos = []
        
        for index in range(len(df)):
            try:
                contacto = self._extraer_contacto_formato_normal(df, index)
                if contacto:
                    contactos.append(contacto)
            except Exception as e:
                continue  # Saltar filas con errores
        
        return contactos
    
    def _extraer_contacto_formato_especial(self, df, index):
        """Extraer contacto del formato especial"""
        # Obtener la fila completa
        fila_completa = str(df.iloc[index, 0])
        datos = fila_completa.split('\t')
        
        if len(datos) < MIN_COLUMNAS_FORMATO_ESPECIAL:  # Mínimo de columnas necesarias
            return None
        
        # Extraer datos según el orden: [Agencia, Cliente, NIF, Matricula, Vehiculo, Ocup., ...]
        nombre = datos[1].strip() if len(datos) > 1 else f"Cliente {index+1}"
        
        # Determinar de qué columna extraer el teléfono según la plantilla seleccionada
        plantilla_actual = self.plantilla_actual.get()
        if plantilla_actual == "Recogidas":
            # Para plantilla de recogidas, buscar en "Nº Vuelo VUELTA"
            # Asumiendo que está en una posición específica del formato especial
            # Buscar en todas las columnas que contengan "VUELTA" o números de vuelo
            nif_campo = ""
            for i, dato in enumerate(datos):
                dato_limpio = dato.strip().upper()
                if "VUELTA" in dato_limpio or "VUELO" in dato_limpio:
                    # Extraer número de teléfono del campo de vuelo
                    nif_campo = self._extraer_numero_telefono_vuelo(dato)
                    if nif_campo:
                        self.log_message(f"    📞 Número extraído de columna de vuelo: {nif_campo}")
                        break
            
            # Si no se encontró en campos de vuelo, usar el campo NIF como respaldo
            if not nif_campo:
                nif_campo = datos[2].strip() if len(datos) > 2 else ""
                self.log_message(f"    ⚠️ Usando campo NIF como respaldo: {nif_campo}")
        else:
            # Para otras plantillas, usar el campo NIF normal
            nif_campo = datos[2].strip() if len(datos) > 2 else ""
        
        matricula = datos[3].strip() if len(datos) > 3 else "Sin matrícula"
        ocupantes = datos[5].strip() if len(datos) > 5 else "Sin especificar"
        
        # Obtener hora de entrada
        hora_entrada = self._extraer_hora_entrada(datos)
        
        # Obtener fecha de entrada
        fecha_entrada = self._extraer_fecha_entrada(datos)
        
        # Obtener tipo de plaza
        tipo_plaza = datos[12].strip() if len(datos) > 12 else "Sin especificar"
        
        return self._validar_y_crear_contacto(nombre, nif_campo, matricula, hora_entrada, fecha_entrada, tipo_plaza, ocupantes)
    
    def _extraer_contacto_formato_normal(self, df, index):
        """Extraer contacto del formato normal de Excel"""
        # Obtener datos de las columnas correspondientes
        nombre = str(df.iloc[index]['Cliente']).strip() if 'Cliente' in df.columns else f"Cliente {index+1}"
        
        # Determinar de qué columna extraer el teléfono según la plantilla seleccionada
        plantilla_actual = self.plantilla_actual.get()
        if plantilla_actual == "Recogidas":
            # Para plantilla de recogidas, buscar en "Nº Vuelo VUELTA"
            nif_campo = ""
            
            # Buscar columnas que contengan "VUELTA" o "VUELO"
            columnas_vuelo = [col for col in df.columns if "VUELTA" in col.upper() or "VUELO" in col.upper()]
            
            if columnas_vuelo:
                # Usar la primera columna de vuelo encontrada
                columna_vuelo = columnas_vuelo[0]
                valor_vuelo = df.iloc[index][columna_vuelo]
                if pd.notna(valor_vuelo):
                    # Extraer números de teléfono del campo de vuelo
                    nif_campo = self._extraer_numero_telefono_vuelo(str(valor_vuelo))
                    if nif_campo:
                        self.log_message(f"    📞 Número extraído de '{columna_vuelo}': {nif_campo}")
                    else:
                        self.log_message(f"    ⚠️ No se pudo extraer número válido de '{columna_vuelo}': {valor_vuelo}")
            
            # Si no se encontró en campos de vuelo, usar el campo NIF como respaldo
            if not nif_campo:
                nif_campo = str(df.iloc[index]['NIF']).strip() if 'NIF' in df.columns else ""
                self.log_message(f"    ⚠️ Usando campo NIF como respaldo: {nif_campo}")
        else:
            # Para otras plantillas, usar el campo NIF normal
            nif_campo = str(df.iloc[index]['NIF']).strip() if 'NIF' in df.columns else ""
        
        matricula = str(df.iloc[index]['Matricula']).strip() if 'Matricula' in df.columns else "Sin matrícula"
        
        # Obtener hora de entrada
        hora_entrada = self._extraer_hora_entrada_excel(df, index)
        
        # Obtener fecha de entrada
        fecha_entrada = self._extraer_fecha_entrada_excel(df, index)
        
        # Obtener tipo de plaza
        tipo_plaza = str(df.iloc[index]['Tipo de Plaza']).strip() if 'Tipo de Plaza' in df.columns else "Sin especificar"
        
        # Obtener número de ocupantes
        ocupantes = self._extraer_ocupantes(df, index)
        
        return self._validar_y_crear_contacto(nombre, nif_campo, matricula, hora_entrada, fecha_entrada, tipo_plaza, ocupantes)
    
    def _extraer_hora_entrada(self, datos):
        """Extraer hora de entrada del formato especial"""
        hora_entrada = "00:00"
        if len(datos) > 10:
            hora_raw = datos[10].strip()
            if hora_raw and ':' in hora_raw:
                hora_entrada = hora_raw
        return hora_entrada
    
    def _extraer_hora_entrada_excel(self, df, index):
        """Extraer hora de entrada del formato Excel"""
        hora_entrada = "00:00"
        if 'Hora entrada' in df.columns:
            hora_raw = df.iloc[index]['Hora entrada']
            if pd.notna(hora_raw):
                hora_str = str(hora_raw)
                if ':' in hora_str:
                    hora_entrada = hora_str.split(':')[0] + ":" + hora_str.split(':')[1]
                else:
                    hora_entrada = hora_str[:2] + ":00"
        return hora_entrada
    
    def _extraer_ocupantes(self, df, index):
        """Extraer número de ocupantes del formato Excel"""
        ocupantes = "Sin especificar"
        if 'Ocup.' in df.columns:
            ocupantes_raw = df.iloc[index]['Ocup.']
            if pd.notna(ocupantes_raw):
                ocupantes = str(ocupantes_raw).strip()
        return ocupantes
    
    def _extraer_fecha_entrada(self, datos):
        """Extraer fecha de entrada del formato especial"""
        fecha_entrada = "Desconocida"
        if len(datos) > 10:
            fecha_raw = datos[10].strip()
            if fecha_raw and '-' in fecha_raw:
                fecha_entrada = fecha_raw
        return fecha_entrada
    
    def _extraer_fecha_entrada_excel(self, df, index):
        """Extraer fecha de entrada del formato Excel"""
        fecha_entrada = "Desconocida"
        if 'Fecha entrada' in df.columns:
            fecha_raw = df.iloc[index]['Fecha entrada']
            if pd.notna(fecha_raw):
                fecha_str = str(fecha_raw)
                if '-' in fecha_str:
                    fecha_entrada = fecha_str.split('-')[0] + "-" + fecha_str.split('-')[1] + "-" + fecha_str.split('-')[2]
                else:
                    fecha_entrada = fecha_str[:4] + "-" + fecha_str[4:6] + "-" + fecha_str[6:]
        return fecha_entrada
    
    def _validar_y_crear_contacto(self, nombre, nif_campo, matricula, hora_entrada, fecha_entrada, tipo_plaza, ocupantes):
        """Validar y crear contacto si cumple los criterios"""
        # Verificar si el NIF es realmente un teléfono (español o extranjero)
        if not self.es_telefono_valido(nif_campo):
            return None
        
        # FILTRO: No enviar si Tipo de Plaza está en la lista de excluidos
        if tipo_plaza.upper() in TIPOS_PLAZA_EXCLUIDOS:
            self.log_message(f"    ⏭️ Saltando {nombre} - Tipo de Plaza: {tipo_plaza}")
            return None
        
        # Determinar tipo de número
        tipo_numero = self.determinar_tipo_numero(nif_campo)
        self.log_message(f"    ✅ {nombre}: {nif_campo} ({tipo_numero})")
        
        return {
            'nombre': nombre,
            'telefono': nif_campo,
            'matricula': matricula,
            'hora_entrada': hora_entrada,
            'fecha_entrada': fecha_entrada,
            'tipo_plaza': tipo_plaza,
            'ocupantes': ocupantes
        }
    
    def es_telefono_valido(self, telefono):
        """Verificar si un campo es un número de teléfono válido (español o extranjero)"""
        if not telefono or telefono == 'nan':
            return False
        
        # Limpiar el número
        telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
        
        # Si ya empieza con +, es válido
        if str(telefono).startswith('+'):
            return len(telefono_limpio) >= 10 and len(telefono_limpio) <= 15
        
        # Si empieza con 00, es válido (formato internacional)
        if telefono_limpio.startswith('00'):
            return len(telefono_limpio) >= 12 and len(telefono_limpio) <= 17
        
        # Números españoles: 9 dígitos que empiecen con 6 o 7
        if len(telefono_limpio) == 9 and telefono_limpio[0] in ['6', '7']:
            return True
        
        # Números españoles con código de país: 11 dígitos que empiecen con 34
        if len(telefono_limpio) == 11 and telefono_limpio.startswith('34'):
            return True
        
        # Números extranjeros: solo si está habilitado en la configuración
        if self.numeros_extranjeros.get():
            # Números extranjeros: 10-15 dígitos que no empiecen con 34
            if len(telefono_limpio) >= 10 and len(telefono_limpio) <= 15 and not telefono_limpio.startswith('34'):
                return True
            
            # Números con formato especial (con espacios, guiones, etc.)
            if len(telefono_limpio) >= 9 and len(telefono_limpio) <= 15:
                return True
        
        return False
    
    def determinar_tipo_numero(self, telefono):
        """Determinar el tipo de número de teléfono"""
        if not telefono or telefono == 'nan':
            return "Inválido"
        
        # Limpiar el número
        telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
        
        # Si ya empieza con +, es internacional
        if str(telefono).startswith('+'):
            if telefono_limpio.startswith('34'):
                return "Español Internacional"
            else:
                return "Extranjero Internacional"
        
        # Si empieza con 00, es internacional
        if telefono_limpio.startswith('00'):
            if telefono_limpio.startswith('0034'):
                return "Español Internacional (00)"
            else:
                return "Extranjero Internacional (00)"
        
        # Números españoles: 9 dígitos que empiecen con 6 o 7
        if len(telefono_limpio) == 9 and telefono_limpio[0] in ['6', '7']:
            return "Español Nacional"
        
        # Números españoles con código de país: 11 dígitos que empiecen con 34
        if len(telefono_limpio) == 11 and telefono_limpio.startswith('34'):
            return "Español con Código"
        
        # Números extranjeros: 10-15 dígitos que no empiecen con 34
        if len(telefono_limpio) >= 10 and len(telefono_limpio) <= 15 and not telefono_limpio.startswith('34'):
            return "Extranjero"
        
        # Números con formato especial
        if len(telefono_limpio) >= 9 and len(telefono_limpio) <= 15:
            return "Formato Especial"
        
        return "Desconocido"
    
    def update_preview(self):
        """Actualizar vista previa de datos"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar datos
        for contacto in self.contactos[:20]:  # Mostrar solo los primeros 20
            # Preparar información de matrículas para mostrar
            if contacto.get('consolidado', False) and 'matriculas' in contacto:
                matriculas_mostrar = ', '.join(contacto['matriculas'][:3])  # Mostrar solo las primeras 3
                if len(contacto['matriculas']) > 3:
                    matriculas_mostrar += f" (+{len(contacto['matriculas']) - 3} más)"
            else:
                matriculas_mostrar = contacto['matricula']
            
            # Preparar información de ocupantes
            if contacto.get('consolidado', False) and 'ocupantes_total' in contacto:
                ocupantes_mostrar = f"{contacto['ocupantes_total']} total"
            else:
                ocupantes_mostrar = contacto.get('ocupantes', 'Sin especificar')
            
            # Agregar indicador de consolidación al nombre
            nombre_mostrar = contacto['nombre']
            if contacto.get('consolidado', False):
                nombre_mostrar += f" (🔗 {contacto['reservas_count']} reservas)"
            
            self.tree.insert('', tk.END, values=(
                nombre_mostrar,
                contacto['telefono'],
                matriculas_mostrar,
                contacto['hora_entrada'],
                contacto.get('tipo_plaza', 'Sin especificar'),
                ocupantes_mostrar
            ))
    
    def load_template(self, event=None):
        """Cargar plantilla seleccionada"""
        plantilla = obtener_plantilla(self.plantilla_actual.get())
        self.template_text.delete(1.0, tk.END)
        self.template_text.insert(1.0, plantilla)
        
        # Mostrar información sobre la columna de teléfono según la plantilla
        plantilla_actual = self.plantilla_actual.get()
        if plantilla_actual == "Recogidas":
            self.log_message(f"📝 Plantilla cargada: {self.plantilla_actual.get()} (Recogida)")
            self.log_message("📞 Configuración: Buscando números en columna 'Nº Vuelo VUELTA'")
        else:
            self.log_message(f"📝 Plantilla cargada: {self.plantilla_actual.get()}")
            self.log_message("📞 Configuración: Buscando números en columna 'NIF'")
    
    def restore_template(self):
        """Restaurar plantilla original"""
        self.load_template()
        self.log_message("🔄 Plantilla restaurada")
    
    def preview_message(self):
        """Vista previa del mensaje"""
        if not self.contactos:
            messagebox.showwarning("Advertencia", "No hay contactos para mostrar vista previa")
            return
        
        # Crear ventana de vista previa
        preview_window = tk.Toplevel(self.root)
        preview_window.title("👁️ Vista Previa del Mensaje")
        preview_window.geometry("600x400")
        preview_window.configure(bg="#ffffff")
        
        # Obtener primer contacto para ejemplo
        contacto = self.contactos[0]
        
        # Verificar si es un contacto consolidado
        if contacto.get('consolidado', False):
            mensaje = self.crear_mensaje_consolidado(contacto)
            titulo_extra = f" (Consolidado: {contacto['reservas_count']} reservas)"
        else:
            mensaje = self.crear_mensaje_personalizado(
                contacto['nombre'], 
                contacto['matricula'], 
                contacto['hora_entrada']
            )
            titulo_extra = ""
        
        # Mostrar mensaje con formato preservado
        text_widget = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD,
                                               font=("Segoe UI", 11),
                                               bg="#ffffff", fg="#202124",
                                               relief="flat", bd=0)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert(1.0, mensaje)
        text_widget.config(state=tk.DISABLED)
        
        # Agregar información sobre el formato y consolidación
        info_text = "✅ Formato preservado - Saltos de línea y espacios mantenidos"
        if contacto.get('consolidado', False):
            info_text += f"\n🔗 Contacto consolidado: {contacto['reservas_count']} reservas agrupadas"
            info_text += f"\n📋 Matrículas: {', '.join(contacto['matriculas'])}"
            info_text += f"\n👥 Total ocupantes: {contacto['ocupantes_total']}"
        
        info_label = tk.Label(preview_window, 
                             text=info_text,
                             font=("Segoe UI", 9), bg="#ffffff", fg="#34a853",
                             justify=tk.LEFT)
        info_label.pack(pady=(0, 10))
    
    def show_templates(self):
        """Mostrar todas las plantillas disponibles"""
        templates_window = tk.Toplevel(self.root)
        templates_window.title("📋 Todas las Plantillas")
        templates_window.geometry("800x600")
        templates_window.configure(bg="#ffffff")
        
        # Notebook para pestañas
        notebook = ttk.Notebook(templates_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for nombre, plantilla in PLANTILLAS_DISPONIBLES.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=nombre)
            
            text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD,
                                                   font=("Segoe UI", 10),
                                                   bg="#ffffff", fg="#202124")
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(1.0, plantilla)
            text_widget.config(state=tk.DISABLED)
    
    def crear_mensaje_personalizado(self, nombre, matricula, hora, ocupantes="Sin especificar"):
        """Crea el mensaje usando la plantilla actual y limpia caracteres problemáticos"""
        try:
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%d-%m-%Y")
            
            # Obtener plantilla preservando saltos de línea
            plantilla = self.template_text.get(1.0, tk.END)
            
            # Reemplazar variables en la plantilla
            mensaje = plantilla.format(
                nombre=nombre,
                matricula=matricula,
                hora=hora,
                fecha_actual=fecha_actual,
                ocupantes=ocupantes
            )
            
            # Limpiar caracteres Unicode problemáticos preservando formato y emojis
            mensaje_limpio = self.limpiar_caracteres_unicode(mensaje)
            
            # Verificar si se preservaron los emojis
            emojis_originales = [char for char in mensaje if ord(char) > 0xFFFF]
            emojis_preservados = [char for char in mensaje_limpio if ord(char) > 0xFFFF]
            
            if emojis_originales and len(emojis_preservados) == len(emojis_originales):
                self.log_message(f"    ✅ Emojis preservados correctamente: {len(emojis_preservados)} emojis")
            elif emojis_originales and len(emojis_preservados) < len(emojis_originales):
                self.log_message(f"    ⚠️ Algunos emojis se perdieron: {len(emojis_preservados)}/{len(emojis_originales)} preservados")
            
            return mensaje_limpio
        except Exception as e:
            return f"Error en la plantilla: {str(e)}"
    
    def crear_mensaje_consolidado(self, contacto):
        """
        Crear mensaje personalizado para contactos consolidados.
        
        Args:
            contacto (dict): Contacto consolidado con múltiples matrículas
            
        Returns:
            str: Mensaje formateado para contacto consolidado
        """
        try:
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%d-%m-%Y")
            
            # Obtener plantilla preservando saltos de línea
            plantilla = self.template_text.get(1.0, tk.END)
            
            # Preparar información de matrículas
            if contacto.get('consolidado', False) and 'matriculas' in contacto:
                matriculas = contacto['matriculas']
                if len(matriculas) == 1:
                    matricula_texto = matriculas[0]
                elif len(matriculas) == 2:
                    matricula_texto = f"{matriculas[0]} y {matriculas[1]}"
                else:
                    matricula_texto = f"{', '.join(matriculas[:-1])} y {matriculas[-1]}"
                
                # Agregar información de consolidación
                if len(matriculas) > 1:
                    matricula_texto += f" ({len(matriculas)} vehículos)"
            else:
                matricula_texto = contacto['matricula']
            
            # Preparar información de ocupantes
            ocupantes_texto = contacto.get('ocupantes', 'Sin especificar')
            if contacto.get('consolidado', False) and 'ocupantes_total' in contacto:
                ocupantes_texto = f"{contacto['ocupantes_total']} personas total"
            
            # Reemplazar variables en la plantilla
            mensaje = plantilla.format(
                nombre=contacto['nombre'],
                matricula=matricula_texto,
                hora=contacto['hora_entrada'],
                fecha_actual=fecha_actual,
                ocupantes=ocupantes_texto
            )
            
            # Limpiar caracteres Unicode problemáticos preservando formato y emojis
            mensaje_limpio = self.limpiar_caracteres_unicode(mensaje)
            
            return mensaje_limpio
        except Exception as e:
            return f"Error en la plantilla consolidada: {str(e)}"
    
    def start_sending(self):
        """Iniciar el proceso de envío"""
        if not self.contactos:
            messagebox.showerror("Error", "No hay contactos para enviar. Analiza los datos primero.")
            return
        
        # Verificar progreso guardado
        progreso_prev = self.cargar_progreso()
        if progreso_prev > 0 and progreso_prev < len(self.contactos):
            if self.mostrar_dialogo_progreso(progreso_prev, len(self.contactos)):
                self.log_message(f"🔄 Reanudando envío desde contacto {progreso_prev + 1}")
                self.indice_inicio = progreso_prev
            else:
                self.borrar_progreso()
                self.indice_inicio = 0
                self.log_message("🔄 Iniciando envío desde el principio")
        else:
            self.indice_inicio = 0
            self.log_message("🚀 Iniciando nuevo envío")
        
        # Confirmar envío automático
        contactos_restantes = len(self.contactos) - self.indice_inicio
        respuesta = messagebox.askyesno("Confirmar Envío Automático", 
            f"¿Enviar {contactos_restantes} mensajes automáticamente?\n\n"
            "El programa abrirá cada chat y enviará el mensaje automáticamente\n"
            "usando send_keys() y Keys.ENTER (método natural de Selenium).")
        if not respuesta:
            return
        
        # Iniciar hilo de envío
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.sending_thread)
        thread.daemon = True
        thread.start()
    
    def stop_sending(self):
        """Detener el proceso de envío"""
        self.is_running = False
        self.log_message("⏹️ Deteniendo envío...")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def sending_thread(self):
        """
        Hilo principal de envío con Selenium.
        
        Esta función ejecuta el proceso completo de envío de mensajes:
        1. Inicializa Chrome con configuración robusta
        2. Conecta a WhatsApp Web
        3. Procesa todos los contactos y envía mensajes
        4. Maneja errores y actualiza progreso
        
        El proceso se ejecuta en un hilo separado para mantener
        la interfaz de usuario responsiva.
        
        Raises:
            ChromeInitializationError: Si no se puede inicializar Chrome
            WhatsAppConnectionError: Si no se puede conectar a WhatsApp Web
            MessageSendError: Si hay errores al enviar mensajes
        """
        driver = None
        try:
            self._log_inicio_envio()
            driver = self._inicializar_chrome()
            self._conectar_whatsapp(driver)
            self._procesar_contactos(driver)
            
        except TimeoutException:
            self.log_message("⏰ Tiempo de espera agotado. No se pudo conectar a WhatsApp Web")
        except Exception as e:
            self.log_message(f"❌ Error en el envío: {str(e)}")
        finally:
            if driver:
                driver.quit()
            self.cleanup()
    
    def _log_inicio_envio(self):
        """Registrar mensajes de inicio del envío"""
        self.log_message("🚀 Iniciando envío automático con send_keys() y Keys.ENTER...")
        self.log_message("ℹ️ Usando método natural de Selenium: send_keys() para escribir y Keys.ENTER para enviar")
        self.log_message("ℹ️ Soporte completo para Unicode, emojis y caracteres especiales")
        self.log_message("ℹ️ Emojis preservados automáticamente en todas las plantillas")
        self.log_message("ℹ️ Detectando envío automático de WhatsApp Web para evitar escritura duplicada")
        self.log_message("📱 Configurando Chrome...")
    
    def _inicializar_chrome(self):
        """Inicializar Chrome con configuración robusta"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import os
        
        # Configurar opciones de Chrome
        chrome_options = self._configurar_opciones_chrome()
        
        # Inicializar driver con configuración robusta
        driver = None
        try:
            self.log_message("🔧 Configurando Chrome...")
            
            # Método 1: Usar webdriver-manager con configuración específica
            try:
                service = Service(ChromeDriverManager(version="latest").install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                self.log_message("✅ Chrome iniciado con webdriver-manager")
            except Exception as e1:
                self.log_message(f"⚠️ webdriver-manager falló: {str(e1)}")
                
                # Método 2: Usar ChromeDriver directo
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                    self.log_message("✅ Chrome iniciado directamente")
                except Exception as e2:
                    self.log_message(f"⚠️ Chrome directo falló: {str(e2)}")
                    
                    # Método 3: Usar configuración mínima
                    try:
                        chrome_options_minimal = Options()
                        chrome_options_minimal.add_argument("--no-sandbox")
                        chrome_options_minimal.add_argument("--disable-dev-shm-usage")
                        driver = webdriver.Chrome(options=chrome_options_minimal)
                        self.log_message("✅ Chrome iniciado con configuración mínima")
                    except Exception as e3:
                        self.log_message(f"⚠️ Configuración mínima falló: {str(e3)}")
                        raise ChromeInitializationError("No se pudo inicializar Chrome. Verifica la instalación.")
            
            if driver:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
        except Exception as e:
            self.log_message(f"❌ Error crítico inicializando Chrome: {str(e)}")
            raise ChromeInitializationError(f"Error inicializando Chrome: {str(e)}")
        
        return driver
    
    def _configurar_opciones_chrome(self):
        """Configurar opciones de Chrome con persistencia de sesión"""
        from selenium.webdriver.chrome.options import Options
        import os
        
        chrome_options = Options()
        
        # Directorio para persistir la sesión de WhatsApp Web
        user_data_dir = os.path.join(os.getcwd(), "whatsapp_session")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        })
        
        return chrome_options
    
    def _conectar_whatsapp(self, driver):
        """Conectar a WhatsApp Web"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        self.log_message("🌐 Abriendo WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Esperar a que se cargue WhatsApp Web y detectar si ya está conectado
        self.log_message("🔍 Verificando estado de conexión...")
        
        # Esperar a que aparezca el chat list o el código QR
        wait = WebDriverWait(driver, TIMEOUT_WHATSAPP_CONNECTION)  # 30 segundos para verificar conexión
        
        try:
            # Intentar detectar si ya está conectado (chat list visible)
            chat_list = wait.until(EC.presence_of_element_located((By.ID, "pane-side")))
            self.log_message("✅ WhatsApp Web ya está conectado! (sesión persistente)")
            self.log_message("📱 No es necesario escanear el código QR")
        except:
            # Si no está conectado, mostrar código QR
            self.log_message("📱 Código QR detectado - Escanea con tu teléfono")
            self.log_message("⏳ Esperando escaneo del código QR...")
            
            # Esperar hasta 2 minutos para escanear QR
            wait_qr = WebDriverWait(driver, TIMEOUT_QR_SCAN)
            try:
                chat_list = wait_qr.until(EC.presence_of_element_located((By.ID, "pane-side")))
                self.log_message("✅ WhatsApp Web conectado exitosamente!")
                self.log_message("💾 Sesión guardada para futuros usos")
            except:
                self.log_message("❌ Tiempo agotado para escanear código QR")
                raise WhatsAppConnectionError("No se pudo conectar a WhatsApp Web - Tiempo agotado para escanear QR")
        
        # Pausa inicial para asegurar que WhatsApp Web esté completamente cargado
        self.log_message("⏳ Esperando a que WhatsApp Web esté completamente listo...")
        time.sleep(10)
        self.log_message("📤 Iniciando envío automático de mensajes...")
    
    def _procesar_contactos(self, driver):
        """Procesar todos los contactos para envío"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from urllib.parse import quote
        import time
        import random
        
        # Contador de mensajes enviados
        enviados = 0
        errores = 0
        
        for i, contacto in enumerate(self.contactos[self.indice_inicio:], start=self.indice_inicio):
            if not self.is_running:
                break
            
            try:
                resultado = self._enviar_mensaje_contacto(driver, contacto, i)
                if resultado:
                    enviados += 1
                else:
                    errores += 1
                
                # Log de progreso
                self.log_message(f"    📊 Progreso: {enviados} enviados, {errores} errores")
                
                # Guardar progreso
                self.guardar_progreso(i)
                
                # Actualizar progreso
                progress = ((i + 1) / len(self.contactos)) * 100
                self.progress['value'] = progress
                self.root.update_idletasks()
                
                # Pausa entre mensajes
                delay = random.randint(self.delay_min.get(), self.delay_max.get())
                self.log_message(f"    ⏳ Pausa de {delay}s...")
                time.sleep(delay)
                
            except Exception as e:
                errores += 1
                self.log_message(f"❌ Error con {contacto['nombre']}: {str(e)}")
                
                # Si hay un error crítico, preguntar si continuar
                if "chrome not reachable" in str(e).lower() or "session deleted" in str(e).lower():
                    respuesta = messagebox.askyesno("Error Crítico", 
                        f"Error crítico detectado: {str(e)}\n¿Deseas continuar con el siguiente contacto?")
                    if not respuesta:
                        break
                continue
        
        self.log_message(f"✅ Envío completado: {enviados} mensajes enviados, {errores} errores")
        
        # Borrar progreso al completar
        self.borrar_progreso()
    
    def _enviar_mensaje_contacto(self, driver, contacto, indice):
        """Enviar mensaje a un contacto específico"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from urllib.parse import quote
        import time
        import random
        
        self.log_message(f"📤 [{indice+1}/{len(self.contactos)}] Enviando mensaje a {contacto['nombre']}")
        
        # Verificar si es un contacto consolidado
        if contacto.get('consolidado', False):
            self.log_message(f"    🔗 Enviando mensaje consolidado ({contacto['reservas_count']} reservas)")
            mensaje = self.crear_mensaje_consolidado(contacto)
        else:
            # Crear mensaje personalizado normal
            mensaje = self.crear_mensaje_personalizado(
                contacto['nombre'], 
                contacto['matricula'], 
                contacto['hora_entrada'],
                contacto.get('ocupantes', 'Sin especificar')
            )
        
        # Verificar si el mensaje contiene emojis
        emojis_en_mensaje = [char for char in mensaje if ord(char) > 0xFFFF]
        if emojis_en_mensaje:
            self.log_message(f"    😊 Mensaje contiene {len(emojis_en_mensaje)} emojis")
        
        # Método mejorado: Usar URL directa de WhatsApp y envío automático
        telefono_formateado = self.formatear_telefono_whatsapp(contacto['telefono'])
        numero_limpio = telefono_formateado.replace('+', '').replace(' ', '')
        url_whatsapp = f"https://web.whatsapp.com/send?phone={numero_limpio}&text={quote(mensaje)}"

        self.log_message(f"    🌐 Abriendo chat directo para {contacto['nombre']}")
        driver.get(url_whatsapp)

        # Tiempo de espera especial para el primer contacto
        if indice == 0:
            self.log_message(f"    ⏳ Esperando más tiempo para el primer contacto...")
            time.sleep(TIMEOUT_FIRST_CONTACT)  # Más tiempo para el primer contacto
        else:
            time.sleep(random.randint(TIMEOUT_BETWEEN_MESSAGES_MIN, TIMEOUT_BETWEEN_MESSAGES_MAX))  # Más tiempo para procesar

        # Esperar que aparezca el cuadro de texto y enviar automáticamente
        try:
            input_box = WebDriverWait(driver, TIMEOUT_FIELD_SEARCH).until(
                EC.presence_of_element_located((
                    By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'
                ))
            )
            input_box.send_keys(Keys.ENTER)
            self.log_message(f"    ✅ Mensaje enviado automáticamente a {contacto['nombre']}")
            return True
        except Exception as e:
            self.log_message(f"    ❌ No se pudo enviar el mensaje a {contacto['nombre']}: {e}")
            return False
    

    def formatear_telefono_whatsapp(self, telefono):
        """Formatear número de teléfono para WhatsApp - Mejorado para números extranjeros"""
        # Si ya empieza con +, devolverlo tal como está
        if str(telefono).startswith('+'):
            return str(telefono)
        
        # Limpiar el número
        telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
        
        # Si empieza con 00, convertir a +
        if telefono_limpio.startswith('00'):
            return f"+{telefono_limpio[2:]}"
        
        # Si empieza con 34 (España), mantenerlo
        if telefono_limpio.startswith('34'):
            return f"+{telefono_limpio}"
        
        # Si empieza con 6 o 7 (móvil español), agregar 34
        if telefono_limpio.startswith(('6', '7')) and len(telefono_limpio) == 9:
            return f"+34{telefono_limpio}"
        
        # Si ya tiene 9 dígitos y empieza con 6 o 7, agregar 34
        if len(telefono_limpio) == 9 and telefono_limpio[0] in ['6', '7']:
            return f"+34{telefono_limpio}"
        
        # Si ya tiene el formato correcto con 34, devolverlo
        if telefono_limpio.startswith('34') and len(telefono_limpio) >= 11:
            return f"+{telefono_limpio}"
        
        # Para números extranjeros, verificar si ya tienen código de país
        # Si tiene 10-15 dígitos y no empieza con 34, asumir que ya tiene código de país
        if len(telefono_limpio) >= 10 and len(telefono_limpio) <= 15 and not telefono_limpio.startswith('34'):
            return f"+{telefono_limpio}"
        
        # Si tiene menos de 9 dígitos, probablemente es un número español sin código
        if len(telefono_limpio) < 9:
            return f"+34{telefono_limpio}"
        
        # Por defecto, agregar 34 (España)
        return f"+34{telefono_limpio}"
    
    def limpiar_caracteres_unicode(self, texto):
        """Limpiar caracteres Unicode problemáticos para ChromeDriver preservando formato y emojis"""
        try:
            # Convertir a string si no lo es
            if not isinstance(texto, str):
                texto = str(texto)
            
            # Preservar emojis y caracteres Unicode válidos
            # Los emojis están en rangos específicos de Unicode
            texto_limpio = ""
            for char in texto:
                # Preservar emojis (rangos Unicode de emojis)
                # Emojis básicos: U+1F600-U+1F64F (Emoticons)
                # Emojis varios: U+1F300-U+1F5FF (Miscellaneous Symbols and Pictographs)
                # Emojis transporte: U+1F680-U+1F6FF (Transport and Map Symbols)
                # Emojis varios suplementarios: U+1F900-U+1F9FF (Supplemental Symbols and Pictographs)
                # Emojis símbolos: U+2600-U+26FF (Miscellaneous Symbols)
                # Emojis dingbats: U+2700-U+27BF (Dingbats)
                
                char_code = ord(char)
                
                # Verificar si es un emoji válido usando constantes
                es_emoji = any(start <= char_code <= end for start, end in EMOJI_RANGES)
                
                # Preservar caracteres BMP normales y emojis
                if char_code <= 0xFFFF or es_emoji:
                    texto_limpio += char
                else:
                    # Solo reemplazar caracteres problemáticos muy específicos
                    # pero preservar saltos de línea
                    if char == '\n':
                        texto_limpio += '\n'
                    elif char == '\t':
                        texto_limpio += ' '  # Reemplazar tabs con espacios
                    elif char_code > 0x10FFFF:  # Solo caracteres fuera del rango Unicode válido
                        texto_limpio += " "
                    else:
                        # Preservar otros caracteres Unicode válidos
                        texto_limpio += char
            
            # NO limpiar espacios múltiples para preservar formato
            # Solo eliminar espacios al inicio y final
            texto_limpio = texto_limpio.strip()
            
            return texto_limpio
        except Exception as e:
            self.log_message(f"    ⚠️ Error limpiando caracteres Unicode: {str(e)}")
            # Si falla, devolver texto original sin caracteres problemáticos
            return "".join(char for char in texto if ord(char) <= 0x10FFFF)

    def enviar_mensaje_automatico(self, driver, mensaje):
        """Enviar mensaje usando send_keys() con Keys.ENTER"""
        try:
            self.log_message("    🔍 Preparando y enviando mensaje...")
            
            # Limpiar caracteres Unicode problemáticos preservando emojis
            mensaje_limpio = self.limpiar_caracteres_unicode(mensaje)
            if mensaje_limpio != mensaje:
                self.log_message("    🔧 Mensaje limpiado de caracteres Unicode problemáticos (emojis preservados)")
            
            # Esperar a que la página cargue completamente
            time.sleep(10)
            
            # Buscar el campo de texto
            text_box = self.buscar_campo_texto(driver)
            if not text_box:
                return False
            
            # Verificar si el mensaje ya se envió automáticamente (URL directa)
            if self.verificar_mensaje_enviado_automatico(driver):
                self.log_message("    ✅ Mensaje enviado automáticamente por WhatsApp Web")
                return True
            # Verificar si el mensaje ya está presente en el campo (URL directa)
            elif self.verificar_mensaje_ya_presente(driver, mensaje_limpio):
                self.log_message("    ✅ Mensaje ya está en el campo de texto (URL directa)")
                # Enviar el mensaje que ya está en el campo
                self.log_message("    🚀 Enviando mensaje existente con Keys.ENTER...")
                return self.enviar_con_enter(driver, text_box)
            else:
                # Escribir el mensaje usando send_keys()
                self.log_message("    📝 Escribiendo mensaje con send_keys()...")
                self.escribir_mensaje_con_send_keys(driver, text_box, mensaje_limpio)
                
                # Enviar el mensaje con Keys.ENTER
                self.log_message("    🚀 Enviando mensaje con Keys.ENTER...")
                return self.enviar_con_enter(driver, text_box)
            
        except Exception as e:
            raise Exception(f"Error enviando mensaje: {str(e)}")
    

    
    def buscar_campo_texto(self, driver):
        """Buscar el campo de texto de WhatsApp Web con caché"""
        try:
            # Verificar caché primero
            if 'campo_texto' in self._element_cache:
                try:
                    elemento = self._element_cache['campo_texto']
                    # Verificar que el elemento aún es válido
                    elemento.is_displayed()
                    self.log_message(f"    ✅ Campo de texto encontrado en caché")
                    return elemento
                except:
                    # Elemento ya no es válido, limpiar caché
                    del self._element_cache['campo_texto']
            
            # Buscar elemento si no está en caché
            selectores_texto = [
                '//div[@contenteditable="true"][@data-tab="6"]',
                '//div[@contenteditable="true"][@data-tab="10"]',
                '//div[@contenteditable="true"][@role="textbox"]',
                '//div[@contenteditable="true"]',
                '//div[@data-testid="conversation-compose-box-input"]',
                '//div[@title="Escribe un mensaje"]',
                '//div[@contenteditable="true"][@data-tab="1"]'
            ]
            
            for i, selector in enumerate(selectores_texto):
                try:
                    text_box = WebDriverWait(driver, TIMEOUT_FIELD_SEARCH).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    # Guardar en caché
                    self._element_cache['campo_texto'] = text_box
                    self.log_message(f"    ✅ Campo de texto encontrado con selector {i+1} (guardado en caché)")
                    return text_box
                except Exception as e:
                    self.log_message(f"    ⚠️ Selector {i+1} falló: {str(e)}")
                    continue
            
            raise Exception("No se pudo encontrar el campo de texto")
            
        except Exception as e:
            self.log_message(f"    ❌ Error buscando campo de texto: {str(e)}")
            return None
    
    def limpiar_cache_elementos(self):
        """Limpiar caché de elementos cuando sea necesario"""
        self._element_cache.clear()
        self.log_message("    🧹 Caché de elementos limpiado")
    
    def verificar_mensaje_ya_presente(self, driver, mensaje_limpio):
        """Verificar si el mensaje ya está presente en el campo de texto"""
        try:
            # Primero verificar si ya hay mensajes recientes en el chat
            if self.hay_mensajes_recientes_en_chat(driver):
                self.log_message("    ⚠️ Detectados mensajes recientes en el chat - posible envío previo")
                return True
            
            text_box = self.buscar_campo_texto(driver)
            if not text_box:
                return False
            
            texto_actual = text_box.get_attribute('innerHTML') or text_box.text or text_box.get_attribute('textContent') or ""
            
            # Comparar de manera más flexible
            mensaje_para_comparar = mensaje_limpio.strip()
            texto_para_comparar = texto_actual.strip()
            
            # Verificar si el mensaje ya está presente (al menos 80% del contenido)
            if self.mensaje_ya_presente(texto_para_comparar, mensaje_para_comparar):
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error verificando mensaje presente: {str(e)}")
            return False
    
    def hay_mensajes_recientes_en_chat(self, driver):
        """Verificar si hay mensajes recientes en el chat que indiquen envío previo"""
        try:
            # Verificar con JavaScript si hay mensajes recientes
            hay_mensajes = driver.execute_script("""
                // Buscar mensajes enviados recientemente
                const mensajesEnviados = document.querySelectorAll('div[data-testid="msg-meta"].message-out');
                if (mensajesEnviados.length > 0) {
                    return true;
                }
                
                // Buscar cualquier mensaje reciente
                const mensajesRecientes = document.querySelectorAll('div[data-testid="msg-meta"]');
                if (mensajesRecientes.length > 0) {
                    // Verificar que el último mensaje tenga contenido sustancial
                    const ultimoMensaje = mensajesRecientes[mensajesRecientes.length - 1];
                    const contenido = ultimoMensaje.textContent || '';
                    if (contenido.length > 30) { // Mensaje con contenido mínimo
                        return true;
                    }
                }
                
                return false;
            """)
            return hay_mensajes
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error verificando mensajes recientes: {str(e)}")
            return False
    
    def escribir_mensaje_con_send_keys(self, driver, text_box, mensaje_limpio):
        """Escribir mensaje usando send_keys()"""
        try:
            # Limpiar el campo de texto de manera segura
            try:
                text_box.clear()
                time.sleep(2)
            except Exception as e:
                self.log_message(f"    ⚠️ Error limpiando campo: {str(e)}")
                # Intentar con JavaScript
                try:
                    driver.execute_script("arguments[0].innerHTML = '';", text_box)
                    time.sleep(2)
                except:
                    pass
            
            # Hacer clic en el campo para enfocarlo
            text_box.click()
            time.sleep(1)
            
            # Escribir el mensaje usando send_keys() (método natural)
            self.log_message(f"    📝 Escribiendo mensaje con send_keys()...")
            text_box.send_keys(mensaje_limpio)
            
            # Esperar a que se complete la escritura
            time.sleep(3)
            
            self.log_message(f"    ✅ Mensaje escrito correctamente con send_keys()")
            
        except Exception as e:
            self.log_message(f"    ❌ Error escribiendo mensaje: {str(e)}")
            raise Exception(f"Error escribiendo mensaje: {str(e)}")
    
    def enviar_con_enter(self, driver, text_box):
        """Enviar mensaje usando Keys.ENTER"""
        try:
            # Asegurar que el campo esté enfocado
            text_box.click()
            time.sleep(1)
            
            # Enviar con Keys.ENTER
            self.log_message(f"    🚀 Enviando con Keys.ENTER...")
            text_box.send_keys(Keys.ENTER)
            
            # Esperar a que se procese el envío
            time.sleep(5)
            
            # Verificar que se envió correctamente
            if self.verificar_mensaje_enviado(driver):
                self.log_message(f"    ✅ Mensaje enviado exitosamente con Keys.ENTER")
                return True
            else:
                self.log_message(f"    ⚠️ Mensaje no confirmado, intentando método alternativo...")
                return self.enviar_con_enter_alternativo(driver, text_box)
                
        except Exception as e:
            self.log_message(f"    ❌ Error enviando con Keys.ENTER: {str(e)}")
            return self.enviar_con_enter_alternativo(driver, text_box)
    
    def enviar_con_enter_alternativo(self, driver, text_box):
        """Método alternativo para enviar con Enter usando ActionChains"""
        try:
            self.log_message(f"    🔄 Intentando método alternativo con ActionChains...")
            
            # Usar ActionChains para mayor confiabilidad
            actions = ActionChains(driver)
            actions.move_to_element(text_box).click().send_keys(Keys.ENTER).perform()
            
            # Esperar a que se procese el envío
            time.sleep(5)
            
            # Verificar que se envió correctamente
            if self.verificar_mensaje_enviado(driver):
                self.log_message(f"    ✅ Mensaje enviado exitosamente con ActionChains")
                return True
            else:
                self.log_message(f"    ❌ No se pudo confirmar el envío")
                return False
                
        except Exception as e:
            self.log_message(f"    ❌ Error con método alternativo: {str(e)}")
            return False
    

    def mensaje_ya_presente(self, texto_campo, mensaje_esperado):
        """Verificar si el mensaje ya está presente en el campo de texto"""
        try:
            # Si el campo está vacío, no está presente
            if not texto_campo or not texto_campo.strip():
                return False
            
            # Si el mensaje esperado está vacío, no está presente
            if not mensaje_esperado or not mensaje_esperado.strip():
                return False
            
            # Normalizar ambos textos para comparación
            texto_normalizado = texto_campo.strip().lower()
            mensaje_normalizado = mensaje_esperado.strip().lower()
            
            # Método 1: Verificar si el mensaje completo está presente
            if mensaje_normalizado in texto_normalizado:
                return True
            
            # Método 2: Verificar si al menos 80% del contenido coincide
            palabras_mensaje = set(mensaje_normalizado.split())
            palabras_campo = set(texto_normalizado.split())
            
            if palabras_mensaje:
                palabras_coincidentes = palabras_mensaje.intersection(palabras_campo)
                porcentaje_coincidencia = len(palabras_coincidentes) / len(palabras_mensaje)
                
                if porcentaje_coincidencia >= 0.8:  # 80% de coincidencia
                    return True
            
            # Método 3: Verificar si hay una coincidencia parcial significativa
            # Buscar frases clave del mensaje en el campo
            frases_clave = mensaje_normalizado.split('\n')[:3]  # Primeras 3 líneas
            frases_encontradas = 0
            
            for frase in frases_clave:
                if frase.strip() and frase.strip() in texto_normalizado:
                    frases_encontradas += 1
            
            if frases_clave and frases_encontradas >= len(frases_clave) * 0.7:  # 70% de frases
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error verificando mensaje presente: {str(e)}")
            return False
    
    def verificar_mensaje_enviado_automatico(self, driver):
        """Verificar si el mensaje se envió automáticamente por WhatsApp Web"""
        try:
            # Esperar un poco más para que se procese completamente
            time.sleep(3)
            
            # Verificar si el campo de texto está vacío (indicador principal de envío automático)
            text_box = None
            try:
                text_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="6"]')
            except:
                try:
                    text_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
                except:
                    pass
            
            if text_box:
                texto_actual = text_box.get_attribute('innerHTML') or text_box.text or text_box.get_attribute('textContent') or ""
                if not texto_actual.strip():
                    return True
            
            # Verificar con JavaScript para mayor precisión
            try:
                mensaje_enviado = driver.execute_script("""
                    // Verificar si el campo de texto está vacío (indicador principal de envío automático)
                    const textBox = document.querySelector('div[contenteditable="true"]');
                    if (textBox && (!textBox.textContent || textBox.textContent.trim() === '')) {
                        return true;
                    }
                    
                    // Verificar si hay mensajes enviados recientemente (últimos 10 segundos)
                    const mensajesEnviados = document.querySelectorAll('div[data-testid="msg-meta"].message-out');
                    if (mensajesEnviados.length > 0) {
                        // Verificar que el mensaje sea reciente
                        const ultimoMensaje = mensajesEnviados[mensajesEnviados.length - 1];
                        const timestamp = ultimoMensaje.querySelector('span[data-testid="msg-meta"]');
                        if (timestamp) {
                            return true;
                        }
                    }
                    
                    // Verificar si hay indicadores de envío reciente (checkmarks)
                    const indicadoresEnvio = document.querySelectorAll('div[data-testid="msg-meta"] span[data-testid="msg-check"]');
                    if (indicadoresEnvio.length > 0) {
                        return true;
                    }
                    
                    // Verificar si hay mensajes con contenido completo reciente
                    const mensajesRecientes = document.querySelectorAll('div[data-testid="msg-meta"]');
                    if (mensajesRecientes.length > 0) {
                        // Verificar que el último mensaje tenga contenido sustancial (no solo una línea)
                        const ultimoMensaje = mensajesRecientes[mensajesRecientes.length - 1];
                        const contenido = ultimoMensaje.textContent || '';
                        if (contenido.length > 50) { // Mensaje con contenido sustancial
                            return true;
                        }
                    }
                    
                    return false;
                """)
                return mensaje_enviado
            except:
                pass
            
            return False
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error verificando envío automático: {str(e)}")
            return False
    
    def verificar_mensaje_enviado(self, driver):
        """Verificar si el mensaje se envió realmente"""
        try:
            # Esperar un poco para que se procese el envío
            time.sleep(3)
            
            # Verificar si el campo de texto está vacío (indicador de envío exitoso)
            text_box = None
            try:
                text_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="6"]')
            except:
                try:
                    text_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
                except:
                    pass
            
            if text_box:
                texto_actual = text_box.get_attribute('innerHTML') or text_box.text
                if not texto_actual.strip():
                    return True
            
            # Verificar si hay mensajes en el chat (indicador de envío)
            try:
                mensajes = driver.find_elements(By.XPATH, '//div[@data-testid="msg-meta"]')
                if len(mensajes) > 0:
                    return True
            except:
                pass
            
            # Verificar con JavaScript
            try:
                mensaje_enviado = driver.execute_script("""
                    // Verificar si el campo de texto está vacío
                    const textBox = document.querySelector('div[contenteditable="true"]');
                    if (textBox && (!textBox.textContent || textBox.textContent.trim() === '')) {
                        return true;
                    }
                    
                    // Verificar si hay mensajes en el chat
                    const mensajes = document.querySelectorAll('div[data-testid="msg-meta"]');
                    if (mensajes.length > 0) {
                        return true;
                    }
                    
                    return false;
                """)
                return mensaje_enviado
            except:
                pass
            
            return False
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error verificando envío: {str(e)}")
            return False
    
    def cleanup(self):
        """Limpiar recursos"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
    
    def limpiar_sesion_whatsapp(self):
        """Limpiar la sesión persistente de WhatsApp Web"""
        try:
            import shutil
            import os
            
            user_data_dir = os.path.join(os.getcwd(), "whatsapp_session")
            if os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir)
                self.log_message("🧹 Sesión de WhatsApp Web limpiada")
                messagebox.showinfo("Sesión Limpiada", "La sesión persistente de WhatsApp Web ha sido eliminada.\n\nLa próxima vez que ejecutes el programa, necesitarás escanear el código QR nuevamente.")
            else:
                messagebox.showinfo("Sin Sesión", "No hay sesión persistente para limpiar.")
        except Exception as e:
            self.log_message(f"❌ Error limpiando sesión: {str(e)}")
            messagebox.showerror("Error", f"Error limpiando sesión: {str(e)}")
    
    def verificar_sesion_whatsapp(self):
        """Verificar si existe una sesión persistente de WhatsApp Web"""
        try:
            import os
            user_data_dir = os.path.join(os.getcwd(), "whatsapp_session")
            if os.path.exists(user_data_dir):
                # Verificar si hay archivos de sesión
                session_files = os.listdir(user_data_dir)
                if session_files:
                    self.log_message("💾 Sesión persistente detectada")
                    return True
            return False
        except Exception as e:
            self.log_message(f"⚠️ Error verificando sesión: {str(e)}")
            return False
    
    # ===================== Funciones de Gestión de Progreso =====================
    def guardar_progreso(self, indice):
        """Guardar el progreso actual en archivo JSON"""
        try:
            with open(PROGRESO_FILE, "w") as f:
                json.dump({"indice": indice, "fecha": datetime.now().isoformat()}, f)
        except Exception as e:
            self.log_message(f"⚠️ Error guardando progreso: {str(e)}")
    
    def cargar_progreso(self):
        """Cargar el progreso guardado desde archivo JSON"""
        try:
            if os.path.exists(PROGRESO_FILE):
                with open(PROGRESO_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("indice", 0)
            return 0
        except Exception as e:
            self.log_message(f"⚠️ Error cargando progreso: {str(e)}")
            return 0
    
    def borrar_progreso(self):
        """Borrar el archivo de progreso"""
        try:
            if os.path.exists(PROGRESO_FILE):
                os.remove(PROGRESO_FILE)
                self.log_message("🗑️ Progreso guardado eliminado")
        except Exception as e:
            self.log_message(f"⚠️ Error borrando progreso: {str(e)}")
    
    def mostrar_dialogo_progreso(self, progreso_prev, total_contactos):
        """Mostrar diálogo para reanudar envío"""
        mensaje = f"Se detectó un envío previo detenido en el contacto {progreso_prev + 1} de {total_contactos}.\n\n¿Deseas continuar desde ahí?"
        return messagebox.askyesno("Reanudar Envío", mensaje)
    
    def mostrar_info_progreso(self):
        """Mostrar información del progreso guardado"""
        try:
            if os.path.exists(PROGRESO_FILE):
                with open(PROGRESO_FILE, "r") as f:
                    data = json.load(f)
                    indice = data.get("indice", 0)
                    fecha = data.get("fecha", "Desconocida")
                    
                    mensaje = f"📋 Información del Progreso Guardado:\n\n"
                    mensaje += f"• Contactos procesados: {indice}\n"
                    mensaje += f"• Fecha del último envío: {fecha}\n"
                    mensaje += f"• Archivo: {PROGRESO_FILE}"
                    
                    messagebox.showinfo("Información de Progreso", mensaje)
            else:
                messagebox.showinfo("Sin Progreso", "No hay progreso guardado.")
        except Exception as e:
            messagebox.showerror("Error", f"Error leyendo progreso: {str(e)}")
    
    def probar_formato_plantilla(self):
        """Probar el formato de la plantilla actual"""
        try:
            # Obtener plantilla actual
            plantilla_original = self.template_text.get(1.0, tk.END)
            
            # Crear mensaje de prueba
            mensaje_prueba = self.crear_mensaje_personalizado(
                "Juan Pérez", 
                "ABC123", 
                "14:30",
                "2 personas"
            )
            
            # Crear ventana de prueba
            test_window = tk.Toplevel(self.root)
            test_window.title("🧪 Prueba de Formato de Plantilla")
            test_window.geometry("800x600")
            test_window.configure(bg="#ffffff")
            
            # Frame para plantilla original
            original_frame = tk.LabelFrame(test_window, text="📝 Plantilla Original", 
                                         font=("Segoe UI", 10, "bold"), bg="#ffffff")
            original_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD,
                                                     font=("Consolas", 10),
                                                     bg="#f8f9fa", fg="#202124",
                                                     height=8)
            original_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            original_text.insert(1.0, plantilla_original)
            original_text.config(state=tk.DISABLED)
            
            # Frame para mensaje procesado
            processed_frame = tk.LabelFrame(test_window, text="✅ Mensaje Procesado", 
                                          font=("Segoe UI", 10, "bold"), bg="#ffffff")
            processed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            processed_text = scrolledtext.ScrolledText(processed_frame, wrap=tk.WORD,
                                                      font=("Consolas", 10),
                                                      bg="#e8f5e8", fg="#202124",
                                                      height=8)
            processed_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            processed_text.insert(1.0, mensaje_prueba)
            processed_text.config(state=tk.DISABLED)
            
            # Información adicional
            info_frame = tk.Frame(test_window, bg="#ffffff")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(info_frame, text="🔍 Compara el formato original con el procesado",
                    font=("Segoe UI", 9), bg="#ffffff", fg="#1a73e8").pack()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error probando formato: {str(e)}")
    
    def probar_emojis(self):
        """Probar el manejo de emojis en las plantillas"""
        try:
            # Obtener plantilla actual
            plantilla_original = self.template_text.get(1.0, tk.END)
            
            # Crear mensaje de prueba con emojis
            mensaje_prueba = self.crear_mensaje_personalizado(
                "María García", 
                "XYZ789", 
                "16:45",
                "4 personas"
            )
            
            # Contar emojis en la plantilla original y en el mensaje procesado
            emojis_plantilla = [char for char in plantilla_original if ord(char) > 0xFFFF]
            emojis_mensaje = [char for char in mensaje_prueba if ord(char) > 0xFFFF]
            
            # Crear ventana de prueba de emojis
            test_window = tk.Toplevel(self.root)
            test_window.title("😊 Prueba de Emojis")
            test_window.geometry("900x700")
            test_window.configure(bg="#ffffff")
            
            # Frame para información de emojis
            info_frame = tk.LabelFrame(test_window, text="📊 Información de Emojis", 
                                     font=("Segoe UI", 10, "bold"), bg="#ffffff")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            info_text = f"Emojis en plantilla original: {len(emojis_plantilla)}\n"
            info_text += f"Emojis en mensaje procesado: {len(emojis_mensaje)}\n"
            info_text += f"Estado: {'✅ Preservados' if len(emojis_mensaje) == len(emojis_plantilla) else '❌ Perdidos'}\n\n"
            
            if emojis_plantilla:
                info_text += "Emojis detectados en plantilla:\n"
                for i, emoji in enumerate(emojis_plantilla[:10], 1):  # Mostrar solo los primeros 10
                    info_text += f"  {i}. {emoji} (U+{ord(emoji):X})\n"
                if len(emojis_plantilla) > 10:
                    info_text += f"  ... y {len(emojis_plantilla) - 10} más\n"
            
            info_label = tk.Label(info_frame, text=info_text, font=("Segoe UI", 9),
                                bg="#ffffff", fg="#202124", justify=tk.LEFT)
            info_label.pack(padx=10, pady=10)
            
            # Frame para plantilla original
            original_frame = tk.LabelFrame(test_window, text="📝 Plantilla Original", 
                                         font=("Segoe UI", 10, "bold"), bg="#ffffff")
            original_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD,
                                                     font=("Consolas", 10),
                                                     bg="#f8f9fa", fg="#202124",
                                                     height=8)
            original_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            original_text.insert(1.0, plantilla_original)
            original_text.config(state=tk.DISABLED)
            
            # Frame para mensaje procesado
            processed_frame = tk.LabelFrame(test_window, text="✅ Mensaje Procesado", 
                                          font=("Segoe UI", 10, "bold"), bg="#ffffff")
            processed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            processed_text = scrolledtext.ScrolledText(processed_frame, wrap=tk.WORD,
                                                      font=("Consolas", 10),
                                                      bg="#e8f5e8", fg="#202124",
                                                      height=8)
            processed_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            processed_text.insert(1.0, mensaje_prueba)
            processed_text.config(state=tk.DISABLED)
            
            # Botón para copiar mensaje procesado
            copy_btn = tk.Button(test_window, text="📋 Copiar Mensaje Procesado",
                                command=lambda: self.copiar_al_portapapeles(mensaje_prueba),
                                font=("Segoe UI", 9, "bold"), bg="#1a73e8", fg="white",
                                relief="flat", bd=0, padx=15, pady=5)
            copy_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error probando emojis: {str(e)}")
    
    def copiar_al_portapapeles(self, texto):
        """Copiar texto al portapapeles"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(texto)
            messagebox.showinfo("Copiado", "Mensaje copiado al portapapeles")
        except Exception as e:
            messagebox.showerror("Error", f"Error copiando al portapapeles: {str(e)}")
    
    def clear_log(self):
        """Limpiar log"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🧹 Log limpiado")
    
    def log_message(self, message, level="INFO"):
        """Agregar mensaje al log con nivel de importancia"""
        # Verificar nivel de logging
        levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        if levels.get(level, 1) < levels.get(self._log_level, 1):
            return
        
        timestamp = time.strftime("%H:%M:%S")
        level_icon = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}
        icon = level_icon.get(level, "ℹ️")
        
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        # Agregar al widget de texto
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Guardar en archivo si está habilitado
        if self._log_to_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except Exception as e:
                # Si falla el logging a archivo, no interrumpir la aplicación
                pass
        
        # Actualizar interfaz
        self.root.update_idletasks()
    
    def set_log_level(self, level):
        """Configurar nivel de logging"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if level.upper() in valid_levels:
            self._log_level = level.upper()
            self.log_message(f"Nivel de logging cambiado a: {level}", "INFO")
        else:
            self.log_message(f"Nivel de logging inválido: {level}. Usando INFO", "WARNING")
    
    def toggle_file_logging(self, enabled=True):
        """Activar/desactivar logging a archivo"""
        self._log_to_file = enabled
        status = "activado" if enabled else "desactivado"
        self.log_message(f"Logging a archivo {status}", "INFO")
    
    def clear_log_file(self):
        """Limpiar archivo de log"""
        try:
            if os.path.exists(self._log_file):
                os.remove(self._log_file)
                self.log_message("Archivo de log limpiado", "INFO")
        except Exception as e:
            self.log_message(f"Error limpiando archivo de log: {e}", "ERROR")
    
    def _consolidar_contactos_duplicados(self, contactos):
        """
        Consolidar contactos duplicados del mismo cliente por día.
        
        Agrupa múltiples reservas del mismo cliente para la misma fecha
        en un solo contacto consolidado con todas las matrículas y ocupantes.
        
        Args:
            contactos (list): Lista de contactos a consolidar
            
        Returns:
            list: Lista de contactos consolidados
        """
        if not contactos:
            return contactos
        
        # Crear diccionario para agrupar por teléfono y fecha
        grupos = {}
        
        for contacto in contactos:
            # Crear clave única: teléfono + fecha
            clave = f"{contacto['telefono']}_{contacto['fecha_entrada']}"
            
            if clave not in grupos:
                grupos[clave] = []
            grupos[clave].append(contacto)
        
        # Consolidar cada grupo
        contactos_consolidados = []
        
        for clave, grupo in grupos.items():
            if len(grupo) == 1:
                # Solo una reserva, mantener como está
                contactos_consolidados.append(grupo[0])
            else:
                # Múltiples reservas, consolidar
                contacto_consolidado = self._crear_contacto_consolidado(grupo)
                contactos_consolidados.append(contacto_consolidado)
                
                # Log de consolidación
                self.log_message(f"    🔗 Consolidado {len(grupo)} reservas para {contacto_consolidado['nombre']}")
                self.log_message(f"       📋 Matrículas: {', '.join(contacto_consolidado['matriculas'])}")
                self.log_message(f"       👥 Total ocupantes: {contacto_consolidado['ocupantes_total']}")
        
        return contactos_consolidados
    
    def _crear_contacto_consolidado(self, grupo):
        """
        Crear un contacto consolidado a partir de un grupo de reservas.
        
        Args:
            grupo (list): Lista de contactos del mismo cliente y fecha
            
        Returns:
            dict: Contacto consolidado
        """
        # Tomar el primer contacto como base
        base = grupo[0]
        
        # Recolectar todas las matrículas únicas
        matriculas = list(set([c['matricula'] for c in grupo if c['matricula'] != 'Sin matrícula']))
        
        # Calcular total de ocupantes
        ocupantes_total = 0
        for contacto in grupo:
            try:
                ocupantes = str(contacto['ocupantes']).strip()
                if ocupantes.isdigit():
                    ocupantes_total += int(ocupantes)
                elif 'persona' in ocupantes.lower():
                    # Extraer número de "X personas"
                    import re
                    match = re.search(r'(\d+)', ocupantes)
                    if match:
                        ocupantes_total += int(match.group(1))
                    else:
                        ocupantes_total += 1
                else:
                    ocupantes_total += 1
            except:
                ocupantes_total += 1
        
        # Crear contacto consolidado
        contacto_consolidado = {
            'nombre': base['nombre'],
            'telefono': base['telefono'],
            'matricula': ', '.join(matriculas) if matriculas else 'Sin matrícula',
            'matriculas': matriculas,  # Lista de matrículas
            'hora_entrada': base['hora_entrada'],
            'fecha_entrada': base['fecha_entrada'],
            'tipo_plaza': base['tipo_plaza'],
            'ocupantes': f"{ocupantes_total} personas",
            'ocupantes_total': ocupantes_total,
            'reservas_count': len(grupo),
            'consolidado': True  # Marcar como consolidado
        }
        
        return contacto_consolidado
    
    def mostrar_info_columnas(self):
        """Mostrar información detallada sobre la configuración de columnas"""
        try:
            plantilla_actual = self.plantilla_actual.get()
            
            # Crear ventana de información
            info_window = tk.Toplevel(self.root)
            info_window.title("📋 Información de Configuración de Columnas")
            info_window.geometry("700x500")
            info_window.configure(bg="#ffffff")
            
            # Frame principal
            main_frame = tk.Frame(info_window, bg="#ffffff")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Título
            titulo = tk.Label(main_frame, 
                             text="📋 Configuración de Columnas por Plantilla",
                             font=("Segoe UI", 16, "bold"),
                             bg="#ffffff", fg="#1a73e8")
            titulo.pack(pady=(0, 20))
            
            # Información de la plantilla actual
            plantilla_frame = tk.LabelFrame(main_frame, text="🎯 Plantilla Actual", 
                                          font=("Segoe UI", 12, "bold"), bg="#ffffff")
            plantilla_frame.pack(fill=tk.X, pady=(0, 15))
            
            plantilla_info = tk.Label(plantilla_frame, 
                                     text=f"Plantilla seleccionada: {plantilla_actual}",
                                     font=("Segoe UI", 11), bg="#ffffff", fg="#202124")
            plantilla_info.pack(padx=15, pady=10)
            
            # Configuración de columnas
            config_frame = tk.LabelFrame(main_frame, text="📊 Configuración de Columnas", 
                                       font=("Segoe UI", 12, "bold"), bg="#ffffff")
            config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            if plantilla_actual == "Recogidas":
                config_text = """📞 COLUMNA PRINCIPAL: 'Nº Vuelo VUELTA'
• Busca automáticamente columnas que contengan 'VUELTA' o 'VUELO'
• Extrae solo los números del campo
• Requiere mínimo 9 dígitos para ser válido

🔄 COLUMNA DE RESPALDO: 'NIF'
• Se usa si no se encuentra columna de vuelo
• Se usa si la columna de vuelo no contiene número válido

📋 OTRAS COLUMNAS:
• Nombre: Columna 'Cliente'
• Matrícula: Columna 'Matricula'
• Hora: Columna 'Hora entrada'
• Fecha: Columna 'Fecha entrada'"""
            else:
                config_text = """📞 COLUMNA PRINCIPAL: 'NIF'
• Campo estándar para números de teléfono
• Soporte para números españoles e internacionales

📋 OTRAS COLUMNAS:
• Nombre: Columna 'Cliente'
• Matrícula: Columna 'Matricula'
• Hora: Columna 'Hora entrada'
• Fecha: Columna 'Fecha entrada'"""
            
            config_label = tk.Label(config_frame, text=config_text,
                                   font=("Segoe UI", 10), bg="#ffffff", fg="#202124",
                                   justify=tk.LEFT)
            config_label.pack(padx=15, pady=15)
            
            # Información del archivo actual (si está cargado)
            if self.excel_path.get():
                archivo_frame = tk.LabelFrame(main_frame, text="📁 Archivo Actual", 
                                            font=("Segoe UI", 12, "bold"), bg="#ffffff")
                archivo_frame.pack(fill=tk.X, pady=(0, 15))
                
                try:
                    df = pd.read_excel(self.excel_path.get())
                    columnas_disponibles = list(df.columns)
                    
                    # Buscar columnas relevantes
                    columnas_vuelo = [col for col in columnas_disponibles if "VUELTA" in col.upper() or "VUELO" in col.upper()]
                    columnas_nif = [col for col in columnas_disponibles if "NIF" in col.upper()]
                    
                    archivo_info = f"Archivo: {os.path.basename(self.excel_path.get())}\n"
                    archivo_info += f"Total columnas: {len(columnas_disponibles)}\n"
                    
                    if plantilla_actual == "Recogidas":
                        if columnas_vuelo:
                            archivo_info += f"✅ Columnas de vuelo encontradas: {', '.join(columnas_vuelo)}\n"
                        else:
                            archivo_info += "⚠️ No se encontraron columnas de vuelo\n"
                    
                    if columnas_nif:
                        archivo_info += f"📞 Columnas NIF encontradas: {', '.join(columnas_nif)}\n"
                    else:
                        archivo_info += "⚠️ No se encontraron columnas NIF\n"
                    
                    archivo_label = tk.Label(archivo_frame, text=archivo_info,
                                           font=("Segoe UI", 10), bg="#ffffff", fg="#202124",
                                           justify=tk.LEFT)
                    archivo_label.pack(padx=15, pady=10)
                    
                except Exception as e:
                    error_label = tk.Label(archivo_frame, 
                                          text=f"Error leyendo archivo: {str(e)}",
                                          font=("Segoe UI", 10), bg="#ffffff", fg="#ea4335")
                    error_label.pack(padx=15, pady=10)
            else:
                archivo_label = tk.Label(main_frame, 
                                       text="📁 No hay archivo Excel cargado",
                                       font=("Segoe UI", 10), bg="#ffffff", fg="#5f6368")
                archivo_label.pack(pady=10)
            
            # Botón cerrar
            cerrar_btn = tk.Button(main_frame, text="Cerrar",
                                  command=info_window.destroy,
                                  font=("Segoe UI", 10, "bold"), bg="#1a73e8", fg="white",
                                  relief="flat", bd=0, padx=20, pady=8)
            cerrar_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error mostrando información: {str(e)}")
    
    def _extraer_numero_telefono_vuelo(self, valor_vuelo):
        """
        Extraer número de teléfono de un campo de vuelo que puede contener texto mezclado.
        
        Args:
            valor_vuelo (str): Valor del campo de vuelo (ej: 'T4-T4-IB23677-609553462')
            
        Returns:
            str: Número de teléfono extraído o cadena vacía si no se encuentra
        """
        try:
            if not valor_vuelo or valor_vuelo == 'nan':
                return ""
            
            valor_limpio = str(valor_vuelo).strip()
            
            # Buscar secuencias de 9 o más dígitos consecutivos
            import re
            
            # Patrón 1: Buscar números de 9+ dígitos al final del string
            patron_final = r'(\d{9,})$'
            match_final = re.search(patron_final, valor_limpio)
            if match_final:
                numero = match_final.group(1)
                if self.es_telefono_valido(numero):
                    return numero
            
            # Patrón 2: Buscar números de 9+ dígitos precedidos por espacios o guiones
            patron_espaciado = r'[-\s](\d{9,})'
            match_espaciado = re.search(patron_espaciado, valor_limpio)
            if match_espaciado:
                numero = match_espaciado.group(1)
                if self.es_telefono_valido(numero):
                    return numero
            
            # Patrón 3: Buscar cualquier secuencia de 9+ dígitos
            patron_general = r'(\d{9,})'
            matches = re.findall(patron_general, valor_limpio)
            for numero in matches:
                if self.es_telefono_valido(numero):
                    return numero
            
            # Si no se encuentra con patrones, intentar extraer todos los dígitos
            todos_digitos = ''.join(filter(str.isdigit, valor_limpio))
            if len(todos_digitos) >= 9:
                # Buscar la secuencia más larga de dígitos consecutivos
                secuencias = re.findall(r'\d+', valor_limpio)
                for secuencia in secuencias:
                    if len(secuencia) >= 9 and self.es_telefono_valido(secuencia):
                        return secuencia
            
            return ""
            
        except Exception as e:
            self.log_message(f"    ⚠️ Error extrayendo número de vuelo: {str(e)}")
            return ""

def main():
    """Función principal"""
    root = tk.Tk()
    app = WhatsAppSenderGUIMejorado(root)
    
    # Configurar cierre
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Salir", "El envío está en progreso. ¿Deseas salir?"):
                app.stop_sending()
                app.cleanup()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Maximizar ventana
    root.state('zoomed')  # Para Windows
    try:
        root.attributes('-zoomed', True)  # Para Linux
    except:
        pass
    
    # Iniciar aplicación
    root.mainloop()

if __name__ == "__main__":
    main() 