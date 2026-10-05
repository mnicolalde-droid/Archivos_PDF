import os
import io
import fitz
from PIL import Image
from tkinter import filedialog, messagebox


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

    try:

        documento = fitz.open(archivo)

        paginas_contenido = []
        paginas_vacias = []

        for numero, pagina in enumerate(documento):

            porcentaje, tiene_contenido = (
                analizar_pagina(pagina)
            )

            if tiene_contenido:

                paginas_contenido.append(
                    numero
                )

            else:

                paginas_vacias.append(
                    numero
                )

        total_paginas = len(documento)

        if not paginas_vacias:

            messagebox.showinfo(
                "Resultado",
                "No se encontraron páginas vacías."
            )

            documento.close()
            return

        nombre, extension = os.path.splitext(
            archivo
        )

        archivo_salida = (
            f"{nombre}_sin_paginas_vacias.pdf"
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
        documento.close()

        messagebox.showinfo(
            "Proceso terminado",
            f"PDF procesado correctamente.\n\n"
            f"Páginas originales: {total_paginas}\n"
            f"Páginas conservadas: "
            f"{len(paginas_contenido)}\n"
            f"Páginas eliminadas: "
            f"{len(paginas_vacias)}\n\n"
            f"Archivo generado:\n"
            f"{archivo_salida}"
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            f"No fue posible procesar el PDF.\n\n"
            f"{error}"
        )
