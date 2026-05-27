import serial

class SerialCommunication:
    def __init__(self):
        try:
            # COM Administrador de Dispositivos
            self.com = serial.Serial("COM6", 115200, timeout=0, write_timeout=10)
            print("Conexión serial establecida con éxito.")
        except serial.SerialException as e:
            # Imprime la razón real del fallo
            print(f"No se detectó ESP32 o el puerto es incorrecto. Error: {e}")
            print("Iniciando en modo simulación.")
    
            self.com = None

    def sending_data(self, data):
        
        if self.com is not None:
            try:
                self.com.write(data.encode('ascii'))
            except Exception as e:
                print(f"Error al enviar datos al ESP32: {e}")
        else:
            print(f"[Simulador] Comando virtual enviado a la chapa: {data}")

    def read_data(self):
        if self.com is not None:
            try:
                if self.com.in_waiting > 0:
                    line = self.com.readline().decode('ascii', errors='ignore').strip()
                    return line
            except Exception as e:
                print(f"Error leyendo la báscula: {e}")
        return None