import io
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageTk


# ============================================================
# CONFIGURACIÓN
# ============================================================

ANCHO_VISTA = 900
ALTO_VISTA = 650
ANCHO_INICIAL_SELLO = 120  # Ancho inicial en puntos PDF

NOMBRES_SELLOS = [
    "Sello1.png",
    "Sello2.png",
    "Sello3.png",
    "Sello4.png",
    "Sello5.png",
    "Sello6.png",
    "Sello7.png",
    "Sello8.png",
]


def obtener_ruta_sellos():
    """Obtiene la carpeta de sellos al ejecutar Python o el EXE."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent

    return base / "docs" / "sellos"


# ============================================================
# EDITOR DE SELLOS
# ============================================================

class EditorSellosPDF:

    def __init__(self, ventana_principal):
        self.ventana = tk.Toplevel(ventana_principal)
        self.ventana.title("Insertar sellos en PDF")
        self.ventana.geometry("1150x750")
        self.ventana.minsize(950, 650)

        self.ruta_pdf = None
        self.documento = None
        self.numero_pagina = 0

        self.imagenes_originales = {}
        self.imagenes_tk = []
        self.imagen_fondo_tk = None

        # Los sellos se guardan por número de página.
        # Cada sello almacena su posición y tamaño en puntos PDF.
        self.sellos_por_pagina = {}
        self.sello_seleccionado = None

        self.escala = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.arrastrando = False
        self.posicion_arrastre = None

        self._cargar_imagenes_sellos()
        self._construir_interfaz()

        self.ventana.transient(ventana_principal)
        self.ventana.grab_set()

    # --------------------------------------------------------
    # CARGA DE RECURSOS
    # --------------------------------------------------------

    def _cargar_imagenes_sellos(self):
        carpeta = obtener_ruta_sellos()

        for nombre in NOMBRES_SELLOS:
            ruta = carpeta / nombre

            if ruta.exists():
                try:
                    imagen = Image.open(ruta).convert("RGBA")
                    self.imagenes_originales[nombre] = imagen
                except Exception as error:
                    print(f"No se pudo cargar {nombre}: {error}")
            else:
                print(f"No se encontró el sello: {ruta}")

    # --------------------------------------------------------
    # INTERFAZ
    # --------------------------------------------------------

    def _construir_interfaz(self):
        barra_superior = tk.Frame(self.ventana)
        barra_superior.pack(fill="x", padx=10, pady=8)

        tk.Button(
            barra_superior,
            text="Abrir PDF",
            command=self.abrir_pdf
        ).pack(side="left", padx=4)

        self.etiqueta_archivo = tk.Label(
            barra_superior,
            text="Ningún PDF seleccionado",
            anchor="w"
        )
        self.etiqueta_archivo.pack(
            side="left", padx=10, fill="x", expand=True
        )

        cuerpo = tk.Frame(self.ventana)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)

        # Panel de previsualización
        panel_vista = tk.Frame(cuerpo)
        panel_vista.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            panel_vista,
            width=ANCHO_VISTA,
            height=ALTO_VISTA,
            background="#555555",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar_sello)
        self.canvas.bind("<ButtonRelease-1>", self.terminar_arrastre)
        self.canvas.bind("<Configure>", self._redibujar_si_hay_pdf)
        self.canvas.bind("<MouseWheel>", self.navegar_con_rueda)
        self.canvas.bind("<Button-4>", self.navegar_con_rueda)
        self.canvas.bind("<Button-5>", self.navegar_con_rueda)

        # Panel lateral
        panel_lateral = tk.Frame(cuerpo, width=210)
        panel_lateral.pack(side="right", fill="y", padx=(10, 0))
        panel_lateral.pack_propagate(False)

        tk.Label(
            panel_lateral,
            text="Sellos disponibles",
            font=("Arial", 11, "bold")
        ).pack(pady=(5, 8))

        for nombre in NOMBRES_SELLOS:
            boton = tk.Button(
                panel_lateral,
                text=nombre.replace(".png", ""),
                command=lambda n=nombre: self.agregar_sello(n)
            )
            boton.pack(fill="x", padx=5, pady=3)

            if nombre not in self.imagenes_originales:
                boton.configure(state="disabled")

        tk.Label(
            panel_lateral,
            text="Tamaño del sello",
            font=("Arial", 10, "bold")
        ).pack(pady=(20, 5))

        self.variable_tamano = tk.IntVar(value=100)

        self.control_tamano = tk.Scale(
            panel_lateral,
            from_=20,
            to=250,
            orient="horizontal",
            variable=self.variable_tamano,
            label="Porcentaje del tamaño inicial",
            command=self.cambiar_tamano
        )
        self.control_tamano.pack(fill="x", padx=5)

        tk.Label(
            panel_lateral,
            text="Rotación de sello",
            font=("Arial", 10, "bold")
        ).pack(pady=(15, 5))

        self.etiqueta_rotacion = tk.Label(
            panel_lateral,
            text="Rotación: 0°",
        )
        self.etiqueta_rotacion.pack()

        marco_rotacion=tk.Frame(panel_lateral)
        marco_rotacion.pack(fill="x", padx="5", pady=5)

        tk.Button(
            marco_rotacion,
            text="↶ -90°",
            command=lambda: self.rotar_sello(-90)
        ).pack(side="left", expand="True", fill="x", padx=2)

        tk.Button(
            marco_rotacion,
            text="↷ +90°",
            command=lambda: self.rotar_sello(90)
        ).pack(side="left", expand="True", fill="x", padx=2)

        tk.Button(
            panel_lateral,
            text="Eliminar sello seleccionado",
            command=self.eliminar_sello
        ).pack(fill="x", padx=5, pady=(12, 5))

        tk.Label(
            panel_lateral,
            text=(
                "Haz clic en un sello y arrástralo.\n"
                "Usa el control para cambiar su tamaño."
            ),
            justify="left",
            wraplength=190
        ).pack(padx=5, pady=10)

        # Navegación y guardado
        barra_inferior = tk.Frame(self.ventana)
        barra_inferior.pack(fill="x", padx=10, pady=10)

        self.boton_anterior = tk.Button(
            barra_inferior,
            text="◀ Página anterior",
            command=self.pagina_anterior,
            state="disabled"
        )
        self.boton_anterior.pack(side="left", padx=4)

        self.etiqueta_pagina = tk.Label(
            barra_inferior,
            text="Página: —"
        )
        self.etiqueta_pagina.pack(side="left", padx=10)

        tk.Label(
            barra_inferior,
            text="Ir a página:"
        ).pack(side="left", padx=(12, 4))
        self.variable_pagina=tk.StringVar()
        self.entrada_pagina=tk.Entry(
            barra_inferior,
            textvariable=self.variable_pagina,
            width=6,
            justify="center"
        )
        self.entrada_pagina.pack(side="left", padx=4)

        self.entrada_pagina.bind(
            "<Return>",
            lambda evento: self.ir_a_pagina()
        )

        tk.Button(
            barra_inferior,
            text="Ir",
            command=self.ir_a_pagina
        ).pack(side="left", padx=4)

        self.boton_siguiente = tk.Button(
            barra_inferior,
            text="Página siguiente ▶",
            command=self.pagina_siguiente,
            state="disabled"
        )
        self.boton_siguiente.pack(side="left", padx=4)

        tk.Button(
            barra_inferior,
            text="Guardar PDF nuevo",
            command=self.guardar_pdf
        ).pack(side="right", padx=4)

    # --------------------------------------------------------
    # ABRIR Y MOSTRAR PDF
    # --------------------------------------------------------

    def abrir_pdf(self):
        ruta = filedialog.askopenfilename(
            parent=self.ventana,
            title="Seleccionar PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )

        if not ruta:
            return

        try:
            nuevo_documento = fitz.open(ruta)

            if nuevo_documento.page_count == 0:
                nuevo_documento.close()
                messagebox.showwarning(
                    "PDF vacío",
                    "El archivo seleccionado no contiene páginas.",
                    parent=self.ventana
                )
                return

            if self.documento is not None:
                self.documento.close()

            self.documento = nuevo_documento
            self.ruta_pdf = Path(ruta)
            self.numero_pagina = 0
            self.sellos_por_pagina.clear()
            self.sello_seleccionado = None

            self.etiqueta_archivo.configure(
                text=self.ruta_pdf.name
            )

            self.boton_anterior.configure(state="disabled")
            self.boton_siguiente.configure(
                state=(
                    "normal"
                    if self.documento.page_count > 1
                    else "disabled"
                )
            )

            self.mostrar_pagina()

        except Exception as error:
            messagebox.showerror(
                "Error al abrir PDF",
                f"No se pudo abrir el archivo:\n{error}",
                parent=self.ventana
            )

    def mostrar_pagina(self):
        if self.documento is None:
            return

        pagina = self.documento[self.numero_pagina]
        rect = pagina.rect

        ancho_canvas = max(self.canvas.winfo_width(), ANCHO_VISTA)
        alto_canvas = max(self.canvas.winfo_height(), ALTO_VISTA)

        margen = 30
        escala_x = (ancho_canvas - margen * 2) / rect.width
        escala_y = (alto_canvas - margen * 2) / rect.height

        self.escala = min(escala_x, escala_y)

        pixmap = pagina.get_pixmap(
            matrix=fitz.Matrix(self.escala, self.escala),
            alpha=False
        )

        imagen_pagina = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples
        )

        self.imagen_fondo_tk = ImageTk.PhotoImage(imagen_pagina)

        self.offset_x = (ancho_canvas - pixmap.width) / 2
        self.offset_y = (alto_canvas - pixmap.height) / 2

        self.canvas.delete("all")
        self.canvas.create_image(
            self.offset_x,
            self.offset_y,
            anchor="nw",
            image=self.imagen_fondo_tk,
            tags=("pagina_pdf",)
        )

        if self.sello_seleccionado is None:
            self.etiqueta_rotacion.configure(text="Rotación: 0°")

        self._dibujar_sellos()

        total = self.documento.page_count
        self.etiqueta_pagina.configure(
            text=f"Página {self.numero_pagina + 1} de {total}"
        )
        self.variable_pagina.set(str(self.numero_pagina + 1))

        self.boton_anterior.configure(
            state="normal" if self.numero_pagina > 0 else "disabled"
        )
        self.boton_siguiente.configure(
            state=(
                "normal"
                if self.numero_pagina < total - 1
                else "disabled"
            )
        )

    def _redibujar_si_hay_pdf(self, evento=None):
        if self.documento is not None:
            self.ventana.after_idle(self.mostrar_pagina)
    """-----------"""
    def ir_a_pagina(self):
        """Navega directamente a la página indicada por el usuario."""
        if self.documento is None:
            return

        texto = self.variable_pagina.get().strip()

        try:
            numero = int(texto)
        except ValueError:
            messagebox.showwarning(
                "Número de página inválido",
                "Introduce un número entero de página.",
                parent=self.ventana
            )
            self.entrada_pagina.focus_set()
            self.entrada_pagina.selection_range(0, tk.END)
            return

        total = self.documento.page_count

        if numero < 1 or numero > total:
            messagebox.showwarning(
                "Página fuera de rango",
                f"Introduce un número entre 1 y {total}.",
                parent=self.ventana
            )
            self.entrada_pagina.focus_set()
            self.entrada_pagina.selection_range(0, tk.END)
            return

        self.numero_pagina = numero - 1
        self.sello_seleccionado = None
        self.mostrar_pagina()

    def navegar_con_rueda(self, evento):
        """Avanza o retrocede una página con la rueda del mouse."""
        if self.documento is None:
            return "break"

        # Windows y macOS: MouseWheel.
        # En Windows, delta suele ser positivo hacia arriba
        # y negativo hacia abajo.
        if getattr(evento, "num", None) == 4:
            direccion = -1
        elif getattr(evento, "num", None) == 5:
            direccion = 1
        elif getattr(evento, "delta", 0) > 0:
            direccion = -1
        elif getattr(evento, "delta", 0) < 0:
            direccion = 1
        else:
            return "break"

        nueva_pagina = self.numero_pagina + direccion

        # Evitar salir de los límites del documento.
        nueva_pagina = max(
            0,
            min(nueva_pagina, self.documento.page_count - 1)
        )

        if nueva_pagina != self.numero_pagina:
            self.numero_pagina = nueva_pagina
            self.sello_seleccionado = None
            self.mostrar_pagina()

        return "break"

    """-------"""

    # --------------------------------------------------------
    # SELLOS: DIBUJAR Y AÑADIR
    # --------------------------------------------------------

    def _sellos_actuales(self):
        return self.sellos_por_pagina.setdefault(
            self.numero_pagina, []
        )
    
    def _dibujar_sellos(self):
        self.imagenes_tk.clear()

        for sello in self._sellos_actuales():
            imagen_original = self.imagenes_originales[sello["nombre"]]

            # Calcular el tamaño base del sello en la previsualización.
            ancho_px = max(1, int(sello["ancho"] * self.escala))
            alto_px = max(1, int(sello["alto"] * self.escala))

            imagen = imagen_original.resize(
                (ancho_px, alto_px),
                Image.Resampling.LANCZOS
            )

            # Aplicar la rotación solo a la imagen de previsualización.
            angulo = sello.get("rotacion", 0)

            if angulo:
                imagen = imagen.rotate(
                    angulo,
                    expand=True,
                    resample=Image.Resampling.BICUBIC
                )

            # Guardar la imagen para que Tkinter no la elimine
            # mientras se está mostrando en el lienzo.
            imagen_tk = ImageTk.PhotoImage(imagen)
            self.imagenes_tk.append(imagen_tk)

            # Dimensiones de la imagen después de rotarla.
            ancho_rotado_px, alto_rotado_px = imagen.size

            # Mantener el centro del sello en la posición seleccionada.
            ancho_original_px = sello["ancho"] * self.escala
            alto_original_px = sello["alto"] * self.escala

            centro_x = (
                self.offset_x
                + (sello["x"] + sello["ancho"] / 2) * self.escala
            )

            centro_y = (
                self.offset_y
                + (sello["y"] + sello["alto"] / 2) * self.escala
            )

            x = centro_x - ancho_rotado_px / 2
            y = centro_y - alto_rotado_px / 2

            # Dibujar el sello rotado.
            sello["canvas_id"] = self.canvas.create_image(
                x,
                y,
                anchor="nw",
                image=imagen_tk,
                tags=("sello",)
            )

            # Dibujar el marco de selección alrededor del sello.
            if sello is self.sello_seleccionado:
                self.canvas.create_rectangle(
                    x,
                    y,
                    x + ancho_rotado_px,
                    y + alto_rotado_px,
                    outline="#00A8FF",
                    width=2,
                    tags=("seleccion",)
                )


    

    def agregar_sello(self, nombre):
        if self.documento is None:
            messagebox.showwarning(
                "Selecciona un PDF",
                "Primero abre el PDF en el que deseas insertar sellos.",
                parent=self.ventana
            )
            return

        if nombre not in self.imagenes_originales:
            messagebox.showerror(
                "Sello no disponible",
                f"No se pudo cargar {nombre}.",
                parent=self.ventana
            )
            return

        pagina = self.documento[self.numero_pagina]
        imagen = self.imagenes_originales[nombre]

        ancho = min(ANCHO_INICIAL_SELLO, pagina.rect.width * 0.5)
        alto = ancho * imagen.height / imagen.width

        x = max(0, (pagina.rect.width - ancho) / 2)
        y = max(0, (pagina.rect.height - alto) / 2)

        sello = {
            "nombre": nombre,
            "x": x,
            "y": y,
            "ancho": ancho,
            "alto": alto,
            "ancho_inicial": ancho,
            "alto_inicial": alto,
            "rotacion": 0,
            "canvas_id": None,
        }

        self._sellos_actuales().append(sello)
        self.sello_seleccionado = sello
        self.variable_tamano.set(100)
        self.mostrar_pagina()

    # --------------------------------------------------------
    # SELECCIÓN Y MOVIMIENTO
    # --------------------------------------------------------

    def iniciar_arrastre(self, evento):
        self.arrastrando = False
        self.sello_seleccionado = None

        # Revisar primero los objetos que están encima de otros.
        objetos = self.canvas.find_overlapping(
            evento.x, evento.y, evento.x, evento.y
        )

        for objeto in reversed(objetos):
            if "sello" not in self.canvas.gettags(objeto):
                continue

            for sello in self._sellos_actuales():
                if sello.get("canvas_id") == objeto:
                    self.sello_seleccionado = sello
                    self.etiqueta_rotacion.configure(
                        text=f"Rotación: {sello.get('rotacion', 0)}°"
                    )
                    self.arrastrando = True
                    self.posicion_arrastre = (
                        evento.x,
                        evento.y,
                        sello["x"],
                        sello["y"]
                    )

                    self.variable_tamano.set(
                        round(
                            100 * sello["ancho"] /
                            sello["ancho_inicial"]
                        )
                    )
                    self.mostrar_pagina()
                    return

        self.mostrar_pagina()

    def arrastrar_sello(self, evento):
        if not self.arrastrando or self.sello_seleccionado is None:
            return

        x_inicial, y_inicial, sello_x, sello_y = self.posicion_arrastre

        desplazamiento_x = (evento.x - x_inicial) / self.escala
        desplazamiento_y = (evento.y - y_inicial) / self.escala

        pagina = self.documento[self.numero_pagina]
        sello = self.sello_seleccionado

        nuevo_x = sello_x + desplazamiento_x
        nuevo_y = sello_y + desplazamiento_y

        nuevo_x = max(
            0,
            min(nuevo_x, pagina.rect.width - sello["ancho"])
        )
        nuevo_y = max(
            0,
            min(nuevo_y, pagina.rect.height - sello["alto"])
        )

        sello["x"] = nuevo_x
        sello["y"] = nuevo_y

        self.mostrar_pagina()

    def terminar_arrastre(self, evento):
        self.arrastrando = False
        self.posicion_arrastre = None



    def rotar_sello(self, grados):
        """Rota el sello seleccionado en incrementos de 90 grados."""
        if self.sello_seleccionado is None:
            messagebox.showinfo(
                "Seleccionar sello",
                "Primero selecciona un sello",
                parent=self.ventana
            )
            return
        sello=self.sello_seleccionado
        sello["rotacion"]=(sello.get("rotacion", 0) + grados)%360
        self.etiqueta_rotacion.configure(
            text=f"Ángulo: {sello['rotacion']}°"
        )
        self.mostrar_pagina()

    # --------------------------------------------------------
    # CAMBIAR TAMAÑO Y ELIMINAR SELLO
    # --------------------------------------------------------

    def cambiar_tamano(self, valor):
        if self.sello_seleccionado is None:
            return

        porcentaje = float(valor) / 100
        sello = self.sello_seleccionado

        sello["ancho"] = sello["ancho_inicial"] * porcentaje
        sello["alto"] = sello["alto_inicial"] * porcentaje

        pagina = self.documento[self.numero_pagina]

        sello["x"] = max(
            0,
            min(sello["x"], pagina.rect.width - sello["ancho"])
        )
        sello["y"] = max(
            0,
            min(sello["y"], pagina.rect.height - sello["alto"])
        )

        self.mostrar_pagina()

    def eliminar_sello(self):
        if self.sello_seleccionado is None:
            messagebox.showinfo(
                "Seleccionar sello",
                "Haz clic en un sello para seleccionarlo primero.",
                parent=self.ventana
            )
            return

        sellos = self._sellos_actuales()
        sellos.remove(self.sello_seleccionado)
        self.sello_seleccionado = None
        self.mostrar_pagina()

    # --------------------------------------------------------
    # NAVEGACIÓN
    # --------------------------------------------------------

    def pagina_anterior(self):
        if self.documento is None or self.numero_pagina <= 0:
            return

        self.numero_pagina -= 1
        self.sello_seleccionado = None
        self.mostrar_pagina()

    def pagina_siguiente(self):
        if (
            self.documento is None
            or self.numero_pagina >= self.documento.page_count - 1
        ):
            return

        self.numero_pagina += 1
        self.sello_seleccionado = None
        self.mostrar_pagina()

    # --------------------------------------------------------
    # GUARDAR PDF
    # --------------------------------------------------------

    
    def guardar_pdf(self):
        if self.documento is None or self.ruta_pdf is None:
            messagebox.showwarning(
                "Selecciona un PDF",
                "Primero abre el PDF que deseas modificar.",
                parent=self.ventana
            )
            return

        ruta_salida = filedialog.asksaveasfilename(
            parent=self.ventana,
            title="Guardar PDF con sellos",
            initialdir=str(self.ruta_pdf.parent),
            initialfile=f"{self.ruta_pdf.stem}_sellado.pdf",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )

        if not ruta_salida:
            return

        destino = Path(ruta_salida).resolve()
        origen = self.ruta_pdf.resolve()

        if destino == origen:
            messagebox.showerror(
                "Ruta no permitida",
                "Guarda el resultado con un nombre distinto al PDF original.",
                parent=self.ventana
            )
            return

        if destino.exists():
            if not messagebox.askyesno(
                "Confirmar reemplazo",
                "El archivo de destino ya existe. ¿Deseas reemplazarlo?",
                parent=self.ventana
            ):
                return

        try:
            with fitz.open(str(origen)) as documento_salida:

                for numero_pagina, lista_sellos in self.sellos_por_pagina.items():
                    pagina = documento_salida[numero_pagina]

                    # Una página puede contener varios sellos.
                    for sello in lista_sellos:
                        ruta_imagen = obtener_ruta_sellos() / sello["nombre"]

                        if not ruta_imagen.is_file():
                            raise FileNotFoundError(
                                f"No se encontró el archivo: {ruta_imagen}"
                            )

                        rotacion_usuario = sello.get("rotacion", 0) % 360

                        # Dimensiones originales del sello en puntos PDF.
                        ancho = sello["ancho"]
                        alto = sello["alto"]

                        # Dimensiones de la caja visible después de rotar.
                        if rotacion_usuario in (90, 270):
                            ancho_visible, alto_visible = alto, ancho
                        else:
                            ancho_visible, alto_visible = ancho, alto

                        # Centro del sello en las coordenadas visibles del editor.
                        centro_x = sello["x"] + ancho / 2
                        centro_y = sello["y"] + alto / 2

                        rectangulo_vista = fitz.Rect(
                            centro_x - ancho_visible / 2,
                            centro_y - alto_visible / 2,
                            centro_x + ancho_visible / 2,
                            centro_y + alto_visible / 2
                        )

                        # Las coordenadas visibles deben convertirse al
                        # sistema interno del PDF.
                        rectangulo_pdf = (
                            rectangulo_vista * pagina.derotation_matrix
                        )

                        # Preparar la imagen a una resolución suficiente,
                        # manteniendo la proporción original del sello.
                        with Image.open(ruta_imagen) as original:
                            imagen = original.convert("RGBA")

                        ancho_px = max(1, round(ancho * 4))
                        alto_px = max(1, round(alto * 4))

                        imagen = imagen.resize(
                            (ancho_px, alto_px),
                            Image.Resampling.LANCZOS
                        )

                        # Compensar la rotación de la página para que,
                        # al visualizar el PDF, el sello conserve el ángulo
                        # elegido en el editor.
                        rotacion_imagen = (
                            rotacion_usuario + pagina.rotation
                        ) % 360

                        if rotacion_imagen:
                            imagen = imagen.rotate(
                                rotacion_imagen,
                                expand=True,
                                resample=Image.Resampling.BICUBIC
                            )

                        buffer = io.BytesIO()
                        imagen.save(buffer, format="PNG")
                        imagen_bytes = buffer.getvalue()
                        buffer.close()

                        pagina.insert_image(
                            rectangulo_pdf,
                            stream=imagen_bytes,
                            overlay=True,
                            keep_proportion=False
                        )

                documento_salida.save(
                    str(destino),
                    garbage=4,
                    deflate=True
                )

            messagebox.showinfo(
                "PDF guardado",
                f"El archivo se guardó correctamente en:\n{destino}",
                parent=self.ventana
            )

        except Exception as error:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo guardar el archivo:\n{error}",
                parent=self.ventana
            )



# ============================================================
# FUNCIÓN PÚBLICA PARA main.py
# ============================================================

def insertar_sellos(ventana_principal):
    EditorSellosPDF(ventana_principal)
