from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame, QCalendarWidget
from PyQt6.QtCore import Qt, QDate
from src.core.models import Event, ClassRegistry # ClassRegistry for type hint
from src.core.database_manager import DatabaseManager
from datetime import date, datetime
from typing import Tuple, Optional # For type hinting

class TodaysClassesView(QWidget):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.teacher_id = 1  # Hardcoded for now

        self.setObjectName("TodaysClassesView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.title_label = QLabel("Aulas de Hoje") # Will be updated
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setSelectedDate(QDate.currentDate())
        self.calendar_widget.setMaximumDate(QDate.currentDate().addYears(1)) # Example: Max 1 year in future
        self.calendar_widget.setMinimumDate(QDate.currentDate().addYears(-1)) # Example: Min 1 year in past
        self.calendar_widget.selectionChanged.connect(self.on_date_selected)
        # Reduce calendar height a bit if needed, or set a fixed height
        self.calendar_widget.setFixedHeight(250) # Adjust as needed
        layout.addWidget(self.calendar_widget)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        self.classes_list_widget = QListWidget()
        self.classes_list_widget.setObjectName("HistoricalClassesList")
        layout.addWidget(self.classes_list_widget)

        self.setLayout(layout)

        self.classes_list_widget.itemClicked.connect(self.on_class_selected)
        self.on_date_selected() # Initial load for today's date

    def load_classes_for_date(self, selected_date: date):
        self.classes_list_widget.clear()
        # print(f"DEBUG: Loading classes for teacher_id: {self.teacher_id} on date: {selected_date}")

        try:
            # This method returns List[Tuple[Event, Optional[ClassRegistry]]]
            events_with_registries: List[Tuple[Event, Optional[ClassRegistry]]] = \
                self.db_manager.get_class_registries_for_date(self.teacher_id, selected_date)

            if not events_with_registries:
                no_classes_item = QListWidgetItem(f"Nenhuma aula para {selected_date.strftime('%d/%m/%Y')}.")
                no_classes_item.setFlags(no_classes_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.classes_list_widget.addItem(no_classes_item)
                return

            for event, registry_status in events_with_registries:
                turma_info = "Turma X" # Placeholder
                if event.description and "Turma:" in event.description:
                    try:
                        turma_info = event.description.split("Turma:")[1].split(",")[0].strip()
                    except IndexError: pass

                status_text = "Registrado" if registry_status else "Não Registrado"
                display_text = f"{event.title} - {turma_info} ({event.start_time.strftime('%H:%M') if event.start_time else 'N/A'}) - {status_text}"

                list_item = QListWidgetItem(display_text)
                # Store both event and the specific date for which the registry is relevant
                list_item.setData(Qt.ItemDataRole.UserRole, (event, selected_date))
                self.classes_list_widget.addItem(list_item)

        except Exception as e:
            print(f"Erro ao carregar aulas para data {selected_date}: {e}")
            error_item = QListWidgetItem(f"Erro ao carregar aulas para {selected_date.strftime('%d/%m/%Y')}.")
            error_item.setForeground(Qt.GlobalColor.red) # Assuming Qt is imported from PyQt6.QtGui
            self.classes_list_widget.addItem(error_item)

    def on_date_selected(self):
        pyqt_selected_date = self.calendar_widget.selectedDate()
        selected_date = pyqt_selected_date.toPyDate() # Convert QDate to datetime.date

        if selected_date == date.today():
            self.title_label.setText("Minhas Aulas de Hoje")
        else:
            self.title_label.setText(f"Aulas de {selected_date.strftime('%d/%m/%Y')}")

        self.load_classes_for_date(selected_date)

    def on_class_selected(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and isinstance(data, tuple) and len(data) == 2:
            event, class_date_for_registry = data
            if isinstance(event, Event) and isinstance(class_date_for_registry, date):
                main_win = self.window()
                if main_win and hasattr(main_win, 'show_class_registry_view'):
                    # print(f"DEBUG: Requesting ClassRegistryView for Event ID: {event.id}, Date: {class_date_for_registry}")
                    main_win.show_class_registry_view(event, class_date_for_registry)
                else:
                    print("ERRO: Não foi possível encontrar a MainWindow ou o método show_class_registry_view.")
            else:
                 print(f"ERRO: Dados do item da lista em formato inesperado: {data}")
        else:
            # Handles "Nenhuma aula..." or error items
            pass

    def refresh_view(self):
        """Public method to reload classes for the currently selected calendar date."""
        # print("DEBUG: TodaysClassesView.refresh_view() called")
        self.on_date_selected() # Re-trigger load based on current calendar selection

if __name__ == '__main__':
    # This part is for testing the TodaysClassesView independently.
    # It requires a running QApplication and a DatabaseManager instance.
    # You'd typically run the main application (main.py) instead.
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QColor # For error item
    import sys

    # Dummy DatabaseManager for standalone testing
    class DummyDBManager:
        def get_class_registries_for_date(self, teacher_id, selected_date):
            print(f"DummyDBManager: get_class_registries_for_date for teacher {teacher_id} on {selected_date}")
            # Simulate some events based on date
            events = []
            if selected_date == date.today():
                evt1_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
                evt2_time = datetime.now().replace(hour=14, minute=30, second=0, microsecond=0)
                events.append( (Event(id=101, title="Matemática Hoje", start_time=evt1_time, event_type="aula", description="Turma: 3A"), None) )
                events.append( (Event(id=102, title="Física Hoje", start_time=evt2_time, event_type="aula", description="Turma: Exp"), ClassRegistry(id=1,event_id=102,class_date=selected_date,attendance_records=[],content_taught="Algo")) )
            elif selected_date == date.today().replace(day=date.today().day -1): # Yesterday
                evt3_time = datetime.now().replace(day=date.today().day -1, hour=10, minute=0, second=0, microsecond=0)
                events.append( (Event(id=103, title="História Ontem", start_time=evt3_time, event_type="aula", description="Turma: H1"), ClassRegistry(id=2,event_id=103,class_date=selected_date,attendance_records=[],content_taught="")) )
            return events

    app = QApplication(sys.argv)
    db_man = DummyDBManager()

    main_view = TodaysClassesView(db_man)
    main_view.setWindowTitle("Teste de Visão de Aulas (Histórico)")
    main_view.setGeometry(100, 100, 450, 550) # Adjusted size for calendar
    main_view.show()

    sys.exit(app.exec())
