import os
import io
import fitz
import threading
import queue
import tkinter as tk

from PIL import Image
from tkinter import filedialog, messagebox, ttk


# ============================================================
# CONFIGURACIÓN
# ============================================================

DPI = 120
UMBRAL_BLANCO = 245
PORCENTAJE_MINIMO_CONTENIDO = 0.10


# ============================================================
# SELECCIONAR PDF
# ============================================================

def seleccionar_pdf():

    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    return archivo


# ============================================================
# ANALIZAR PÁGINA
# ============================================================

def analizar_pagina(pagina):

    matriz = fitz.Matrix(
        DPI / 72,
        DPI / 72
    )

    pix = pagina.get_pixmap(
        matrix=matriz,
        colorspace=fitz.csGRAY,
        alpha=False
    )

    imagen = Image.open(
        io.BytesIO(
            pix.tobytes("png")
        )
    ).convert("L")

    total_pixeles = (
        imagen.width * imagen.height
    )

    pixeles_contenido = sum(
        1
        for pixel in imagen.getdata()
        if pixel < UMBRAL_BLANCO
    )

    porcentaje_contenido = (
        pixeles_contenido / total_pixeles
    ) * 100

    tiene_contenido = (
        porcentaje_contenido
        >= PORCENTAJE_MINIMO_CONTENIDO
    )

    return (
        porcentaje_contenido,
        tiene_contenido
    )


# ============================================================
# ELIMINAR PÁGINAS VACÍAS
# ============================================================

