import cv2
from pyzbar.pyzbar import decode
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credenciales = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
cliente = gspread.authorize(credenciales)

# Abre la hoja de cálculo
spreadsheet = cliente.open("AsistenciaQR")  # nombre de tu hoja de cálculo
hoja_lista = spreadsheet.worksheet("Lista")  # hoja con la lista de participantes
hoja_asistencia = spreadsheet.worksheet("Asistencia")  # hoja para guardar asistencias

# Carga la lista de participantes
def cargar_lista():
    data = hoja_lista.get_all_records()
    return pd.DataFrame(data)

# Registra asistencia en la hoja
def registrar_asistencia(telefono, df_lista):
    try:
        telefono = int(telefono)
    except ValueError:
        print("Número inválido.")
        return

    persona = df_lista[df_lista["Telefono"] == telefono]
    if not persona.empty:
        nombre = persona.iloc[0]["Nombre"]
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Verificar duplicados en hoja de asistencia
        registros = hoja_asistencia.get_all_records()
        for registro in registros:
            if int(registro["Telefono"]) == telefono and registro["Hora"].startswith(ahora[:10]):
                print(f"{nombre} ya registró asistencia hoy.")
                return

        hoja_asistencia.append_row([nombre, telefono, ahora])
        print(f"Asistencia registrada: {nombre} - {telefono} - {ahora}")
    else:
        print(f"Teléfono {telefono} no está en la lista.")

# Menú principal
def main():
    df_lista = cargar_lista()

    print("Opciones:")
    print("1. Escanear código QR")
    print("2. Ingresar teléfono manualmente")
    opcion = input("Selecciona una opción (1 o 2): ")

    if opcion == "1":
        cap = cv2.VideoCapture(0)
        print("Escanea el código QR (presiona 'q' para salir)")
        while True:
            success, frame = cap.read()
            for code in decode(frame):
                telefono = code.data.decode("utf-8")
                registrar_asistencia(telefono, df_lista)
                df_lista = cargar_lista()  # Recargar lista por si cambia en línea

            cv2.imshow("Escaner QR", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    elif opcion == "2":
        while True:
            telefono = input("Ingresa el número de teléfono (o 'salir' para terminar): ")
            if telefono.lower() == "salir":
                break
            registrar_asistencia(telefono, df_lista)
            df_lista = cargar_lista()

    else:
        print("Opción no válida.")

if __name__ == "__main__":
    main()