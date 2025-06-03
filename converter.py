#!/usr/bin/env python3
"""
Data Format Converter with GUI
Konwerter formatów danych z interfejsem graficznym
Obsługuje XML, JSON i YAML z asynchroniczną obsługą plików
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

import yaml
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QFileDialog, QTextEdit,
                             QProgressBar, QMessageBox, QGroupBox, QComboBox)


class ConversionWorker(QThread):
    """Worker thread dla asynchronicznej konwersji plików"""

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.converter = DataConverter()

    def run(self):
        try:
            self.log.emit(f"Rozpoczynam konwersję: {self.input_path}")
            self.progress.emit(10)

            # Symulacja czasu ładowania
            time.sleep(0.5)
            self.progress.emit(30)

            # Wykonanie konwersji
            self.converter.convert_file(self.input_path, self.output_path)
            self.progress.emit(80)

            time.sleep(0.3)
            self.progress.emit(100)

            self.log.emit(f"Konwersja zakończona: {self.output_path}")
            self.finished.emit(f"Konwersja zakończona pomyślnie!\nPlik zapisano jako: {self.output_path}")

        except Exception as e:
            self.error.emit(f"Błąד podczas konwersji: {str(e)}")


class DataConverter:
    """Klasa do konwersji między formatami XML, JSON i YAML"""

    def __init__(self):
        self.supported_formats = ['.xml', '.json', '.yml', '.yaml']

    def validate_file_format(self, file_path):
        extension = Path(file_path).suffix.lower()
        if extension not in self.supported_formats:
            raise ValueError(f"Nieobsługiwany format pliku: {extension}")
        return extension

    @staticmethod
    def read_json(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod
    def write_json(data, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def read_yaml(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def write_yaml(self, data, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True, indent=2)

    def dict_to_xml(self, data, root_name='root'):
        def build_xml(parent, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            elem = ET.SubElement(parent, key)
                            build_xml(elem, item)
                    else:
                        elem = ET.SubElement(parent, key)
                        build_xml(elem, value)
            elif isinstance(data, list):
                for item in data:
                    elem = ET.SubElement(parent, 'item')
                    build_xml(elem, item)
            else:
                parent.text = str(data) if data is not None else ''

        root = ET.Element(root_name)
        build_xml(root, data)
        return root

    def xml_to_dict(self, element):
        result = {}

        if element.attrib:
            result['@attributes'] = element.attrib

        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['#text'] = element.text.strip()

        children = {}
        for child in element:
            child_data = self.xml_to_dict(child)
            if child.tag in children:
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data

        result.update(children)
        return result if result else None

    def read_xml(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        return {root.tag: self.xml_to_dict(root)}

    def write_xml(self, data, file_path):
        if isinstance(data, dict) and len(data) == 1:
            root_name = list(data.keys())[0]
            root_data = data[root_name]
        else:
            root_name = 'root'
            root_data = data

        root = self.dict_to_xml(root_data, root_name)
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ')
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(pretty_xml)

    def convert_file(self, input_path, output_path):
        global data
        input_format = self.validate_file_format(input_path)
        output_format = self.validate_file_format(output_path)

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Plik wejściowy nie istnieje: {input_path}")

        # Wczytanie danych
        if input_format == '.json':
            data = self.read_json(input_path)
        elif input_format in ['.yml', '.yaml']:
            data = self.read_yaml(input_path)
        elif input_format == '.xml':
            data = self.read_xml(input_path)

        # Zapis danych
        if output_format == '.json':
            self.write_json(data, output_path)
        elif output_format in ['.yml', '.yaml']:
            self.write_yaml(data, output_path)
        elif output_format == '.xml':
            self.write_xml(data, output_path)


class DataConverterGUI(QMainWindow):
    """Główne okno aplikacji z interfejsem graficznym"""

    def __init__(self):
        super().__init__()
        self.input_file = ""
        self.output_file = ""
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Data Format Converter v1.0")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        # Centralny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Główny layout
        main_layout = QVBoxLayout(central_widget)

        # Nagłówek
        self.create_header(main_layout)

        # Sekcja wyboru plików
        self.create_file_selection(main_layout)

        # Sekcja podglądu i logów
        self.create_preview_section(main_layout)

        # Sekcja konwersji
        self.create_conversion_section(main_layout)

        # Status bar
        self.statusBar().showMessage("Gotowy do konwersji")

    def create_header(self, layout):
        header = QLabel("Konwerter Formatów Danych")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)

    def create_file_selection(self, layout):
        file_group = QGroupBox("Wybór Plików")
        file_group.setFont(QFont("Arial", 10, QFont.Bold))
        file_layout = QVBoxLayout(file_group)

        # Plik wejściowy
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Plik wejściowy: Nie wybrano")
        self.input_label.setStyleSheet("QLabel { padding: 5px; background-color: #ecf0f1; border-radius: 5px; }")
        input_btn = QPushButton("Wybierz plik wejściowy")
        input_btn.clicked.connect(self.select_input_file)
        input_btn.setStyleSheet(self.get_button_style("#3498db"))

        input_layout.addWidget(self.input_label, 2)
        input_layout.addWidget(input_btn, 1)
        file_layout.addLayout(input_layout)

        # Format wyjściowy
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Format wyjściowy:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON (.json)", "XML (.xml)", "YAML (.yml)", "YAML (.yaml)"])
        self.format_combo.setStyleSheet("QComboBox { padding: 5px; }")
        output_layout.addWidget(self.format_combo, 1)

        output_btn = QPushButton("Wybierz lokalizację zapisu")
        output_btn.clicked.connect(self.select_output_file)
        output_btn.setStyleSheet(self.get_button_style("#27ae60"))
        output_layout.addWidget(output_btn, 1)

        file_layout.addLayout(output_layout)

        self.output_label = QLabel("Plik wyjściowy: Nie wybrano")
        self.output_label.setStyleSheet("QLabel { padding: 5px; background-color: #ecf0f1; border-radius: 5px; }")
        file_layout.addWidget(self.output_label)

        layout.addWidget(file_group)

    def create_preview_section(self, layout):
        preview_group = QGroupBox("Podgląd i Logi")
        preview_group.setFont(QFont("Arial", 10, QFont.Bold))
        preview_layout = QVBoxLayout(preview_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Courier New';
                font-size: 10px;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.log_text.setPlaceholderText("Logi konwersji pojawią się tutaj...")

        preview_layout.addWidget(self.log_text)
        layout.addWidget(preview_group)

    def create_conversion_section(self, layout):
        conversion_group = QGroupBox("Konwersja")
        conversion_group.setFont(QFont("Arial", 10, QFont.Bold))
        conversion_layout = QVBoxLayout(conversion_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        conversion_layout.addWidget(self.progress_bar)

        # Przyciski
        button_layout = QHBoxLayout()

        self.convert_btn = QPushButton("Rozpocznij Konwersję")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.convert_btn.setMinimumHeight(40)

        self.clear_btn = QPushButton("🗑️ Wyczyść")
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        self.clear_btn.setMinimumHeight(40)

        button_layout.addWidget(self.convert_btn, 2)
        button_layout.addWidget(self.clear_btn, 1)

        conversion_layout.addLayout(button_layout)
        layout.addWidget(conversion_group)

    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """

    @staticmethod
    def darken_color(color, factor=0.9):
        # Proste przyciemnienie koloru
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik wejściowy",
            "",
            "Wszystkie obsługiwane (*.json *.xml *.yml *.yaml);;JSON (*.json);;XML (*.xml);;YAML (*.yml *.yaml)"
        )

        if file_path:
            self.input_file = file_path
            self.input_label.setText(f"Plik wejściowy: {os.path.basename(file_path)}")
            self.log_message(f"Wybrano plik wejściowy: {file_path}")
            self.update_convert_button()

    def select_output_file(self):
        format_map = {
            "JSON (.json)": "json",
            "XML (.xml)": "xml",
            "YAML (.yml)": "yml",
            "YAML (.yaml)": "yaml"
        }

        selected_format = self.format_combo.currentText()
        extension = format_map[selected_format]

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Wybierz lokalizację zapisu",
            f"converted_file.{extension}",
            f"{selected_format} (*.{extension})"
        )

        if file_path:
            self.output_file = file_path
            self.output_label.setText(f"Plik wyjściowy: {os.path.basename(file_path)}")
            self.log_message(f"Wybrano plik wyjściowy: {file_path}")
            self.update_convert_button()

    def update_convert_button(self):
        if self.input_file and self.output_file:
            self.convert_btn.setEnabled(True)
            self.convert_btn.setText("Rozpocznij Konwersję")
        else:
            self.convert_btn.setEnabled(False)
            self.convert_btn.setText("Wybierz pliki")

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.ensureCursorVisible()

    def start_conversion(self):
        if not self.input_file or not self.output_file:
            QMessageBox.warning(self, "Błąd", "Proszę wybrać pliki wejściowy i wyjściowy!")
            return

        # Wyłączenie przycisków i pokazanie progress bara
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Uruchomienie worker thread
        self.worker = ConversionWorker(self.input_file, self.output_file)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.error.connect(self.conversion_error)
        self.worker.log.connect(self.log_message)
        self.worker.start()

        self.statusBar().showMessage("Konwersja w toku...")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def conversion_finished(self, message):
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.statusBar().showMessage("Konwersja zakończona pomyślnie!")

        QMessageBox.information(self, "Sukces!", message)
        self.log_message("Konwersja zakończona pomyślnie!")

    def conversion_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.statusBar().showMessage("Błąd podczas konwersji")

        QMessageBox.critical(self, "Błąd konwersji", error_message)
        self.log_message(f"Błąd: {error_message}")

    def clear_all(self):
        self.input_file = ""
        self.output_file = ""
        self.input_label.setText("Plik wejściowy: Nie wybrano")
        self.output_label.setText("Plik wyjściowy: Nie wybrano")
        self.log_text.clear()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.update_convert_button()
        self.statusBar().showMessage("Gotowy do konwersji")
        self.log_message("Wyczyszczono wszystkie pola")


def main():
    app = QApplication(sys.argv)

    # Ustawienie stylu aplikacji
    app.setStyle('Fusion')

    # Utworzenie i wyświetlenie okna
    window = DataConverterGUI()
    window.show()

    # Uruchomienie aplikacji
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
