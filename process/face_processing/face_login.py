import numpy as np
import sqlite3

from process.face_processing.face_utils import FaceUtils
from process.database.config import DataBasePaths


class FaceLogIn:
    def __init__(self):
        self.face_utilities = FaceUtils()
        self.database = DataBasePaths()

        self.db_path = 'process/database/intellibox.db'

        self.matcher = None
        self.comparison = False
        self.cont_frame = 0

    def process(self, face_image: np.ndarray):
        # detección de rostro
        check_face_detect, face_info, face_save = self.face_utilities.check_face(face_image)
        if check_face_detect is False:
            return face_image, self.matcher, '¡No face detected!'

        # crear la malla facial
        check_face_mesh, face_mesh_info = self.face_utilities.face_mesh(face_image)
        if check_face_mesh is False:
            return face_image, self.matcher, '¡No face mesh detected!'

        # extraer la malla facial
        face_mesh_points_list = self.face_utilities.extract_face_mesh(face_image, face_mesh_info)

        # obtener el centro de la cara
        check_face_center = self.face_utilities.check_face_center(face_mesh_points_list)

        # mostrar estado
        self.face_utilities.show_state_login(face_image, state=self.matcher)

        if check_face_center:
            # extraer info del rostro
            self.cont_frame = self.cont_frame + 1
            if self.cont_frame == 48:
                face_bbox = self.face_utilities.extract_face_bbox(face_image, face_info)
                face_points = self.face_utilities.extract_face_points(face_image, face_info)

                # cortar cara
                face_crop = self.face_utilities.face_crop(face_save, face_bbox)

                # leer base de datos
                faces_database, names_database, info = self.face_utilities.read_face_database(self.database.faces)

                if len(faces_database) != 0 and not self.comparison and self.matcher is None:
                    self.comparison = True

                    # comparar rostros
                    self.matcher, user_id = self.face_utilities.face_matching(face_crop, faces_database, names_database)

                    self.face_utilities.show_state_login(face_image, state=self.matcher)

                    if self.matcher:
                        # guardar registro en SQLite
                        try:
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()

                            # insertar el registro de acceso
                            cursor.execute("INSERT INTO access_logs (user_id) VALUES (?)", (user_id,))

                            cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
                            real_name_row = cursor.fetchone()
                            real_name = real_name_row[0] if real_name_row else "Desconocido"

                            conn.commit()
                            conn.close()

                            print(f"[ACCESO CONCEDIDO] Usuario: {real_name} (ID: {user_id})")

                        except Exception as e:
                            print(f"Error registrando el log en la base de datos: {e}")

                        return face_image, self.matcher, 'Approved user access!'
                    else:
                        return face_image, self.matcher, 'User no approved'
                else:
                    return face_image, self.matcher, 'Empty database'
            else:
                return face_image, self.matcher, 'wait frames'
        else:
            return face_image, self.matcher, 'No center face'