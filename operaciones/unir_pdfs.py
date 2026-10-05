import os
import fitz
import tkinter as tk
from tkinter import filedialog, messagebox


def unir_pdfs(ventana_principal):

    archivos = filedialog.askopenfilenames(
        title="Seleccionar archivos PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not archivos:
        return

    archivos = list(archivos)

    ventana_union = tk.Toplevel(
        ventana_principal
    )

    ventana_union.title(
        "Unir archivos PDF"
    )

    ventana_union.geometry(
        "750x500"
    )

    ventana_union.resizable(
        False,
        False
    )

    tk.Label(
        ventana_union,
        text="Orden de los archivos:",
        font=("Arial", 11, "bold")
    ).pack(
        pady=(15, 5)
    )

    tk.Label(
        ventana_union,
        text="Utilice los botones para modificar el orden.",
        font=("Arial", 9)
    ).pack()

    marco_lista = tk.Frame(
        ventana_union
    )

    marco_lista.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    lista = tk.Listbox(
        marco_lista,
        width=85,
        height=15,
        font=("Arial", 9)
    )

    lista.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar = tk.Scrollbar(
        marco_lista,
        orient="vertical",
        command=lista.yview
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    lista.config(
        yscrollcommand=scrollbar.set
    )

    for archivo in archivos:

        lista.insert(
            tk.END,
            os.path.basename(archivo)
        )

    def actualizar_lista(
        indice_seleccionado=0
    ):

        lista.delete(
            0,
            tk.END
        )

        for archivo in archivos:

            lista.insert(
                tk.END,
                os.path.basename(archivo)
            )

        if archivos:

            indice_seleccionado = max(
                0,
                min(
                    indice_seleccionado,
                    len(archivos) - 1
                )
            )

            lista.selection_set(
                indice_seleccionado
            )

            lista.activate(
                indice_seleccionado
            )

    def subir():

        seleccion = lista.curselection()

        if not seleccion:
            return

        indice = seleccion[0]

        if indice == 0:
            return

        archivos[
            indice - 1
        ], archivos[indice] = (

            archivos[indice],
            archivos[indice - 1]
        )

        actualizar_lista(
            indice - 1
        )

    def bajar():

        seleccion = lista.curselection()

        if not seleccion:
            return

        indice = seleccion[0]

        if indice == len(archivos) - 1:
            return

        archivos[
            indice
        ], archivos[indice + 1] = (

            archivos[indice + 1],
            archivos[indice]
        )

        actualizar_lista(
            indice + 1
        )

    def quitar():

        seleccion = lista.curselection()

        if not seleccion:
            return

        indice = seleccion[0]

        archivos.pop(
            indice
        )

        actualizar_lista(
            min(
                indice,
                len(archivos) - 1
            )
        )

    marco_botones = tk.Frame(
        ventana_union
    )

    marco_botones.pack(
        pady=5
    )

    tk.Button(
        marco_botones,
        text="▲ Subir",
        width=12,
        command=subir
    ).grid(
        row=0,
        column=0,
        padx=5
    )

    tk.Button(
        marco_botones,
        text="▼ Bajar",
        width=12,
        command=bajar
    ).grid(
        row=0,
        column=1,
        padx=5
    )

    tk.Button(
        marco_botones,
        text="✖ Quitar",
        width=12,
        command=quitar
    ).grid(
        row=0,
        column=2,
        padx=5
    )

    def unir():

        if not archivos:

            messagebox.showwarning(
                "Sin archivos",
                "No hay archivos PDF para unir.",
                parent=ventana_union
            )

            return

        archivo_salida = filedialog.asksaveasfilename(
            title="Guardar PDF unido",
            defaultextension=".pdf",
            filetypes=[
                ("Archivos PDF", "*.pdf")
            ],
            initialfile="PDF_unido.pdf"
        )

        if not archivo_salida:
            return

        try:

            documento_final = fitz.open()

            for archivo in archivos:

                documento = fitz.open(
                    archivo
                )

                documento_final.insert_pdf(
                    documento
                )

                documento.close()

            documento_final.save(
                archivo_salida,
                garbage=4,
                deflate=True
            )

            documento_final.close()

            messagebox.showinfo(
                "Proceso terminado",
                "Los archivos PDF fueron unidos "
                "correctamente.\n\n"
                f"Archivo generado:\n"
                f"{archivo_salida}",
                parent=ventana_union
            )

            ventana_union.destroy()

        except Exception as error:

            messagebox.showerror(
                "Error",
                f"No fue posible unir los archivos.\n\n"
                f"{error}",
                parent=ventana_union
            )

    tk.Button(
        ventana_union,
        text="UNIR PDFs",
        width=20,
        height=2,
        font=("Arial", 10, "bold"),
        command=unir
    ).pack(
        pady=15
    )
