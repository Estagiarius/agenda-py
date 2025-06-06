from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette

from src.core.models import Event, Entity, ClassRegistry, AttendanceRecord
from src.core.database_manager import DatabaseManager
from datetime import date, datetime # Added datetime for save_class_registry in dummy
from typing import Optional, Dict, List

class StudentAttendanceRow(QWidget):
    """Widget for a single student's attendance controls."""
    status_changed = pyqtSignal(int, str) # student_id, status

    def __init__(self, student: Entity, initial_status: str = "Presente", parent=None):
        super().__init__(parent)
        self.student = student
        self.current_status = initial_status

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2) # Compact layout

        self.name_label = QLabel(student.name)
        self.name_label.setMinimumWidth(150) # Ensure name is visible
        layout.addWidget(self.name_label)

        layout.addStretch() # Pushes buttons to the right

        self.buttons: Dict[str, QPushButton] = {}
        statuses = {"Presente": "P", "Ausente": "A", "Atrasado": "T"}

        for status_key, status_char in statuses.items():
            btn = QPushButton(status_char)
            btn.setCheckable(True)
            btn.setFixedSize(30, 30) # Small, square buttons
            btn.setProperty("status_key", status_key) # Store status key on button
            btn.clicked.connect(self._on_button_clicked)
            self.buttons[status_key] = btn
            layout.addWidget(btn)

        self.update_button_states()

    def _on_button_clicked(self):
        sender_button = self.sender()
        new_status = sender_button.property("status_key")

        if self.current_status == new_status and sender_button.isChecked(): # Clicking an already active button (should not happen if logic is correct)
            # This case might mean user is trying to uncheck, but we want one always active
            # For now, just ensure it stays checked and others are unchecked
            pass
        elif self.current_status == new_status and not sender_button.isChecked():
             # User tried to uncheck the active button. Re-check it.
             sender_button.setChecked(True)
             return


        self.current_status = new_status
        self.update_button_states()
        self.status_changed.emit(self.student.id, self.current_status)

    def update_button_states(self):
        for status_key, btn in self.buttons.items():
            is_active = (status_key == self.current_status)
            btn.setChecked(is_active)

            # Basic styling for active/inactive
            # palette = btn.palette()
            # if is_active:
            #     palette.setColor(QPalette.ColorRole.Button, QColor("#a0d0a0" if status_key == "Presente" else "#d0a0a0")) # Greenish for P, Reddish for A/T
            # else:
            #     palette.setColor(QPalette.ColorRole.Button, QColor("#e0e0e0")) # Default
            # btn.setPalette(palette)
            # btn.setAutoFillBackground(True) # Important for palette changes to show

            # Simpler styling for now:
            if is_active:
                if status_key == "Presente":
                    btn.setStyleSheet("background-color: #c8e6c9; border: 1px solid #81c784;") # Light Green
                elif status_key == "Ausente":
                    btn.setStyleSheet("background-color: #ffcdd2; border: 1px solid #e57373;") # Light Red
                else: # Atrasado
                    btn.setStyleSheet("background-color: #fff9c4; border: 1px solid #ffd54f;") # Light Yellow
            else:
                btn.setStyleSheet("") # Revert to default stylesheet

    def set_status(self, status: str):
        if status in self.buttons:
            self.current_status = status
            self.update_button_states()
            # No emit here, this is for programmatic setting

