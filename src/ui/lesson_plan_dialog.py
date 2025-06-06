import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QDateTimeEdit, QPushButton, QDialogButtonBox, QMessageBox,
    QLabel, QScrollArea, QWidget as QtWidget, QCheckBox,
    QSizePolicy, QSpacerItem, QListWidget, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QDateTime, QUrl
from typing import Optional, List, Tuple, Dict
from datetime import datetime # Ensure datetime is imported

from src.core.models import LessonPlan, LessonPlanFile, LessonPlanLink, Entity
from src.core.database_manager import DatabaseManager

class LessonPlanDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager, lesson_plan: Optional[LessonPlan] = None, teacher_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.lesson_plan_to_save: Optional[LessonPlan] = None
        self.original_lesson_plan = lesson_plan

        if self.original_lesson_plan:
            self.current_teacher_id = self.original_lesson_plan.teacher_id
        elif teacher_id is not None:
            self.current_teacher_id = teacher_id
        else:
            QMessageBox.critical(self, "Erro Crítico", "ID do Professor não fornecido para novo Plano de Aula.")
            self.current_teacher_id = -1 # Invalid ID
            # Consider closing or raising an error immediately
            # self.close()
            # raise ValueError("Teacher ID is required")

        self.attached_files_map: Dict[str, LessonPlanFile] = {} # path -> LessonPlanFile object
        self.attached_links_list: List[LessonPlanLink] = []
        self.selected_class_ids: List[int] = []

        if self.original_lesson_plan and self.original_lesson_plan.id is not None:
            self.setWindowTitle(f"Editar Plano de Aula: {self.original_lesson_plan.title}")
            if self.original_lesson_plan.files:
                for f in self.original_lesson_plan.files:
                    self.attached_files_map[f.file_path] = f
            if self.original_lesson_plan.links:
                self.attached_links_list = list(self.original_lesson_plan.links)
            if self.original_lesson_plan.class_ids:
                self.selected_class_ids = list(self.original_lesson_plan.class_ids)
        else:
            self.setWindowTitle("Criar Novo Plano de Aula")

        self.setMinimumWidth(700)
        self.setMinimumHeight(750)

        main_layout = QVBoxLayout(self)

        form_basic_info = QFormLayout()
        self.title_edit = QLineEdit()
        self.lesson_date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.lesson_date_edit.setCalendarPopup(True)
        self.lesson_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_basic_info.addRow("Título*:", self.title_edit)
        form_basic_info.addRow("Data da Aula:", self.lesson_date_edit)
        main_layout.addLayout(form_basic_info)

        classes_label = QLabel("Turma(s) Associada(s):")
        main_layout.addWidget(classes_label)
        self.classes_scroll_area = QScrollArea()
        self.classes_scroll_area.setWidgetResizable(True)
        self.classes_scroll_area.setFixedHeight(100)
        self.classes_container_widget = QtWidget()
        self.classes_checkbox_layout = QVBoxLayout(self.classes_container_widget)
        self.classes_scroll_area.setWidget(self.classes_container_widget)
        main_layout.addWidget(self.classes_scroll_area)

        scroll_rich_text = QScrollArea()
        scroll_rich_text.setWidgetResizable(True)
        rich_text_widget_container = QtWidget()
        rich_text_form_layout = QFormLayout(rich_text_widget_container)
        rich_text_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.objectives_edit = QTextEdit()
        self.objectives_edit.setPlaceholderText("Detalhe os objetivos de aprendizagem...")
        self.objectives_edit.setMinimumHeight(80)
        rich_text_form_layout.addRow("Objetivos:", self.objectives_edit)

        self.program_content_edit = QTextEdit()
        self.program_content_edit.setPlaceholderText("Descreva os tópicos da aula...")
        self.program_content_edit.setMinimumHeight(100)
        rich_text_form_layout.addRow("Conteúdo Programático:", self.program_content_edit)

        self.methodology_edit = QTextEdit()
        self.methodology_edit.setPlaceholderText("Descreva as atividades e métodos de ensino...")
        self.methodology_edit.setMinimumHeight(100)
        rich_text_form_layout.addRow("Metodologia/Atividades:", self.methodology_edit)

        self.resources_text_edit = QTextEdit()
        self.resources_text_edit.setPlaceholderText("Liste os materiais e recursos textuais (livros, etc.). Links e arquivos podem ser anexados abaixo.")
        self.resources_text_edit.setMinimumHeight(80)
        rich_text_form_layout.addRow("Recursos (descrição textual):", self.resources_text_edit)

        self.assessment_method_edit = QTextEdit()
        self.assessment_method_edit.setPlaceholderText("Descreva como o progresso dos alunos será avaliado...")
        self.assessment_method_edit.setMinimumHeight(80)
        rich_text_form_layout.addRow("Forma de Avaliação:", self.assessment_method_edit)

        scroll_rich_text.setWidget(rich_text_widget_container)
        main_layout.addWidget(scroll_rich_text)

        attachments_main_h_layout = QHBoxLayout()
        files_v_layout = QVBoxLayout()
        files_label = QLabel("Arquivos Anexados:")
        files_v_layout.addWidget(files_label)
        self.files_list_widget = QListWidget()
        self.files_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        files_v_layout.addWidget(self.files_list_widget)
        files_buttons_h_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Anexar Arquivo(s)")
        self.remove_file_button = QPushButton("Remover Selecionado(s)")
        files_buttons_h_layout.addWidget(self.add_file_button)
        files_buttons_h_layout.addWidget(self.remove_file_button)
        files_v_layout.addLayout(files_buttons_h_layout)
        attachments_main_h_layout.addLayout(files_v_layout)

        links_v_layout = QVBoxLayout()
        links_label = QLabel("Links Externos:")
        links_v_layout.addWidget(links_label)
        self.links_list_widget = QListWidget()
        self.links_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        links_v_layout.addWidget(self.links_list_widget)
        links_buttons_h_layout = QHBoxLayout()
        self.add_link_button = QPushButton("Adicionar Link")
        self.remove_link_button = QPushButton("Remover Selecionado(s)")
        links_buttons_h_layout.addWidget(self.add_link_button)
        links_buttons_h_layout.addWidget(self.remove_link_button)
        links_v_layout.addLayout(links_buttons_h_layout)
        attachments_main_h_layout.addLayout(links_v_layout)

        main_layout.addLayout(attachments_main_h_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self._validate_and_accept_data) # Connect OK button
        main_layout.addWidget(self.button_box)

        self._load_and_display_teacher_classes()
        if self.original_lesson_plan:
            self._populate_fields_for_editing()

        self._update_ui_files_list()
        self._update_ui_links_list()

        # Connect file/link buttons
        self.add_file_button.clicked.connect(self._handle_add_file_dialog)
        self.remove_file_button.clicked.connect(self._handle_remove_selected_files)
        self.add_link_button.clicked.connect(self._handle_add_link_dialog)
        self.remove_link_button.clicked.connect(self._handle_remove_selected_links)

    def _clear_layout(self, layout):
        """Remove todos os widgets de um layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    child_layout = item.layout()
                    if child_layout is not None:
                        self._clear_layout(child_layout)

    def _load_and_display_teacher_classes(self):
        """Carrega as turmas do professor e as exibe como checkboxes."""
        self._clear_layout(self.classes_checkbox_layout)

        # Supondo que o DB Manager pode buscar turmas (Entities do tipo 'turma')
        # Se precisar filtrar por professor, o db_manager precisaria de um método específico
        # ou assumimos que get_all_entities pode, de alguma forma, ser restrito (não é o caso atual)
        # Por agora, vamos carregar todas as turmas como exemplo.
        try:
            all_classes = self.db_manager.get_all_entities(entity_type="turma")
            if not all_classes:
                no_classes_label = QLabel("Nenhuma turma encontrada no sistema.")
                self.classes_checkbox_layout.addWidget(no_classes_label)
                return

            for class_entity in all_classes:
                if class_entity.id is None: continue # Skip if ID is None for some reason
                checkbox = QCheckBox(class_entity.name)
                checkbox.setProperty("class_id", class_entity.id) # Store ID in property
                if self.original_lesson_plan and class_entity.id in self.selected_class_ids:
                    checkbox.setChecked(True)
                checkbox.stateChanged.connect(self._on_class_checkbox_changed)
                self.classes_checkbox_layout.addWidget(checkbox)
            self.classes_checkbox_layout.addStretch(1) # Pushes checkboxes to the top
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Turmas", f"Não foi possível carregar as turmas: {e}")
            self.classes_checkbox_layout.addWidget(QLabel("Erro ao carregar turmas."))


    def _on_class_checkbox_changed(self, state):
        """Atualiza a lista de IDs de turmas selecionadas."""
        checkbox = self.sender()
        class_id = checkbox.property("class_id")
        if state == Qt.CheckState.Checked.value:
            if class_id not in self.selected_class_ids:
                self.selected_class_ids.append(class_id)
        else:
            if class_id in self.selected_class_ids:
                self.selected_class_ids.remove(class_id)

    def _populate_fields_for_editing(self):
        """Preenche os campos do formulário com os dados de um LessonPlan existente."""
        if not self.original_lesson_plan:
            return

        self.title_edit.setText(self.original_lesson_plan.title or "")

        if self.original_lesson_plan.lesson_date:
            # Convert Python datetime to QDateTime
            q_lesson_date = QDateTime(
                self.original_lesson_plan.lesson_date.year,
                self.original_lesson_plan.lesson_date.month,
                self.original_lesson_plan.lesson_date.day,
                0, 0, 0 # Hora, Minuto, Segundo - ajuste se lesson_date tiver hora
            )
            self.lesson_date_edit.setDateTime(q_lesson_date)

        # Campos de texto rico (usar setHtml para manter a formatação se houver)
        self.objectives_edit.setHtml(self.original_lesson_plan.objectives or "")
        self.program_content_edit.setHtml(self.original_lesson_plan.program_content or "")
        self.methodology_edit.setHtml(self.original_lesson_plan.methodology or "")
        self.resources_text_edit.setHtml(self.original_lesson_plan.resources_text or "")
        self.assessment_method_edit.setHtml(self.original_lesson_plan.assessment_method or "")

        # As turmas selecionadas já são tratadas em _load_and_display_teacher_classes
        # Os arquivos e links são populados em _update_ui_files_list e _update_ui_links_list

    def _update_ui_files_list(self):
        """Atualiza a QListWidget de arquivos."""
        self.files_list_widget.clear()
        for file_path, file_obj in self.attached_files_map.items():
            # O ID do arquivo pode ser None se ainda não foi salvo no DB
            item_text = f"{file_obj.file_name} ({file_path})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, file_obj) # Store the LessonPlanFile object
            self.files_list_widget.addItem(item)

    def _update_ui_links_list(self):
        """Atualiza a QListWidget de links."""
        self.links_list_widget.clear()
        for link_obj in self.attached_links_list:
            item_text = f"{link_obj.title} ({link_obj.url})" if link_obj.title else link_obj.url
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, link_obj) # Store the LessonPlanLink object
            self.links_list_widget.addItem(item)

    def _handle_add_file_dialog(self):
        """Abre um diálogo para adicionar arquivos e os adiciona à lista interna."""
        # O diretório inicial pode ser configurado ou lembrado da última vez
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Anexar Arquivos", "", "Todos os Arquivos (*);;Documentos (*.pdf *.doc *.docx *.txt)")

        if file_paths:
            added_count = 0
            skipped_count = 0
            for path in file_paths:
                if path in self.attached_files_map:
                    skipped_count += 1
                    continue

                file_name = path.split('/')[-1]
                # lesson_plan_id será None aqui se for um novo plano. Será definido ao salvar.
                # id e uploaded_at também serão None/default até salvar.
                new_file = LessonPlanFile(
                    lesson_plan_id=self.original_lesson_plan.id if self.original_lesson_plan else 0, # Placeholder
                    file_name=file_name,
                    file_path=path
                )
                self.attached_files_map[path] = new_file
                added_count +=1

            if added_count > 0:
                self._update_ui_files_list()
            if skipped_count > 0:
                QMessageBox.information(self, "Arquivos Ignorados", f"{skipped_count} arquivo(s) já estava(m) na lista e foram ignorados.")

    def _handle_remove_selected_files(self):
        """Remove os arquivos selecionados da lista interna e da UI."""
        selected_items = self.files_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Nenhuma Seleção", "Nenhum arquivo selecionado para remover.")
            return

        confirm_msg = f"Tem certeza que deseja remover os {len(selected_items)} arquivo(s) selecionado(s) da lista de anexos?"
        reply = QMessageBox.question(self, "Confirmar Remoção", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            paths_to_remove = []
            for item in selected_items:
                file_obj = item.data(Qt.ItemDataRole.UserRole)
                if file_obj and file_obj.file_path in self.attached_files_map:
                    paths_to_remove.append(file_obj.file_path)

            for path in paths_to_remove:
                del self.attached_files_map[path]

            self._update_ui_files_list()

    def _handle_add_link_dialog(self):
        """Abre diálogos para adicionar um novo link externo."""
        url_str, ok_url = QInputDialog.getText(self, "Adicionar Link Externo", "URL do Link (ex: http://www.exemplo.com):")
        if not ok_url or not url_str.strip():
            return # Usuário cancelou ou não inseriu URL

        qurl = QUrl(url_str.strip())
        if not qurl.isValid() or not (qurl.scheme() in ["http", "https"]):
            QMessageBox.warning(self, "URL Inválida", "A URL fornecida não é válida. Certifique-se de incluir http:// ou https://.")
            return

        title_str, ok_title = QInputDialog.getText(self, "Adicionar Link Externo", "Título para o Link (opcional):")
        # ok_title será True mesmo se o título estiver vazio, o que é permitido.

        # lesson_plan_id será None aqui se for um novo plano. Será definido ao salvar.
        new_link = LessonPlanLink(
            lesson_plan_id=self.original_lesson_plan.id if self.original_lesson_plan else 0, # Placeholder
            url=qurl.toString(),
            title=title_str.strip() if ok_title else None
        )
        self.attached_links_list.append(new_link)
        self._update_ui_links_list()

    def _handle_remove_selected_links(self):
        """Remove os links selecionados da lista interna e da UI."""
        selected_items = self.links_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Nenhuma Seleção", "Nenhum link selecionado para remover.")
            return

        confirm_msg = f"Tem certeza que deseja remover os {len(selected_items)} link(s) selecionado(s)?"
        reply = QMessageBox.question(self, "Confirmar Remoção", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            links_to_remove = []
            for item in selected_items:
                link_obj = item.data(Qt.ItemDataRole.UserRole)
                if link_obj:
                    links_to_remove.append(link_obj)

            for link_obj in links_to_remove:
                if link_obj in self.attached_links_list: # Check necessary if list could change elsewhere
                    self.attached_links_list.remove(link_obj)

            self._update_ui_links_list()

    def _collect_data_from_form(self) -> Optional[LessonPlan]:
        """Coleta os dados dos campos do formulário e cria/atualiza um objeto LessonPlan."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Validação Falhou", "O título do plano de aula é obrigatório.")
            return None

        lesson_date_qdt = self.lesson_date_edit.dateTime()
        # Convert QDateTime to Python datetime. Ensure it's not None.
        # toPyDateTime() returns a Python datetime object.
        py_lesson_date = lesson_date_qdt.toPyDateTime() if lesson_date_qdt else None

        objectives = self.objectives_edit.toHtml()
        program_content = self.program_content_edit.toHtml()
        methodology = self.methodology_edit.toHtml()
        resources_text = self.resources_text_edit.toHtml()
        assessment_method = self.assessment_method_edit.toHtml()

        # Prepare files and links:
        # For files, the LessonPlanFile objects in attached_files_map are mostly ready.
        # Their lesson_plan_id will be correctly set by the DB manager during actual save.
        # If it's a new LessonPlan, their current lesson_plan_id (placeholder 0) is fine.
        # If editing, existing files from original_lesson_plan already have their correct lesson_plan_id.
        # New files added during edit session also have placeholder 0, which is fine.
        current_files = list(self.attached_files_map.values())

        # Same logic for links
        current_links = list(self.attached_links_list) # Make a copy

        if self.original_lesson_plan and self.original_lesson_plan.id is not None:
            # Editing existing plan
            return LessonPlan(
                id=self.original_lesson_plan.id,
                teacher_id=self.current_teacher_id,
                title=title,
                lesson_date=py_lesson_date,
                class_ids=list(self.selected_class_ids), # Ensure it's a copy
                objectives=objectives,
                program_content=program_content,
                methodology=methodology,
                resources_text=resources_text,
                assessment_method=assessment_method,
                files=current_files,
                links=current_links,
                created_at=self.original_lesson_plan.created_at, # Preserve original creation date
                updated_at=datetime.now() # Update to now
            )
        else:
            # Creating new plan
            return LessonPlan(
                teacher_id=self.current_teacher_id,
                title=title,
                lesson_date=py_lesson_date,
                class_ids=list(self.selected_class_ids),
                objectives=objectives,
                program_content=program_content,
                methodology=methodology,
                resources_text=resources_text,
                assessment_method=assessment_method,
                files=current_files,
                links=current_links,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    def _validate_and_accept_data(self):
        """Valida os dados do formulário e, se válidos, processa e fecha o diálogo."""
        collected_lp = self._collect_data_from_form()
        if collected_lp:
            self.lesson_plan_to_save = collected_lp
            self.accept() # Fecha o diálogo com QDialog.DialogCode.Accepted
        # If collected_lp is None, _collect_data_from_form already showed a warning.

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication # Ensure QApplication is imported here
    app = QApplication(sys.argv)

    class MockDBManager(DatabaseManager):
        def __init__(self, db_path=':memory:'):
            # super().__init__(db_path) # Avoid actual DB connection for mock
            print("MockDBManager for LessonPlanDialog test initialized (no actual DB connection).")
            self.db_path = db_path
            self.conn = None # No connection for mock

        def get_all_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
            if entity_type == "turma":
                return [
                    Entity(id=1, name="Turma A1", type="turma"),
                    Entity(id=2, name="Turma B2", type="turma"),
                    Entity(id=3, name="Turma C3 - Noite", type="turma"),
                ]
            return []

        # Add mock methods for any other DB interactions if needed for dialog testing
        # For example, if the dialog tried to save directly (it doesn't currently)

    mock_db_manager = MockDBManager()

    print("--- Testando Criação de Novo Plano de Aula ---")
    dialog_new = LessonPlanDialog(db_manager=mock_db_manager, teacher_id=101) # Example teacher_id

    # Simulate some user interactions for testing _collect_data_from_form
    dialog_new.title_edit.setText("  Aula Teste Título  ")
    dialog_new.objectives_edit.setHtml("<p>Aprender <b>PyQt6</b></p>")
    # Select a class by finding its checkbox (example)
    for i in range(dialog_new.classes_checkbox_layout.count()):
        widget = dialog_new.classes_checkbox_layout.itemAt(i).widget()
        if isinstance(widget, QCheckBox) and widget.text() == "Turma A1":
            widget.setChecked(True)
            break
    # Add a mock file
    mock_file = LessonPlanFile(lesson_plan_id=0, file_name="teste.pdf", file_path="/mock/teste.pdf")
    dialog_new.attached_files_map[mock_file.file_path] = mock_file
    dialog_new._update_ui_files_list()
    # Add a mock link
    mock_link = LessonPlanLink(lesson_plan_id=0, url="http://example.com", title="Exemplo")
    dialog_new.attached_links_list.append(mock_link)
    dialog_new._update_ui_links_list()

    if dialog_new.exec() == QDialog.DialogCode.Accepted:
        print("\n--- Novo Plano de Aula Salvo (Mock) ---")
        saved_plan = dialog_new.lesson_plan_to_save
        if saved_plan:
            print(f"  ID: {saved_plan.id}")
            print(f"  Título: '{saved_plan.title}'")
            print(f"  ID Professor: {saved_plan.teacher_id}")
            print(f"  Data da Aula: {saved_plan.lesson_date}")
            print(f"  Objetivos: {saved_plan.objectives}")
            print(f"  Conteúdo: {saved_plan.program_content}") # Assuming empty for this test
            print(f"  IDs Turmas Selecionadas: {saved_plan.class_ids}")
            print(f"  Arquivos ({len(saved_plan.files)}):")
            for f in saved_plan.files:
                print(f"    - {f.file_name} (Path: {f.file_path}, LP_ID: {f.lesson_plan_id})")
            print(f"  Links ({len(saved_plan.links)}):")
            for l_link in saved_plan.links:
                print(f"    - {l_link.title} ({l_link.url}, LP_ID: {l_link.lesson_plan_id})")
            print(f"  Criado em: {saved_plan.created_at}")
            print(f"  Atualizado em: {saved_plan.updated_at}")
    else:
        print("\n--- Criação de Novo Plano de Aula Cancelada ---")

    print("\n--- Testando Edição de Plano de Aula Existente (Mock) ---")
    existing_files = [LessonPlanFile(id=1, lesson_plan_id=1, file_name="doc.pdf", file_path="/orig/doc.pdf", uploaded_at=datetime.now())]
    existing_links = [LessonPlanLink(id=1, lesson_plan_id=1, url="http://site.com", title="Site", added_at=datetime.now())]
    existing_lp_instance = LessonPlan(
        id=1, teacher_id=102, title="Plano Original", lesson_date=datetime(2023, 10, 5),
        class_ids=[2], files=existing_files, links=existing_links,
        objectives="<p>Objetivos Originais</p>", created_at=datetime(2023,10,1)
    )
    dialog_edit = LessonPlanDialog(db_manager=mock_db_manager, lesson_plan=existing_lp_instance)
    # Simulate user changing the title and adding a new class
    # dialog_edit.title_edit.setText("Plano Original (Modificado)")
    # for i in range(dialog_edit.classes_checkbox_layout.count()):
    #     widget = dialog_edit.classes_checkbox_layout.itemAt(i).widget()
    #     if isinstance(widget, QCheckBox) and widget.text() == "Turma A1": # Add Turma A1
    #         widget.setChecked(True)
    #         break

    # To run interactively for manual testing:
    # dialog_edit.show()
    # if app.exec() == QDialog.DialogCode.Accepted: # Need to handle app.exec for interactive
    # For non-interactive test of collection:
    if dialog_edit.exec() == QDialog.DialogCode.Accepted: # Simulates clicking OK
        print("\n--- Plano de Aula Editado Salvo (Mock) ---")
        saved_plan = dialog_edit.lesson_plan_to_save
        if saved_plan:
            print(f"  ID: {saved_plan.id}")
            print(f"  Título: '{saved_plan.title}'")
            print(f"  ID Professor: {saved_plan.teacher_id}")
            print(f"  Data da Aula: {saved_plan.lesson_date}")
            print(f"  Objetivos: {saved_plan.objectives}")
            print(f"  IDs Turmas Selecionadas: {saved_plan.class_ids}")
            print(f"  Arquivos ({len(saved_plan.files)}):")
            for f in saved_plan.files:
                print(f"    - {f.file_name} (Path: {f.file_path}, ID: {f.id}, LP_ID: {f.lesson_plan_id})")
            print(f"  Links ({len(saved_plan.links)}):")
            for l_link in saved_plan.links:
                print(f"    - {l_link.title} ({l_link.url}, ID: {l_link.id}, LP_ID: {l_link.lesson_plan_id})")
            print(f"  Criado em: {saved_plan.created_at}") # Should be original
            print(f"  Atualizado em: {saved_plan.updated_at}") # Should be new
    else:
        print("\n--- Edição de Plano de Aula Cancelada ---")

    sys.exit(0) # Exit cleanly for non-interactive tests
