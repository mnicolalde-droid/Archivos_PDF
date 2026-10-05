import os
import fitz
import tkinter as tk
from tkinter import messagebox, filedialog


# ============================================================
# AGREGAR NUMERACIÓN A PDF
# ============================================================

def numerar_pdf(ventana_principal):

    # ========================================================
    # SELECCIONAR PDF
    # ========================================================

    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not archivo:
        return

    try:

        documento = fitz.open(archivo)

        total_paginas = len(documento)

        if total_paginas == 0:

            documento.close()

            messagebox.showwarning(
                "PDF vacío",
                "El archivo seleccionado no contiene páginas."
            )

            return

        # ====================================================
        # VENTANA DE CONFIGURACIÓN
        # ====================================================

        ventana_numero = tk.Toplevel(
            ventana_principal
        )

        ventana_numero.title(
            "Configuración de numeración"
        )

        ventana_numero.geometry(
            "500x420"
        )

        ventana_numero.resizable(
            False,
            False
        )

        tk.Label(
            ventana_numero,
            text="Agregar numeración al PDF",
            font=("Arial", 14, "bold")
        ).pack(pady=(20, 5))

        tk.Label(
            ventana_numero,
            text=f"El documento contiene {total_paginas} páginas.",
            font=("Arial", 10)
        ).pack(pady=(0, 20))

        # ====================================================
        # POSICIÓN
        # ====================================================

        tk.Label(
            ventana_numero,
            text="Posición de la numeración:",
            font=("Arial", 10, "bold")
        ).pack()

        posicion = tk.StringVar(
            value="Abajo derecha"
        )

        posiciones = [
            "Arriba izquierda",
            "Arriba derecha",
            "Abajo izquierda",
            "Abajo derecha"
        ]

        menu_posicion = tk.OptionMenu(
            ventana_numero,
            posicion,
            *posiciones
        )

        menu_posicion.config(
            width=20
        )

        menu_posicion.pack(
            pady=8
        )

        # ====================================================
        # TAMAÑO DE LETRA
        # ====================================================

        tk.Label(
            ventana_numero,
            text="Tamaño de letra:",
            font=("Arial", 10, "bold")
        ).pack(
            pady=(15, 0)
        )

        tamano = tk.StringVar(
            value="10"
        )

        entrada_tamano = tk.Entry(
            ventana_numero,
            textvariable=tamano,
            width=10,
            justify="center"
        )

        entrada_tamano.pack(
            pady=8
        )

        tk.Label(
            ventana_numero,
            text="Recomendado: 8 a 14",
            font=("Arial", 8)
        ).pack()

        # ====================================================
        # MARGEN
        # ====================================================

        tk.Label(
            ventana_numero,
            text="Margen desde el borde:",
            font=("Arial", 10, "bold")
        ).pack(
            pady=(15, 0)
        )

        margen = tk.StringVar(
            value="25"
        )

        entrada_margen = tk.Entry(
            ventana_numero,
            textvariable=margen,
            width=10,
            justify="center"
        )

        entrada_margen.pack(
            pady=8
        )

        tk.Label(
            ventana_numero,
            text="Margen expresado en puntos PDF.",
            font=("Arial", 8)
        ).pack()

        # ====================================================
        # CANCELAR
        # ====================================================

        def cancelar():

            documento.close()
            ventana_numero.destroy()

        # ====================================================
        # GENERAR PDF
        # ====================================================

        def generar():

            # -----------------------------------------------
            # Validar tamaño
            # -----------------------------------------------

            try:

                tamano_fuente = float(
                    tamano.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Valor inválido",
                    "El tamaño de letra debe ser un número.",
                    parent=ventana_numero
                )

                return

            if tamano_fuente <= 0:

                messagebox.showerror(
                    "Valor inválido",
                    "El tamaño de letra debe ser mayor que 0.",
                    parent=ventana_numero
                )

                return

            # -----------------------------------------------
            # Validar margen
            # -----------------------------------------------

            try:

                margen_numero = float(
                    margen.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Valor inválido",
                    "El margen debe ser un número.",
                    parent=ventana_numero
                )

                return

            if margen_numero < 0:

                messagebox.showerror(
                    "Valor inválido",
                    "El margen no puede ser negativo.",
                    parent=ventana_numero
                )

                return

            # -----------------------------------------------
            # Confirmación
            # -----------------------------------------------

            confirmacion = messagebox.askyesno(
                "Confirmar numeración",
                f"Se agregarán números del 1 al "
                f"{total_paginas}.\n\n"
                f"Formato: 1/{total_paginas}, "
                f"2/{total_paginas}, etc.\n\n"
                f"Posición: {posicion.get()}\n"
                f"Tamaño: {tamano_fuente}\n"
                f"Margen: {margen_numero}\n\n"
                f"¿Desea continuar?",
                parent=ventana_numero
            )

            if not confirmacion:
                return

            try:

                paginas_procesadas = 0

                # ============================================
                # PROCESAR CADA PÁGINA
                # ============================================

                for indice in range(total_paginas):

                    pagina = documento[indice]

                    numero_actual = indice + 1

                    texto = (
                        f"{numero_actual}/{total_paginas}"
                    )

                    rect = pagina.rect

                    ancho = rect.width
                    alto = rect.height

                    # ----------------------------------------
                    # Calcular ancho del texto
                    # ----------------------------------------

                    ancho_texto = (
                        fitz.get_text_length(
                            texto,
                            fontname="helv",
                            fontsize=tamano_fuente
                        )
                    )

                    # ----------------------------------------
                    # Posición vertical
                    # ----------------------------------------

                    if posicion.get().startswith("Arriba"):

                        y = (
                            margen_numero
                            + tamano_fuente
                        )

                    else:

                        y = (
                            alto
                            - margen_numero
                            - 2
                        )

                    # ----------------------------------------
                    # Posición horizontal
                    # ----------------------------------------

                    if posicion.get().endswith("izquierda"):

                        x = margen_numero

                    else:

                        x = (
                            ancho
                            - margen_numero
                            - ancho_texto
                        )

                    # ----------------------------------------
                    # Ajustar coordenadas según rotación
                    # ----------------------------------------

                    punto_insercion = (
                        fitz.Point(x, y)
                        * pagina.derotation_matrix
                    )

                    # ----------------------------------------
                    # Insertar texto
                    # ----------------------------------------

                    resultado = pagina.insert_text(
                        punto_insercion,
                        texto,
                        fontsize=tamano_fuente,
                        fontname="helv",
                        color=(0, 0, 0),
                        morph=(
                            punto_insercion,
                            fitz.Matrix(
                                pagina.rotation
                            )
                        ),
                        overlay=True
                    )

                    if resultado == 0:

                        raise Exception(
                            f"No fue posible insertar "
                            f"la numeración en la página "
                            f"{numero_actual}."
                        )

                    paginas_procesadas += 1

                # ============================================
                # GUARDAR ARCHIVO
                # ============================================

                nombre, extension = os.path.splitext(
                    archivo
                )

                archivo_salida = (
                    f"{nombre}_numerado.pdf"
                )

                documento.save(
                    archivo_salida,
                    garbage=4,
                    deflate=True
                )

                documento.close()

                ventana_numero.destroy()

                # ============================================
                # RESULTADO
                # ============================================

                messagebox.showinfo(
                    "Proceso terminado",
                    "El PDF fue numerado correctamente.\n\n"
                    f"Páginas procesadas: "
                    f"{paginas_procesadas}\n"
                    f"Formato: 1/{total_paginas} ... "
                    f"{total_paginas}/{total_paginas}\n\n"
                    f"Archivo generado:\n"
                    f"{archivo_salida}"
                )

            except Exception as error:

                messagebox.showerror(
                    "Error",
                    "No fue posible agregar la numeración.\n\n"
                    f"{error}",
                    parent=ventana_numero
                )

        # ====================================================
        # BOTONES
        # ====================================================

        marco_botones = tk.Frame(
            ventana_numero
        )

        marco_botones.pack(
            pady=20
        )

        tk.Button(
            marco_botones,
            text="CANCELAR",
            width=14,
            command=cancelar
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        tk.Button(
            marco_botones,
            text="NUMERAR PDF",
            width=16,
            font=("Arial", 9, "bold"),
            command=generar
        ).grid(
            row=0,
            column=1,
            padx=5
        )
    except Exception as error:
        messagebox.showerror(
            "Error",
            f"No fue posible procesar el PDF.\n\n{error}"
        )
