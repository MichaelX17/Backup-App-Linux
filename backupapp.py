import os
import zipfile
import locale
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QCheckBox,
    QProgressBar, QMessageBox, QLabel, QHBoxLayout, QStyle
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


# --- Clase para manejar los textos en diferentes idiomas ---
class Translator:
    def __init__(self):
        self.lang = self.detect_language()
        self.translations = {
            'es': {
                'window_title': '🗃️ Linux BackupApp',
                'folder_label': '📁 Carpeta origen: (no seleccionada)',
                'select_folder_button': 'Seleccionar carpeta origen',
                'select_all_button': 'Seleccionar todo',
                'deselect_all_button': 'Deseleccionar todo',
                'backup_button': 'Generar Backup ZIP',
                'status_ready': 'Listo',
                'status_counting': 'Contando archivos...',
                'status_creating': 'Creando backup...',
                'status_completed': '✅ Backup completado',
                'status_error': '❌ Error en el backup',
                'error_no_folder': 'Primero selecciona una carpeta.',
                'error_no_files': 'Selecciona al menos un archivo.',
                'success_title': 'Éxito',
                'success_message': '✅ Backup creado correctamente.',
                'error_title': 'Error',
                'select_folder_dialog': 'Seleccionar carpeta origen',
                'save_backup_dialog': 'Guardar backup como',
                'zip_files': 'Archivo ZIP (*.zip)'
            },
            'en': {
                'window_title': '🗃️ Linux BackupApp',
                'folder_label': '📁 Source folder: (not selected)',
                'select_folder_button': 'Select source folder',
                'select_all_button': 'Select all',
                'deselect_all_button': 'Deselect all',
                'backup_button': 'Generate ZIP Backup',
                'status_ready': 'Ready',
                'status_counting': 'Counting files...',
                'status_creating': 'Creating backup...',
                'status_completed': '✅ Backup completed',
                'status_error': '❌ Backup error',
                'error_no_folder': 'First select a folder.',
                'error_no_files': 'Select at least one file.',
                'success_title': 'Success',
                'success_message': '✅ Backup created successfully.',
                'error_title': 'Error',
                'select_folder_dialog': 'Select source folder',
                'save_backup_dialog': 'Save backup as',
                'zip_files': 'ZIP File (*.zip)'
            }
        }

    def detect_language(self):
        # Detectar el idioma del sistema
        system_lang, _ = locale.getdefaultlocale()
        if system_lang and system_lang.startswith('es'):
            return 'es'
        else:
            return 'en'

    def get_text(self, key):
        # Obtener el texto en el idioma actual
        return self.translations[self.lang].get(key, key)