def eliminar_paginas_vacias():

    archivo = seleccionar_pdf()

    if not archivo:
        return

    # --------------------------------------------------------
    # VENTANA DE PROGRESO
    # --------------------------------------------------------

    ventana = tk.Toplevel()
    ventana.title("Analizando PDF")
    ventana.geometry("780x625")
    ventana.resizable(True, True)

    # Evitar que quede detrás de la ventana principal
    ventana.transient()
    ventana.grab_set()

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------

    marco_superior = ttk.Frame(
        ventana,
        padding=15
    )

    marco_superior.pack(
        fill="x"
    )

    etiqueta_titulo = ttk.Label(
        marco_superior,
        text="Analizando PDF",
        font=("Arial", 14, "bold")
    )

    etiqueta_titulo.pack(
        anchor="w"
    )

    etiqueta_archivo = ttk.Label(
        marco_superior,
        text=f"Archivo: {os.path.basename(archivo)}"
    )

    etiqueta_archivo.pack(
        anchor="w",
        pady=(5, 0)
    )

    # --------------------------------------------------------
    # BARRA DE PROGRESO
    # --------------------------------------------------------

    marco_progreso = ttk.Frame(
        ventana,
        padding=(15, 0, 15, 10)
    )

    marco_progreso.pack(
        fill="x"
    )

    etiqueta_progreso = ttk.Label(
        marco_progreso,
        text="Preparando análisis..."
    )

    etiqueta_progreso.pack(
        anchor="w",
        pady=(0, 5)
    )

    barra_progreso = ttk.Progressbar(
        marco_progreso,
        orient="horizontal",
        mode="determinate"
    )

    barra_progreso.pack(
        fill="x"
    )

    # --------------------------------------------------------
    # ÁREA DE RESULTADOS
    # --------------------------------------------------------

    marco_resultados = ttk.Frame(
        ventana,
        padding=(15, 5, 15, 5)
    )

    marco_resultados.pack(
        fill="both",
        expand=True
    )

    texto_resultados = tk.Text(
        marco_resultados,
        wrap="none",
        font=("Consolas", 10),
        state="disabled"
    )

    scrollbar_vertical = ttk.Scrollbar(
        marco_resultados,
        orient="vertical",
        command=texto_resultados.yview
    )

    scrollbar_horizontal = ttk.Scrollbar(
        marco_resultados,
        orient="horizontal",
        command=texto_resultados.xview
    )

    texto_resultados.configure(
        yscrollcommand=scrollbar_vertical.set,
        xscrollcommand=scrollbar_horizontal.set
    )

    texto_resultados.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    scrollbar_vertical.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    scrollbar_horizontal.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    marco_resultados.rowconfigure(
        0,
        weight=1
    )

    marco_resultados.columnconfigure(
        0,
        weight=1
    )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    marco_resumen = ttk.Frame(
        ventana,
        padding=15
    )

    marco_resumen.pack(
        fill="x"
    )

    etiqueta_resumen = ttk.Label(
        marco_resumen,
        text="Conservadas: 0    Eliminadas: 0"
    )

    etiqueta_resumen.pack(
        anchor="w"
    )

    # --------------------------------------------------------
    # BOTÓN CERRAR
    # --------------------------------------------------------

    boton_cerrar = ttk.Button(
        ventana,
        text="Cerrar",
        state="disabled"
    )

    boton_cerrar.pack(
        pady=(0, 15)
    )

    # --------------------------------------------------------
    # COLA DE COMUNICACIÓN
    # --------------------------------------------------------

    cola = queue.Queue()

    # --------------------------------------------------------
    # FUNCIÓN PARA ESCRIBIR EN EL HISTORIAL
    # --------------------------------------------------------

    def escribir_resultado(mensaje):

        texto_resultados.configure(
            state="normal"
        )

        texto_resultados.insert(
            "end",
            mensaje + "\n"
        )

        texto_resultados.see(
            "end"
        )

        texto_resultados.configure(
            state="disabled"
        )

    # --------------------------------------------------------
    # PROCESAMIENTO
    # --------------------------------------------------------

    def procesar_pdf():

        documento = None
        nuevo_documento = None

        try:

            documento = fitz.open(
                archivo
            )

            total_paginas = len(
                documento
            )

            paginas_contenido = []
            paginas_vacias = []

            cola.put(
                (
                    "inicio",
                    total_paginas
                )
            )

            for numero, pagina in enumerate(
                documento
            ):

                porcentaje, tiene_contenido = (
                    analizar_pagina(pagina)
                )

                if tiene_contenido:

                    paginas_contenido.append(
                        numero
                    )

                    estado = "CONSERVAR"

                else:

                    paginas_vacias.append(
                        numero
                    )

                    estado = "ELIMINAR"

                cola.put(
                    (
                        "pagina",
                        numero + 1,
                        porcentaje,
                        estado,
                        len(paginas_contenido),
                        len(paginas_vacias)
                    )
                )

            # ------------------------------------------------
            # SI NO HAY PÁGINAS VACÍAS
            # ------------------------------------------------

            if not paginas_vacias:

                documento.close()
                documento = None

                cola.put(
                    (
                        "sin_vacias",
                        total_paginas,
                        len(paginas_contenido)
                    )
                )

                return

            # ------------------------------------------------
            # GENERAR ARCHIVO DE SALIDA
            # ------------------------------------------------

            nombre, extension = os.path.splitext(
                archivo
            )

            archivo_salida = (
                f"{nombre}_sin_paginas_vacias.pdf"
            )

            cola.put(
                (
                    "guardando",
                    archivo_salida
                )
            )

            nuevo_documento = fitz.open()

            for numero in paginas_contenido:

                nuevo_documento.insert_pdf(
                    documento,
                    from_page=numero,
                    to_page=numero
                )

            nuevo_documento.save(
                archivo_salida,
                garbage=4,
                deflate=True
            )

            nuevo_documento.close()
            nuevo_documento = None

            documento.close()
            documento = None

            cola.put(
                (
                    "terminado",
                    total_paginas,
                    len(paginas_contenido),
                    len(paginas_vacias),
                    archivo_salida
                )
            )

        except Exception as error:

            if nuevo_documento is not None:

                try:
                    nuevo_documento.close()
                except Exception:
                    pass

            if documento is not None:

                try:
                    documento.close()
                except Exception:
                    pass

            cola.put(
                (
                    "error",
                    str(error)
                )
            )

    # --------------------------------------------------------
    # ACTUALIZAR INTERFAZ
    # --------------------------------------------------------

    def actualizar_interfaz():

        try:

            while True:

                evento = cola.get_nowait()

                tipo = evento[0]

                # --------------------------------------------
                # INICIO
                # --------------------------------------------

                if tipo == "inicio":

                    total_paginas = evento[1]

                    barra_progreso["maximum"] = (
                        total_paginas
                    )

                    barra_progreso["value"] = 0

                    etiqueta_progreso.config(
                        text=f"Analizando 0 de "
                             f"{total_paginas} páginas..."
                    )

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        "INICIO DEL ANÁLISIS"
                    )

                    escribir_resultado(
                        f"Total de páginas: {total_paginas}"
                    )

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado("")

                # --------------------------------------------
                # PÁGINA ANALIZADA
                # --------------------------------------------

                elif tipo == "pagina":

                    numero = evento[1]
                    porcentaje = evento[2]
                    estado = evento[3]
                    conservadas = evento[4]
                    eliminadas = evento[5]

                    barra_progreso["value"] = numero

                    total = int(
                        barra_progreso["maximum"]
                    )

                    etiqueta_progreso.config(
                        text=f"Analizando página "
                             f"{numero} de {total}..."
                    )

                    # Mismo dato importante que se mostraba
                    # durante el análisis:
                    escribir_resultado(
                        f"Página {numero:>4} | "
                        f"{porcentaje:>8.3f}% | "
                        f"{estado}"
                    )

                    etiqueta_resumen.config(
                        text=f"Conservadas: {conservadas}    "
                             f"Eliminadas: {eliminadas}"
                    )

                # --------------------------------------------
                # GUARDANDO
                # --------------------------------------------

                elif tipo == "guardando":

                    archivo_salida = evento[1]

                    etiqueta_progreso.config(
                        text="Generando archivo PDF..."
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "Generando archivo de salida..."
                    )

                    escribir_resultado(
                        f"Archivo: "
                        f"{os.path.basename(archivo_salida)}"
                    )

                # --------------------------------------------
                # NO HAY PÁGINAS VACÍAS
                # --------------------------------------------

                elif tipo == "sin_vacias":

                    total_paginas = evento[1]
                    conservadas = evento[2]

                    etiqueta_progreso.config(
                        text="Análisis terminado."
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        "RESULTADO"
                    )

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        f"Páginas originales: {total_paginas}"
                    )

                    escribir_resultado(
                        f"Páginas conservadas: {conservadas}"
                    )

                    escribir_resultado(
                        "Páginas eliminadas: 0"
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "No se encontraron páginas vacías."
                    )

                    etiqueta_resumen.config(
                        text=f"Conservadas: {conservadas}    "
                             f"Eliminadas: 0"
                    )

                    boton_cerrar.config(
                        state="normal"
                    )

                    ventana.grab_release()

                # --------------------------------------------
                # PROCESO TERMINADO
                # --------------------------------------------

                elif tipo == "terminado":

                    total_paginas = evento[1]
                    conservadas = evento[2]
                    eliminadas = evento[3]
                    archivo_salida = evento[4]

                    barra_progreso["value"] = (
                        barra_progreso["maximum"]
                    )

                    etiqueta_progreso.config(
                        text="Proceso terminado correctamente."
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        "PROCESO TERMINADO"
                    )

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        f"Páginas originales: {total_paginas}"
                    )

                    escribir_resultado(
                        f"Páginas conservadas: {conservadas}"
                    )

                    escribir_resultado(
                        f"Páginas eliminadas: {eliminadas}"
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "Archivo generado:"
                    )

                    escribir_resultado(
                        archivo_salida
                    )

                    etiqueta_resumen.config(
                        text=f"Conservadas: {conservadas}    "
                             f"Eliminadas: {eliminadas}"
                    )

                    boton_cerrar.config(
                        state="normal"
                    )

                    ventana.grab_release()

                # --------------------------------------------
                # ERROR
                # --------------------------------------------

                elif tipo == "error":

                    mensaje = evento[1]

                    etiqueta_progreso.config(
                        text="Se produjo un error."
                    )

                    escribir_resultado("")

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        "ERROR"
                    )

                    escribir_resultado(
                        "=========================================="
                    )

                    escribir_resultado(
                        mensaje
                    )

                    boton_cerrar.config(
                        state="normal"
                    )

                    ventana.grab_release()

                    messagebox.showerror(
                        "Error",
                        f"No fue posible procesar "
                        f"el PDF.\n\n{mensaje}",
                        parent=ventana
                    )

                cola.task_done()

        except queue.Empty:

            pass

        # Continuar revisando la cola
        # mientras la ventana exista.
        if ventana.winfo_exists():

            ventana.after(
                100,
                actualizar_interfaz
            )

    # --------------------------------------------------------
    # CERRAR VENTANA
    # --------------------------------------------------------

    def cerrar_ventana():

        try:
            ventana.grab_release()
        except Exception:
            pass

        ventana.destroy()

    boton_cerrar.config(
        command=cerrar_ventana
    )

    # --------------------------------------------------------
    # EVITAR CIERRE DURANTE EL PROCESAMIENTO
    # --------------------------------------------------------

    def intentar_cerrar():

        if str(
            boton_cerrar["state"]
        ) == "normal":

            cerrar_ventana()

        else:

            messagebox.showinfo(
                "Proceso en ejecución",
                "El PDF todavía está siendo procesado.\n\n"
                "Por favor, espere a que finalice.",
                parent=ventana
            )

    ventana.protocol(
        "WM_DELETE_WINDOW",
        intentar_cerrar
    )

    # --------------------------------------------------------
    # INICIAR PROCESAMIENTO EN SEGUNDO PLANO
    # --------------------------------------------------------

    hilo = threading.Thread(
        target=procesar_pdf,
        daemon=True
    )

    hilo.start()

    # Comenzar actualización de interfaz
    ventana.after(
        100,
        actualizar_interfaz
    )
