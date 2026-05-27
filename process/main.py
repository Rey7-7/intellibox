import os
from tkinter import *
import tkinter as Tk
from tkinter import ttk
import imutils
from PIL import Image, ImageTk
import cv2
import sqlite3
from tkinter import messagebox

try:
    from process.gui.image_paths import ImagePaths
    from process.database.config import DataBasePaths
    from process.face_processing.face_signup import FaceSignUp
    from process.face_processing.face_login import FaceLogIn
    from process.com_interface.serial_com import SerialCommunication
except ImportError as e:
    print(f"Error de importación crítica: {e}")

    class ImagePaths:
        pass

    class DataBasePaths:
        users = "./"

    class FaceSignUp:
        def process(self, f, id):
            return f, False, ""

    class FaceLogIn:
        def process(self, f):
            return f, False, ""

    class SerialCommunication:
        def sending_data(self, d):
            print(f"[Sim Serial] Enviando: {d}")

class CustomFrame(Tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill=Tk.BOTH, expand=True)


class GraphicalUserInterface:
    def __init__(self, root):
        self.main_window = root
        self.main_window.title('intellibox facial check')
        self.main_window.geometry('1280x720')
        self.frame = CustomFrame(self.main_window)

        self.db_path = 'process/database/intellibox.db'

        # camara
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280) 
        self.cap.set(4, 720)

        # ventana
        self.signup_window = None
        self.input_name = None
        self.name = None
        self.user_code = None

        # capturar pantalla
        self.face_signup_window = None
        self.signup_video = None

        # ventana de login
        self.face_login_window = None
        self.login_video = None

        # ventana de usuarios
        self.users_window = None

        # ventana de acceso concedido
        self.access_window = None

        # modulos
        self.images = ImagePaths()
        self.database = DataBasePaths()
        self.face_sign_up = FaceSignUp()
        self.face_login = FaceLogIn()
        self.com = SerialCommunication()

        self.ensure_db_setup()

        # proceso
        self.main()

    # asegurar la base de datos
    def ensure_db_setup(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (
                                  id
                                  INTEGER
                                  PRIMARY
                                  KEY
                                  AUTOINCREMENT,
                                  name
                                  TEXT
                                  NOT
                                  NULL
                              )''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error de DB: {e}.")

    # animar botones
    def animate_button(self, button, original_x, original_y):
        def on_press(event):
            button.place(x=original_x, y=original_y + 3)

        def on_release(event):
            button.place(x=original_x, y=original_y)

        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)

    # cerrar pantalla principal
    def close_login(self):
        self.com.sending_data('C')
        
        # Limpiamos variables de IA sin sobrecargar la memoria
        self.face_login.cont_frame = 0
        self.face_login.comparison = False
        self.face_login.matcher = None
        
        # Destruir ventana padre es suficiente
        if getattr(self, 'face_login_window', None):
            self.face_login_window.destroy()
            self.face_login_window = None

    # acceder
    def facial_login(self):
        if self.cap:
            ret, frame_bgr = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame, user_access, info = self.face_login.process(frame)
                frame = imutils.resize(frame, width=1280)
                im = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=im)
                self.login_video.configure(image=img)
                self.login_video.image = img

                # ciclo
                if getattr(self, 'login_handled', False) is False:
                    self.login_video.after(10, self.facial_login)

                if user_access is True and getattr(self, 'login_handled', False) is False:
                    self.login_handled = True
                    self.com.sending_data('A')
                    self.login_video.after(1000, self.goto_access)

                elif user_access is False and getattr(self, 'login_handled', False) is False:
                    self.login_handled = True
                    self.com.sending_data('C')
                    self.login_video.after(2000, self.close_login)
        else:
            self.cap.release()

    # pantalla acceder
    def gui_login(self):
        self.login_handled = False

        self.face_login_window = Toplevel()
        self.face_login_window.title('facial login')
        self.face_login_window.geometry('1280x720')
        self.login_video = Label(self.face_login_window)
        self.login_video.place(x=0, y=0)
        self.facial_login()

     # ir a acceso concedido
    def goto_access(self):
        # Limpiamos variables de IA
        self.face_login.cont_frame = 0
        self.face_login.comparison = False
        self.face_login.matcher = None
        
        if getattr(self, 'face_login_window', None):
            self.face_login_window.destroy()
            self.face_login_window = None

        self.main_window.withdraw()
        self.gui_access_granted()

    # pantalla de acceso concedido
    def gui_access_granted(self):
        self.access_window = Toplevel(self.frame)
        self.access_window.title('access granted')
        self.access_window.geometry("1280x720")

        if hasattr(self.images, 'access_bg_img'):
            bg_img = ImageTk.PhotoImage(Image.open(self.images.access_bg_img))
            bg_label = Label(self.access_window, image=bg_img)
            bg_label.image = bg_img
            bg_label.place(x=0, y=0)

        if hasattr(self.images, 'return_btn'):
            return_btn_img = ImageTk.PhotoImage(Image.open(self.images.return_btn))
            return_btn = Button(self.access_window, image=return_btn_img,
                                command=self.close_access_granted,
                                borderwidth=0, highlightthickness=0, relief=FLAT)
            return_btn.image = return_btn_img
            return_btn.place(x=439, y=579, width=416, height=55)

            # ... (código del return_btn) ...
            self.animate_button(return_btn, 439, 579)

        self.scale_label = Label(self.access_window, text="Esperando movimientos...",
                                 font=("Arial", 28, "bold"), bg="#11181f", fg="#00ff00")
        self.scale_label.place(x=400, y=300)

        reset_btn = Button(self.access_window, text="Resetear Sensor", bg="#d9534f", fg="white",
                           font=("Arial", 12, "bold"), borderwidth=0, cursor="hand2",
                           command=lambda: self.com.sending_data('T'))
        reset_btn.place(x=50, y=50, width=150, height=40)

        # El ciclo de escucha siempre va al final
        self.check_serial_data()

    def check_serial_data(self):
        if self.access_window and self.access_window.winfo_exists():
            data = self.com.read_data()

            if data:
                print(f"ESP32 dice: {data}")

                if data.startswith("BASCULA:"):
                    mensaje = data.replace("BASCULA:", "")
                    self.scale_label.config(text=mensaje)

                elif data == "ESTADO:CERRADA_AUTO":
                    print("La cerradura se bloqueó físicamente por seguridad.")

            self.access_window.after(100, self.check_serial_data)

    # cerrar acceso concedido
    def close_access_granted(self):
        self.com.sending_data('C')

        if self.access_window:
            self.access_window.destroy()

        self.main_window.deiconify()

    # pantalla usuarios
    def gui_users(self):
        self.users_window = Toplevel(self.frame)
        self.users_window.title('registered users')
        self.users_window.geometry("800x600")

        Label(self.users_window, text="Usuarios Registrados", font=("Arial", 20, "bold")).pack(pady=20)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 11), rowheight=25)

        # columna nomre
        columns = ('name',)
        tree = ttk.Treeview(self.users_window, columns=columns, show='headings')
        tree.heading('name', text='Nombre Completo')
        tree.pack(fill=Tk.BOTH, expand=True, padx=40, pady=10)

        # cargar los datos
        def load_data():
            for item in tree.get_children():
                tree.delete(item)
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT name FROM users ORDER BY name ASC")
                results = cursor.fetchall()
                conn.close()
                for r in results:
                    tree.insert('', Tk.END, values=(r[0],))
            except Exception as e:
                print(f"Error cargando usuarios: {e}")

        # borrar al usuario seleccionado
        def delete_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Precaución", "Selecciona un usuario de la lista para borrar.",
                                       parent=self.users_window)
                return

            # obtener el nombre
            item = tree.item(selected[0])
            user_name = item['values'][0]

            # confirmación
            confirm = messagebox.askyesno("Confirmar",
                                          f"¿Estás seguro de que deseas eliminar a '{user_name}'?\n\n"
                                          "Esto borrará todos sus registros y accesos asociados en la base de datos.",
                                          parent=self.users_window)
            if confirm:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    # Borra de un golpe todas las filas que tengan ese nombre
                    cursor.execute("DELETE FROM users WHERE name = ?", (user_name,))
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Eliminado", f"Usuario '{user_name}' eliminado correctamente.",
                                        parent=self.users_window)
                    load_data()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {e}",
                                         parent=self.users_window)

        load_data()

        # botón borrar
        delete_btn = Button(self.users_window, text="Borrar Seleccionado", bg="#d9534f", fg="white",
                            font=("Arial", 12, "bold"), borderwidth=0, cursor="hand2", command=delete_user)
        delete_btn.pack(pady=15, ipadx=20, ipady=5)

    # cerrar registro
    def close_signup(self):
        # Evitamos reinstanciar la IA
        if getattr(self, 'face_signup_window', None):
            self.face_signup_window.destroy()
            self.face_signup_window = None

    # registrar rostro
    def facial_sign_up(self):
        if self.cap:
            ret, frame_bgr = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame, save_image, info = self.face_sign_up.process(frame, self.user_code)
                frame = imutils.resize(frame, width=1280)
                im = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=im)
                self.signup_video.configure(image=img)
                self.signup_video.image = img
                self.signup_video.after(10, self.facial_sign_up)

                if save_image:
                    self.signup_video.after(3000, self.close_signup)
        else:
            self.cap.release()

    # datos del registro (solo nombre)
    def data_sign_up(self):
        self.name = self.input_name.get().strip()
        if len(self.name) == 0:
            print('Ingrese el nombre')
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name) VALUES (?)", (self.name,))
            conn.commit()
            self.user_code = str(cursor.lastrowid)
            conn.close()
            print(f"Usuario {self.name} registrado.")
        except Exception as e:
            print(f"Error guardando datos: {e}")
            return

        self.input_name.delete(0, END)

        self.face_signup_window = Toplevel()
        self.face_signup_window.title('face capture')
        self.face_signup_window.geometry('1280x720')
        self.signup_video = Label(self.face_signup_window)
        self.signup_video.place(x=0, y=0)
        self.signup_window.destroy()
        self.facial_sign_up()

    # pantalla registro
    def gui_signup(self):
        self.signup_window = Toplevel(self.frame)
        self.signup_window.title('facial sign up')
        self.signup_window.geometry("1280x720")

        if hasattr(self.images, 'gui_signup_img'):
            bgs_img = ImageTk.PhotoImage(Image.open(self.images.gui_signup_img))
            background_signup = Label(self.signup_window, image=bgs_img)
            background_signup.image = bgs_img
            background_signup.place(x=0, y=0)

        bg_color_entry = "#11181f"

        self.input_name = Entry(self.signup_window, font=("Arial", 14),
                                bg=bg_color_entry, fg="white",
                                borderwidth=0, highlightthickness=0,
                                insertbackground="white")

        self.input_name.place(x=495, y=514, width=347, height=42)

        if hasattr(self.images, 'capture_btn'):
            capture_btn_img = ImageTk.PhotoImage(Image.open(self.images.capture_btn))
            register_button = Button(self.signup_window, image=capture_btn_img,
                                     command=self.data_sign_up,
                                     borderwidth=0, highlightthickness=0, relief=FLAT)
            register_button.image = capture_btn_img
            register_button.place(x=434, y=576, width=413, height=55)
            self.animate_button(register_button, 434, 576)

    # pantalla principal
    def main(self):
        if hasattr(self.images, 'init_img'):
            bgi_img = ImageTk.PhotoImage(Image.open(self.images.init_img))
            background = Label(self.frame, image=bgi_img)
            background.image = bgi_img
            background.place(x=0, y=0)

        if hasattr(self.images, 'acc_btn'):
            login_btn_img = ImageTk.PhotoImage(Image.open(self.images.acc_btn))
            login_button = Button(self.frame, image=login_btn_img, command=self.gui_login,
                                  borderwidth=0, highlightthickness=0, relief=FLAT)
            login_button.image = login_btn_img
            login_button.place(x=154, y=576, width=262, height=55)
            self.animate_button(login_button, 154, 576)

        if hasattr(self.images, 'ver_btn'):
            users_btn_img = ImageTk.PhotoImage(Image.open(self.images.ver_btn))
            users_button = Button(self.frame, image=users_btn_img, command=self.gui_users,
                                  borderwidth=0, highlightthickness=0, relief=FLAT)
            users_button.image = users_btn_img
            users_button.place(x=541, y=576, width=200, height=55)
            self.animate_button(users_button, 541, 576)

        if hasattr(self.images, 'reg_btn'):
            signup_btn_img = ImageTk.PhotoImage(Image.open(self.images.reg_btn))
            signup_button = Button(self.frame, image=signup_btn_img, command=self.gui_signup,
                                   borderwidth=0, highlightthickness=0, relief=FLAT)
            signup_button.image = signup_btn_img
            signup_button.place(x=866, y=576, width=262, height=55)
            self.animate_button(signup_button, 866, 576)


if __name__ == "__main__":
    root = Tk.Tk()
    app = GraphicalUserInterface(root)
    root.mainloop()