# --- Hilo para crear el backup sin congelar la interfaz ---
class BackupThread(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, folder, files, dest_zip):
        super().__init__()
        self.folder = folder
        self.files = files
        self.dest_zip = dest_zip
        self.total_files = 0
        self.processed_files = 0

    def count_total_files(self):
        """Cuenta el número total de archivos a comprimir (incluyendo subdirectorios)"""
        total = 0
        for filename in self.files:
            filepath = os.path.join(self.folder, filename)
            if os.path.isfile(filepath):
                total += 1
            elif os.path.isdir(filepath):
                for root, dirs, files in os.walk(filepath):
                    total += len(files)
        return total

    def add_directory_to_zip(self, z, directory, arcname):
        """Añade un directorio completo al ZIP recursivamente con progreso en tiempo real"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Calcular el nombre relativo para mantener la estructura CORRECTA
                parent_dir = os.path.dirname(directory)
                if parent_dir == self.folder:
                    relative_path = os.path.relpath(file_path, self.folder)
                else:
                    relative_path = os.path.relpath(file_path, parent_dir)
                    relative_path = os.path.join(arcname, relative_path)
                
                z.write(file_path, relative_path)
                
                # Actualizar progreso después de cada archivo
                self.processed_files += 1
                progress_percent = int((self.processed_files / self.total_files) * 100)
                self.progress.emit(progress_percent)

    def run(self):
        try:
            # Contar el total de archivos ANTES de empezar
            self.total_files = self.count_total_files()
            self.processed_files = 0
            
            if self.total_files == 0:
                self.progress.emit(100)
                self.done.emit(True)
                return
            
            with zipfile.ZipFile(self.dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
                for filename in self.files:
                    filepath = os.path.join(self.folder, filename)
                    
                    if os.path.isfile(filepath):
                        # Es un archivo normal - añadirlo directamente
                        z.write(filepath, arcname=filename)
                        self.processed_files += 1
                        progress_percent = int((self.processed_files / self.total_files) * 100)
                        self.progress.emit(progress_percent)
                        
                    elif os.path.isdir(filepath):
                        # Es un directorio - añadirlo recursivamente
                        self.add_directory_to_zip(z, filepath, filename)
                    
            self.done.emit(True)
        except Exception as e:
            error_msg = f"Error al crear el backup: {str(e)}"
            self.error.emit(error_msg)
            self.done.emit(False)


# --- Ventana principal ---
class BackupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.translator.get_text('window_title'))
        self.setGeometry(300, 200, 600, 600)

        # Layout principal
        layout = QVBoxLayout()

        # Widgets principales
        self.label_folder = QLabel(self.translator.get_text('folder_label'))
        self.file_list = QListWidget()
        self.btn_select_folder = QPushButton(self.translator.get_text('select_folder_button'))
        self.btn_select_all = QPushButton(self.translator.get_text('select_all_button'))
        self.btn_deselect_all = QPushButton(self.translator.get_text('deselect_all_button'))
        self.btn_backup = QPushButton(self.translator.get_text('backup_button'))
        self.progress = QProgressBar()
        self.status_label = QLabel(self.translator.get_text('status_ready'))

        # Layouts secundarios
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_select_all)
        btn_row.addWidget(self.btn_deselect_all)

        layout.addWidget(self.label_folder)
        layout.addWidget(self.file_list)
        layout.addLayout(btn_row)
        layout.addWidget(self.btn_select_folder)
        layout.addWidget(self.btn_backup)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Conexiones
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        self.btn_backup.clicked.connect(self.create_backup)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translator.get_text('select_folder_dialog'))
        if folder:
            self.folder = folder
            self.label_folder.setText(f"📁 {self.translator.get_text('folder_label').split(':')[0]}: {folder}")
            self.file_list.clear()
            
            # Separar archivos y directorios
            items = os.listdir(folder)
            directories = []
            files = []
            
            for item in items:
                item_path = os.path.join(folder, item)
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
            
            # Ordenar alfabéticamente cada lista
            directories.sort()
            files.sort()
            
            # Obtener iconos del sistema
            folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            file_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            
            # Añadir directorios primero con icono de carpeta
            for directory in directories:
                item = QListWidgetItem(f" {directory}")
                item.setIcon(folder_icon)
                item.setData(Qt.ItemDataRole.UserRole, directory)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.file_list.addItem(item)
            
            # Añadir archivos después con icono de archivo
            for file in files:
                item = QListWidgetItem(f" {file}")
                item.setIcon(file_icon)
                item.setData(Qt.ItemDataRole.UserRole, file)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.file_list.addItem(item)

    def select_all(self):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def create_backup(self):
        if not hasattr(self, "folder"):
            QMessageBox.warning(self, self.translator.get_text('error_title'), self.translator.get_text('error_no_folder'))
            return

        selected_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                original_name = item.data(Qt.ItemDataRole.UserRole)
                selected_files.append(original_name)

        if not selected_files:
            QMessageBox.warning(self, self.translator.get_text('error_title'), self.translator.get_text('error_no_files'))
            return

        dest_zip, _ = QFileDialog.getSaveFileName(
            self, self.translator.get_text('save_backup_dialog'), "", self.translator.get_text('zip_files')
        )
        if not dest_zip:
            return

        if not dest_zip.lower().endswith('.zip'):
            dest_zip += '.zip'

        # Actualizar estado
        self.status_label.setText(self.translator.get_text('status_counting'))
        QApplication.processEvents()  # Forzar actualización de la UI

        # Iniciar backup en hilo aparte
        self.thread = BackupThread(self.folder, selected_files, dest_zip)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.done.connect(self.backup_finished)
        self.thread.error.connect(self.show_error)
        self.progress.setValue(0)
        self.btn_backup.setEnabled(False)
        self.status_label.setText(self.translator.get_text('status_creating'))
        self.thread.start()

    def backup_finished(self, success):
        self.btn_backup.setEnabled(True)
        if success:
            self.status_label.setText(self.translator.get_text('status_completed'))
            QMessageBox.information(self, self.translator.get_text('success_title'), self.translator.get_text('success_message'))
        else:
            self.status_label.setText(self.translator.get_text('status_error'))
        self.progress.setValue(0)

    def show_error(self, error_message):
        self.status_label.setText(self.translator.get_text('status_error'))
        QMessageBox.critical(self, self.translator.get_text('error_title'), error_message)


if __name__ == "__main__":
    app = QApplication([])
    window = BackupApp()
    window.show()
    app.exec()