class ClassRegistryView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_event: Optional[Event] = None
        self.current_date: Optional[date] = None
        self.loaded_attendance_records: Dict[int, str] = {} # student_id: status
        self.student_widgets: Dict[int, StudentAttendanceRow] = {} # student_id: StudentAttendanceRow widget
        self.is_dirty = False

        self.setObjectName("ClassRegistryView")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15,15,15,15)

        # --- Header Section ---
        header_layout = QHBoxLayout()
        self.class_title_label = QLabel("Nenhuma aula selecionada")
        self.class_title_label.setObjectName("ClassRegistryTitleLabel")
        self.class_title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.class_title_label)
        header_layout.addStretch()
        # Placeholder for potential 'Voltar' button or other actions
        main_layout.addLayout(header_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # --- Main Content Split (Attendance | Content) ---
        content_splitter_layout = QHBoxLayout()

        # --- Attendance Section ---
        attendance_section_widget = QWidget()
        attendance_layout = QVBoxLayout(attendance_section_widget)
        attendance_layout.setContentsMargins(0,0,10,0) # Add right margin for separation

        attendance_title_label = QLabel("Registro de Frequência")
        attendance_title_label.setStyleSheet("font-size: 16px; margin-bottom: 5px;")
        attendance_layout.addWidget(attendance_title_label)

        self.mark_all_present_button = QPushButton("Marcar Todos como Presentes")
        self.mark_all_present_button.clicked.connect(self.on_mark_all_present_button_clicked)
        attendance_layout.addWidget(self.mark_all_present_button)

        self.students_scroll_area = QScrollArea()
        self.students_scroll_area.setWidgetResizable(True)
        self.students_scroll_area.setMinimumWidth(350) # Ensure it has some width

        self.students_list_container = QWidget() # This widget will contain the student rows
        self.students_list_layout = QVBoxLayout(self.students_list_container)
        self.students_list_layout.setSpacing(3) # Compact spacing between student rows
        self.students_list_layout.addStretch() # Pushes items to the top

        self.students_scroll_area.setWidget(self.students_list_container)
        attendance_layout.addWidget(self.students_scroll_area)

        content_splitter_layout.addWidget(attendance_section_widget, 1) # Weight 1

        # --- Content Section ---
        content_section_widget = QWidget()
        content_layout = QVBoxLayout(content_section_widget)
        content_layout.setContentsMargins(10,0,0,0) # Add left margin for separation

        content_title_label = QLabel("Conteúdo Lecionado e Observações")
        content_title_label.setStyleSheet("font-size: 16px; margin-bottom: 5px;")
        content_layout.addWidget(content_title_label)

        self.content_text_edit = QTextEdit()
        self.content_text_edit.setPlaceholderText("Digite o conteúdo da aula, observações, etc.")
        content_layout.addWidget(self.content_text_edit)

        content_splitter_layout.addWidget(content_section_widget, 2) # Weight 2 (takes more space)

        main_layout.addLayout(content_splitter_layout)

        # --- Save Button and Dirty Indicator Section ---
        save_area_layout = QHBoxLayout()
        self.dirty_indicator_label = QLabel("")
        self.dirty_indicator_label.setStyleSheet("color: #e67e22; font-style: italic;") # Orange color for pending
        save_area_layout.addWidget(self.dirty_indicator_label, 0, Qt.AlignmentFlag.AlignRight)

        save_area_layout.addStretch(1) # Pushes save button to the center if indicator is on left, or use alignment on main_layout

        self.save_button = QPushButton("Salvar Registro da Aula") # Updated text
        self.save_button.setObjectName("SaveClassRegistryButton")
        self.save_button.setStyleSheet("font-size: 14px; padding: 8px; min-width: 180px;")
        self.save_button.clicked.connect(self.on_save_registry)
        save_area_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignCenter) # Centered save button

        save_area_layout.addStretch(1) # Balances the stretch, keeping button centered

        main_layout.addLayout(save_area_layout)

        self.content_text_edit.textChanged.connect(self.on_content_changed) # Connect textChanged signal

        self.setLayout(main_layout)

    def _set_dirty(self, dirty_status: bool):
        self.is_dirty = dirty_status
        if self.is_dirty:
            self.dirty_indicator_label.setText("Alterações não salvas")
        else:
            self.dirty_indicator_label.setText("") # Clear or set to "Salvo" temporarily after save

    def set_class_and_date(self, event: Event, class_date: date):
        self.current_event = event
        self.current_date = class_date
        self._set_dirty(False) # Reset dirty status when loading new class

        if self.current_event and self.current_date:
            self.class_title_label.setText(f"{self.current_event.title} - {self.current_date.strftime('%d/%m/%Y')}")
            self.load_class_registry_data() # Load content and existing attendance
            self.populate_students_list()   # Then populate students, using loaded attendance
            self._set_dirty(False) # Ensure it's clean after loading
        else:
            self.class_title_label.setText("Nenhuma aula selecionada")
            self._clear_view()

    def _clear_view(self):
        self.content_text_edit.clear()
        self.loaded_attendance_records = {}
        # Clear student list layout
        while self.students_list_layout.count() > 1: # Keep stretch item
            item = self.students_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.student_widgets = {}
        self._set_dirty(False)


    def load_class_registry_data(self):
        self.loaded_attendance_records = {} # Reset
        self.content_text_edit.clear()

        if self.current_event and self.current_event.id is not None and self.current_date:
            registry = self.db_manager.get_class_registry(self.current_event.id, self.current_date)
            if registry:
                self.content_text_edit.setHtml(registry.content_taught if registry.content_taught else "")
                for record in registry.attendance_records:
                    self.loaded_attendance_records[record['student_id']] = record['status']
            else:
                # No existing registry, so content is empty and attendance will be default
                pass
        # print(f"DEBUG: Loaded attendance for {self.current_event.title if self.current_event else 'N/A'}: {self.loaded_attendance_records}")


    def populate_students_list(self):
        # Clear previous student items
        while self.students_list_layout.count() > 1: # Keep the stretch item at the end
            item = self.students_list_layout.takeAt(0) # Remove from top
            if item.widget():
                item.widget().deleteLater()
        self.student_widgets = {}

        if self.current_event and self.current_event.id is not None:
            students: List[Entity] = self.db_manager.get_students_for_class(self.current_event.id)

            if not students:
                no_students_label = QLabel("Nenhum aluno matriculado nesta turma.")
                no_students_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.students_list_layout.insertWidget(0, no_students_label) # Insert at the top
                return

            for student in students:
                initial_status = self.loaded_attendance_records.get(student.id, "Presente")
                student_row_widget = StudentAttendanceRow(student, initial_status)
                student_row_widget.status_changed.connect(self.on_attendance_status_changed)

                # Insert rows at the top, before the stretch item
                self.students_list_layout.insertWidget(self.students_list_layout.count() -1, student_row_widget)
                self.student_widgets[student.id] = student_row_widget
        # print(f"DEBUG: Populated student list. Widgets: {len(self.student_widgets)}")


    def on_attendance_status_changed(self, student_id: int, status: str):
        # This signal is from StudentAttendanceRow
        self._set_dirty(True)
        # print(f"DEBUG: Attendance changed for student {student_id} to {status}. Dirty: {self.is_dirty}")

    def on_content_changed(self):
        self._set_dirty(True)
        # print(f"DEBUG: Content changed. Dirty: {self.is_dirty}")

    def on_mark_all_present_button_clicked(self):
        changed = False
        for student_id, student_row_widget in self.student_widgets.items():
            if student_row_widget.current_status != "Presente":
                student_row_widget.set_status("Presente") # This will trigger individual status_changed signals if connected
                changed = True
        if changed:
            self._set_dirty(True)
            # To ensure the dirty flag is set even if set_status doesn't emit due to no actual change
            # or if we disconnect the direct signal connection for mass updates.
            # For now, StudentAttendanceRow.set_status does not emit, so we manage dirty state here.
            # We also need to manually call the slot if we want its other effects.
            # However, simply setting self.is_dirty = True is the main goal here.
            # And StudentAttendanceRow.set_status will visually update the buttons.

    def on_save_registry(self):
        if not self.current_event or not self.current_date or self.current_event.id is None:
            QMessageBox.warning(self, "Erro ao Salvar", "Nenhuma aula ou data selecionada para salvar.")
            return

        # Disable button during save to prevent double clicks
        original_button_text = self.save_button.text()
        self.save_button.setText("Salvando...")
        self.save_button.setEnabled(False)

        current_attendance_data: List[AttendanceRecord] = []
        for student_id, student_widget in self.student_widgets.items():
            current_attendance_data.append(AttendanceRecord(
                student_id=student_id,
                status=student_widget.current_status, # Get current status from the row widget
                student_name=student_widget.student.name # Optional, but good to have
            ))

        content_html = self.content_text_edit.toHtml()

        # Check if a registry already exists to get its ID for update, or None for insert
        existing_registry_model = self.db_manager.get_class_registry(self.current_event.id, self.current_date)
        registry_id = existing_registry_model.id if existing_registry_model else None

        class_registry_data = ClassRegistry(
            id=registry_id,
            event_id=self.current_event.id,
            class_date=self.current_date,
            content_taught=content_html,
            attendance_records=current_attendance_data
        )

        saved_registry = self.db_manager.save_class_registry(class_registry_data)

        self.save_button.setEnabled(True) # Re-enable button

        if saved_registry and saved_registry.id is not None:
            self.loaded_attendance_records = {rec['student_id']: rec['status'] for rec in saved_registry.attendance_records}
            self._set_dirty(False) # Clear dirty state
            self.dirty_indicator_label.setText("✔️ Salvo!")
            self.save_button.setText("Salvo!")
            QTimer.singleShot(2500, lambda: self.save_button.setText(original_button_text))
            QTimer.singleShot(2500, lambda: self.dirty_indicator_label.setText("")) # Clear "✔️ Salvo!"
            # print(f"Registro de classe salvo com sucesso! ID: {saved_registry.id}")
        else:
            self.save_button.setText(original_button_text) # Restore original text on failure
            QMessageBox.critical(self, "Erro ao Salvar", "Não foi possível salvar o registro da aula. Verifique os logs para mais detalhes.")
            # print("Erro ao salvar registro de classe.")

    def refresh_view(self):
        """Public method to reload data if event/date context is already set."""
        # print(f"DEBUG: ClassRegistryView.refresh_view() called for event: {self.current_event.id if self.current_event else 'None'}, date: {self.current_date}")
        if self.current_event and self.current_date:
            # Re-set to trigger full reload and repopulate
            self.set_class_and_date(self.current_event, self.current_date)
        else:
            self._clear_view()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    class DummyDBManager:
        def get_students_for_class(self, event_id):
            print(f"DummyDBManager: get_students_for_class for event_id {event_id}")
            return [
                Entity(id=1, name="João Silva", type="student"),
                Entity(id=2, name="Maria Oliveira", type="student"),
                Entity(id=3, name="Pedro Costa", type="student"),
            ]

        def get_class_registry(self, event_id, class_date):
            print(f"DummyDBManager: get_class_registry for event {event_id} on {class_date}")
            # Simulate an existing registry for one student
            if event_id == 101 and class_date == date(2023, 10, 26): # Example
                return ClassRegistry(
                    id=1, event_id=101, class_date=class_date,
                    content_taught="Revisão de Frações.",
                    attendance_records=[
                        AttendanceRecord(student_id=1, status="Presente", student_name="João Silva"),
                        AttendanceRecord(student_id=2, status="Ausente", student_name="Maria Oliveira"),
                        # Pedro will default to Presente
                    ]
                )
            return None

        def save_class_registry(self, registry: ClassRegistry):
            print(f"DummyDBManager: save_class_registry called with: {registry.__dict__}")
            registry.id = registry.id or 123 # Simulate setting an ID
            registry.created_at = registry.created_at or datetime.now()
            registry.updated_at = datetime.now()
            return registry


    app = QApplication(sys.argv)
    db_man = DummyDBManager()

    # Example Event and Date
    sample_event = Event(id=101, title="Matemática 101", event_type="aula", start_time=datetime(2023,10,26,10,0,0))
    sample_date = date(2023, 10, 26)

    # Test when no class is set
    # window_no_class = ClassRegistryView(db_man)
    # window_no_class.setWindowTitle("Teste ClassRegistryView - Sem Aula")
    # window_no_class.setGeometry(100, 100, 700, 500)
    # window_no_class.show()

    # Test with a class set
    window_with_class = ClassRegistryView(db_man)
    window_with_class.set_class_and_date(sample_event, sample_date)
    window_with_class.setWindowTitle("Teste ClassRegistryView - Matemática 101")
    window_with_class.setGeometry(150, 150, 800, 600) # Increased size for better layout
    window_with_class.show()

    sys.exit(app.exec())
