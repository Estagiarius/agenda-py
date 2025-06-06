import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QLineEdit,
    QComboBox, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, List, Dict

from src.core.database_manager import DatabaseManager
from src.core.models import LessonPlan, Entity # Assuming Entity is used for classes/turmas
from datetime import datetime # For formatting dates
from PyQt6.QtWidgets import QDialog # Added for type hinting if needed, and good practice
from src.ui.lesson_plan_dialog import LessonPlanDialog

class LessonPlansView(QWidget):
    def __init__(self, db_manager: DatabaseManager, teacher_id: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_teacher_id = teacher_id
        self.all_teacher_classes: List[Entity] = [] # To store class entities for the filter

        self.setWindowTitle("Meus Planos de Aula") # Although this might be set by how it's integrated
        self.setObjectName("LessonPlansView")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Filtros ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Turma:"))
        self.class_filter_combo = QComboBox()
        self.class_filter_combo.setPlaceholderText("Todas as Turmas")
        filter_layout.addWidget(self.class_filter_combo)

        filter_layout.addWidget(QLabel("Buscar por Título:"))
        self.title_search_edit = QLineEdit()
        self.title_search_edit.setPlaceholderText("Palavra-chave no título...")
        filter_layout.addWidget(self.title_search_edit)

        self.apply_filter_button = QPushButton("Buscar/Atualizar")
        self.apply_filter_button.clicked.connect(self._load_lesson_plans)
        filter_layout.addWidget(self.apply_filter_button)
        self.title_search_edit.returnPressed.connect(self._load_lesson_plans) # Also search on Enter
        main_layout.addLayout(filter_layout)

        # --- Tabela de Planos de Aula ---
        self.lesson_plans_table = QTableWidget()
        self.lesson_plans_table.setColumnCount(4) # ID (oculto), Título, Data, Turmas
        self.lesson_plans_table.setHorizontalHeaderLabels(["ID", "Título", "Data da Aula", "Turmas Associadas"])
        self.lesson_plans_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lesson_plans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lesson_plans_table.verticalHeader().setVisible(False)
        self.lesson_plans_table.setColumnHidden(0, True) # Ocultar coluna ID
        header = self.lesson_plans_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.lesson_plans_table)

        # --- Botões de Ação ---
        action_buttons_layout = QHBoxLayout()
        self.create_button = QPushButton("Criar Novo Plano")
        self.create_button.clicked.connect(self._handle_create_lesson_plan)
        action_buttons_layout.addWidget(self.create_button)

        self.edit_button = QPushButton("Ver/Editar Selecionado")
        self.edit_button.clicked.connect(self._handle_edit_lesson_plan)
        action_buttons_layout.addWidget(self.edit_button)

        self.duplicate_button = QPushButton("Duplicar Selecionado")
        self.duplicate_button.clicked.connect(self._handle_duplicate_lesson_plan)
        action_buttons_layout.addWidget(self.duplicate_button)

        self.delete_button = QPushButton("Excluir Selecionado")
        self.delete_button.clicked.connect(self._handle_delete_lesson_plan)
        self.delete_button.setStyleSheet("background-color: #FFC0CB;") # Rosa claro para destaque
        action_buttons_layout.addWidget(self.delete_button)
        main_layout.addLayout(action_buttons_layout)

        self.setLayout(main_layout)

        # Initial data loading
        self._refresh_class_filter()
        self._load_lesson_plans()

    def _refresh_class_filter(self):
        """Populates the class filter combo box."""
        self.class_filter_combo.clear()
        self.all_teacher_classes.clear() # Clear previous cache

        try:
            # For now, get_all_entities of type 'turma'.
            # In a real app, this might be filtered by teacher or school context.
            classes = self.db_manager.get_all_entities(entity_type="turma")
            self.all_teacher_classes = classes if classes else []
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Turmas",
                                 f"Não foi possível carregar a lista de turmas: {e}")
            self.all_teacher_classes = [] # Ensure it's empty on error

        self.class_filter_combo.addItem("Todas as Turmas", None) # UserData is None for 'All'
        for class_entity in self.all_teacher_classes:
            if class_entity.id is not None: # Should always have an ID from DB
                self.class_filter_combo.addItem(class_entity.name, class_entity.id)

        # Optionally, connect currentIndexChanged to _load_lesson_plans if desired
        # self.class_filter_combo.currentIndexChanged.connect(self._load_lesson_plans)


    def _load_lesson_plans(self):
        """Loads lesson plans based on current filter criteria and populates the table."""
        self.lesson_plans_table.setRowCount(0) # Clear existing rows

        selected_class_id = self.class_filter_combo.currentData() # Returns userData
        title_keyword = self.title_search_edit.text().strip()
        if not title_keyword:
            title_keyword = None # Pass None if empty

        try:
            plans = self.db_manager.get_lesson_plans_by_teacher(
                teacher_id=self.current_teacher_id,
                associated_class_id=selected_class_id,
                title_keyword=title_keyword
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Planos",
                                 f"Não foi possível carregar os planos de aula: {e}")
            return

        if not plans:
            # Optionally, display a message in the table or a label
            # print("Nenhum plano de aula encontrado com os filtros atuais.")
            return

        # Cache class names to avoid repeated DB calls if get_entity_by_id is slow
        # self.all_teacher_classes should be populated by _refresh_class_filter
        class_names_cache: Dict[int, str] = {cls.id: cls.name for cls in self.all_teacher_classes if cls.id is not None}

        for plan in plans:
            if plan.id is None: continue # Should not happen for plans from DB

            row_position = self.lesson_plans_table.rowCount()
            self.lesson_plans_table.insertRow(row_position)

            # Column 0: ID (hidden)
            id_item = QTableWidgetItem(str(plan.id))
            self.lesson_plans_table.setItem(row_position, 0, id_item)

            # Column 1: Title
            title_item = QTableWidgetItem(plan.title)
            self.lesson_plans_table.setItem(row_position, 1, title_item)

            # Column 2: Lesson Date
            date_str = ""
            if plan.lesson_date:
                try:
                    # Ensure plan.lesson_date is a datetime object
                    if isinstance(plan.lesson_date, datetime):
                        date_str = plan.lesson_date.strftime("%d/%m/%Y")
                    elif isinstance(plan.lesson_date, str): # Should be datetime from db_manager
                        # Attempt to parse if it's a string (fallback, ideally db_manager handles this)
                        dt_obj = datetime.fromisoformat(plan.lesson_date)
                        date_str = dt_obj.strftime("%d/%m/%Y")
                    else:
                        date_str = str(plan.lesson_date) # Fallback
                except ValueError:
                    date_str = str(plan.lesson_date) # If parsing fails
            date_item = QTableWidgetItem(date_str)
            self.lesson_plans_table.setItem(row_position, 2, date_item)

            # Column 3: Associated Classes
            class_names = []
            if plan.class_ids:
                for class_id in plan.class_ids:
                    name = class_names_cache.get(class_id)
                    if name is None: # Not in cache, try DB (should ideally be pre-cached)
                        class_entity = self.db_manager.get_entity_by_id(class_id)
                        name = class_entity.name if class_entity else f"ID {class_id}?"
                        if class_entity and class_entity.id is not None: # Add to cache if found
                           class_names_cache[class_entity.id] = name
                    class_names.append(name)

            classes_item = QTableWidgetItem(", ".join(class_names) if class_names else "N/A")
            self.lesson_plans_table.setItem(row_position, 3, classes_item)

    def _get_selected_lesson_plan_id(self) -> Optional[int]:
        """Returns the ID of the currently selected lesson plan in the table."""
        selected_rows = self.lesson_plans_table.selectionModel().selectedRows()
        if selected_rows:
            # Assuming single row selection or taking the first selected row
            first_selected_row_index = selected_rows[0].row()
            id_item = self.lesson_plans_table.item(first_selected_row_index, 0) # Column 0 is ID
            if id_item and id_item.text().isdigit():
                return int(id_item.text())
        return None

    def _handle_create_lesson_plan(self):
        """Handles the creation of a new lesson plan."""
        dialog = LessonPlanDialog(db_manager=self.db_manager,
                                  teacher_id=self.current_teacher_id,
                                  parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            plan_to_save = dialog.lesson_plan_to_save
            if plan_to_save:
                try:
                    # Ensure teacher_id is correctly set if dialog doesn't enforce it
                    plan_to_save.teacher_id = self.current_teacher_id

                    saved_plan = self.db_manager.add_lesson_plan(plan_to_save)
                    if saved_plan and saved_plan.id is not None:
                        QMessageBox.information(self, "Sucesso",
                                                f"Plano de aula '{saved_plan.title}' criado com sucesso.")
                        self._load_lesson_plans() # Refresh table
                    else:
                        QMessageBox.warning(self, "Falha na Criação",
                                            "Não foi possível criar o plano de aula no banco de dados.")
                except Exception as e:
                    QMessageBox.critical(self, "Erro no Banco de Dados",
                                         f"Ocorreu um erro ao salvar o plano de aula: {e}")
            else:
                # This case should ideally not be reached if dialog.accept() is only called with valid data
                QMessageBox.warning(self, "Dados Inválidos",
                                    "Os dados do plano de aula não foram coletados corretamente.")

    def _handle_edit_lesson_plan(self):
        """Handles viewing/editing of an existing selected lesson plan."""
        selected_plan_id = self._get_selected_lesson_plan_id()
        if selected_plan_id is None:
            QMessageBox.information(self, "Nenhuma Seleção",
                                    "Por favor, selecione um plano de aula para ver ou editar.")
            return

        try:
            # Fetch with teacher_id to ensure user owns the plan
            fetched_plan = self.db_manager.get_lesson_plan_by_id(
                lesson_plan_id=selected_plan_id,
                teacher_id=self.current_teacher_id
            )
            if fetched_plan is None:
                QMessageBox.warning(self, "Plano Não Encontrado",
                                    "O plano de aula selecionado não foi encontrado ou você não tem permissão para editá-lo.")
                self._load_lesson_plans() # Refresh in case it was deleted by another process
                return
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Plano",
                                 f"Não foi possível carregar o plano de aula para edição: {e}")
            return

        dialog = LessonPlanDialog(db_manager=self.db_manager,
                                  lesson_plan=fetched_plan,
                                  teacher_id=self.current_teacher_id, # Pass for consistency, though fetched_plan has it
                                  parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            plan_to_update = dialog.lesson_plan_to_save
            if plan_to_update and plan_to_update.id is not None: # Must have an ID to update
                 # Ensure teacher_id from the dialog matches current_teacher_id for security
                if plan_to_update.teacher_id != self.current_teacher_id:
                    QMessageBox.critical(self, "Erro de Permissão", "Tentativa de alterar o ID do professor do plano de aula.")
                    return

                try:
                    success = self.db_manager.update_lesson_plan(plan_to_update)
                    if success:
                        QMessageBox.information(self, "Sucesso",
                                                f"Plano de aula '{plan_to_update.title}' atualizado com sucesso.")
                        self._load_lesson_plans() # Refresh table
                    else:
                        QMessageBox.warning(self, "Falha na Atualização",
                                            "Não foi possível atualizar o plano de aula no banco de dados.")
                except Exception as e:
                    QMessageBox.critical(self, "Erro no Banco de Dados",
                                         f"Ocorreu um erro ao atualizar o plano de aula: {e}")
            else:
                QMessageBox.warning(self, "Dados Inválidos",
                                    "Os dados do plano de aula para atualização não foram coletados corretamente.")

    def _handle_duplicate_lesson_plan(self):
        """Handles duplication of the selected lesson plan."""
        selected_plan_id = self._get_selected_lesson_plan_id()
        if selected_plan_id is None:
            QMessageBox.information(self, "Nenhuma Seleção",
                                    "Por favor, selecione um plano de aula para duplicar.")
            return

        try:
            original_plan = self.db_manager.get_lesson_plan_by_id(
                lesson_plan_id=selected_plan_id,
                teacher_id=self.current_teacher_id # Ensure user owns the plan
            )
            if original_plan is None:
                QMessageBox.warning(self, "Plano Não Encontrado",
                                    "O plano de aula original não foi encontrado.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Plano",
                                 f"Não foi possível carregar o plano original para duplicação: {e}")
            return

        # Create the duplicated plan object
        duplicated_plan = LessonPlan(
            id=None, # New ID will be assigned on save
            teacher_id=original_plan.teacher_id,
            title=f"Cópia de {original_plan.title}",
            lesson_date=original_plan.lesson_date, # Or datetime.now() / None as per preference
            class_ids=list(original_plan.class_ids), # Create a new list
            objectives=original_plan.objectives,
            program_content=original_plan.program_content,
            methodology=original_plan.methodology,
            resources_text=original_plan.resources_text,
            assessment_method=original_plan.assessment_method,
            created_at=datetime.now(), # New creation time
            updated_at=datetime.now()  # New update time
        )

        # Duplicate files: Create new LessonPlanFile objects without IDs
        if original_plan.files:
            for orig_file in original_plan.files:
                new_file = LessonPlanFile(
                    lesson_plan_id=0, # Placeholder, will be set by add_lesson_plan
                    file_name=orig_file.file_name,
                    file_path=orig_file.file_path,
                    # uploaded_at can be now, or copied if relevant, or keep model default
                    uploaded_at=datetime.now()
                )
                duplicated_plan.files.append(new_file)

        # Duplicate links: Create new LessonPlanLink objects without IDs
        if original_plan.links:
            for orig_link in original_plan.links:
                new_link = LessonPlanLink(
                    lesson_plan_id=0, # Placeholder
                    url=orig_link.url,
                    title=orig_link.title,
                    # added_at can be now, or copied, or keep model default
                    added_at=datetime.now()
                )
                duplicated_plan.links.append(new_link)

        # Open dialog with the duplicated plan
        dialog = LessonPlanDialog(db_manager=self.db_manager,
                                  lesson_plan=duplicated_plan, # Pass as if editing, but it has no ID
                                  teacher_id=self.current_teacher_id,
                                  parent=self)
        dialog.setWindowTitle(f"Editar Duplicação: {duplicated_plan.title}")


        if dialog.exec() == QDialog.DialogCode.Accepted:
            plan_to_save = dialog.lesson_plan_to_save
            if plan_to_save:
                # Ensure teacher_id is correct and ID is None for add operation
                plan_to_save.teacher_id = self.current_teacher_id
                plan_to_save.id = None

                try:
                    saved_plan = self.db_manager.add_lesson_plan(plan_to_save)
                    if saved_plan and saved_plan.id is not None:
                        QMessageBox.information(self, "Sucesso",
                                                f"Plano de aula '{saved_plan.title}' duplicado e salvo com sucesso.")
                        self._load_lesson_plans() # Refresh table
                    else:
                        QMessageBox.warning(self, "Falha na Duplicação",
                                            "Não foi possível salvar o plano de aula duplicado.")
                except Exception as e:
                     QMessageBox.critical(self, "Erro no Banco de Dados",
                                         f"Ocorreu um erro ao salvar o plano duplicado: {e}")

    def _handle_delete_lesson_plan(self):
        """Handles deletion of the selected lesson plan."""
        selected_plan_id = self._get_selected_lesson_plan_id()
        if selected_plan_id is None:
            QMessageBox.information(self, "Nenhuma Seleção",
                                    "Por favor, selecione um plano de aula para excluir.")
            return

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir o plano de aula ID {selected_plan_id}?\n"
                                     "Esta ação não pode ser desfeita.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.db_manager.delete_lesson_plan(
                    lesson_plan_id=selected_plan_id,
                    teacher_id=self.current_teacher_id # Ensures user owns the plan
                )
                if success:
                    QMessageBox.information(self, "Sucesso",
                                            "Plano de aula excluído com sucesso.")
                    self._load_lesson_plans() # Refresh table
                else:
                    QMessageBox.warning(self, "Falha na Exclusão",
                                        "Não foi possível excluir o plano de aula. "
                                        "Pode ser que já não exista ou você não tenha permissão.")
            except Exception as e:
                QMessageBox.critical(self, "Erro no Banco de Dados",
                                     f"Ocorreu um erro ao excluir o plano de aula: {e}")
