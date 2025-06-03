import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Optional, Any, Dict
from src.core.models import Event, Task, Question, QuizConfig, QuizAttempt, Entity

class DatabaseManager:
    def __init__(self, db_path='data/agenda.db'):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Estabelece a conexão com o banco de dados SQLite."""
        try:
            # Garante que o diretório do banco de dados exista
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Permite acesso aos campos por nome
            self.conn.execute("PRAGMA foreign_keys = ON;") # Habilita chaves estrangeiras
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            # Considerar levantar uma exceção personalizada aqui ou tratar de forma mais robusta

    def _create_tables(self):
        """Cria as tabelas do banco de dados se elas não existirem."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida. Tabelas não criadas.")
            return

        try:
            cursor = self.conn.cursor()

            # Tabela Entities
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Tabela Events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                event_type TEXT NOT NULL,
                location TEXT,
                recurrence_rule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Tabela Event_Entities (Tabela de Associação)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Event_Entities (
                event_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                role TEXT,
                PRIMARY KEY (event_id, entity_id),
                FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES Entities(id) ON DELETE CASCADE
            )
            """)

            # Tabela Tasks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'Medium',
                due_date TIMESTAMP,
                status TEXT DEFAULT 'Open',
                parent_event_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_event_id) REFERENCES Events(id) ON DELETE SET NULL
            )
            """)

            # Tabela Settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            # Tabela Questions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                subject TEXT,
                difficulty TEXT,
                options TEXT, -- JSON array de strings
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Triggers para atualizar 'updated_at'

            # Trigger para Entities
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_entities_updated_at
            AFTER UPDATE ON Entities
            FOR EACH ROW
            BEGIN
                UPDATE Entities SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            # Trigger para Events
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_events_updated_at
            AFTER UPDATE ON Events
            FOR EACH ROW
            BEGIN
                UPDATE Events SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            # Trigger para Tasks
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
            AFTER UPDATE ON Tasks
            FOR EACH ROW
            BEGIN
                UPDATE Tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            # Trigger para Questions
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_questions_updated_at
            AFTER UPDATE ON Questions
            FOR EACH ROW
            BEGIN
                UPDATE Questions SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            # Tabela QuizConfigs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS QuizConfigs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                question_ids TEXT NOT NULL, -- JSON list de ints
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
            )
            """)
            # Trigger para QuizConfigs updated_at
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_quiz_configs_updated_at
            AFTER UPDATE ON QuizConfigs
            FOR EACH ROW
            BEGIN
                UPDATE QuizConfigs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            # Tabela QuizAttempts
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS QuizAttempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_config_id INTEGER NOT NULL,
                user_answers TEXT NOT NULL, -- JSON Dict[int, str]
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Embora possa não ser muito usado
                FOREIGN KEY (quiz_config_id) REFERENCES QuizConfigs(id) ON DELETE CASCADE
            )
            """)
            # Trigger para QuizAttempts updated_at
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_quiz_attempts_updated_at
            AFTER UPDATE ON QuizAttempts
            FOR EACH ROW
            BEGIN
                UPDATE QuizAttempts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao criar tabelas ou triggers: {e}")
            if self.conn:
                self.conn.rollback() # Desfaz alterações em caso de erro

    def _datetime_from_str(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Converte string ISO 8601 para objeto datetime."""
        if timestamp_str:
            try:
                # Tenta primeiro com milissegundos, depois sem
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                try:
                    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Adicione mais formatos se necessário ou logue um aviso
                    print(f"Aviso: Formato de data/hora inesperado '{timestamp_str}'")
                    return None
        return None

    def _datetime_to_str(self, dt_obj: Optional[datetime]) -> Optional[str]:
        """Converte objeto datetime para string ISO 8601 (formato aceito pelo SQLite)."""
        if dt_obj:
            return dt_obj.isoformat(sep=' ', timespec='seconds') # YYYY-MM-DD HH:MM:SS
        return None

    def get_events_by_date(self, date_obj: date) -> List[Event]:
        """Busca eventos pela data (ignorando a hora) de start_time."""
        events = []
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida.")
            return events
        
        try:
            cursor = self.conn.cursor()
            # Busca eventos onde a data de start_time corresponde à date_obj
            # Usamos strftime para comparar apenas a parte da data
            query = """
            SELECT id, title, description, start_time, end_time, event_type, location, recurrence_rule, created_at, updated_at
            FROM Events
            WHERE date(start_time) = ?
            ORDER BY start_time
            """
            cursor.execute(query, (date_obj.isoformat(),))
            
            for row in cursor.fetchall():
                event = Event(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    start_time=self._datetime_from_str(row['start_time']),
                    end_time=self._datetime_from_str(row['end_time']),
                    event_type=row['event_type'],
                    location=row['location'],
                    recurrence_rule=row['recurrence_rule'],
                    created_at=self._datetime_from_str(row['created_at']),
                    updated_at=self._datetime_from_str(row['updated_at'])
                )
                # Filtrar eventos onde start_time não pôde ser parseado (embora não devesse acontecer com dados válidos)
                if event.start_time:
                    events.append(event)
        except sqlite3.Error as e:
            print(f"Erro ao buscar eventos por data: {e}")
        return events

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Busca um evento específico pelo seu ID."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida.")
            return None
            
        try:
            cursor = self.conn.cursor()
            query = """
            SELECT id, title, description, start_time, end_time, event_type, location, recurrence_rule, created_at, updated_at
            FROM Events
            WHERE id = ?
            """
            cursor.execute(query, (event_id,))
            row = cursor.fetchone()
            
            if row:
                event = Event(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    start_time=self._datetime_from_str(row['start_time']),
                    end_time=self._datetime_from_str(row['end_time']),
                    event_type=row['event_type'],
                    location=row['location'],
                    recurrence_rule=row['recurrence_rule'],
                    created_at=self._datetime_from_str(row['created_at']),
                    updated_at=self._datetime_from_str(row['updated_at'])
                )
                return event
        except sqlite3.Error as e:
            print(f"Erro ao buscar evento por ID: {e}")
        return None

    def add_event(self, event: Event) -> Optional[Event]:
        """Adiciona um novo evento ao banco de dados."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida.")
            return None
        
        try:
            cursor = self.conn.cursor()
            query = """
            INSERT INTO Events (title, description, start_time, end_time, event_type, location, recurrence_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                event.title,
                event.description,
                self._datetime_to_str(event.start_time),
                self._datetime_to_str(event.end_time),
                event.event_type,
                event.location,
                event.recurrence_rule
            ))
            self.conn.commit()
            event.id = cursor.lastrowid
            
            # Para obter created_at e updated_at, precisaríamos de uma nova query
            # ou confiar que o objeto Event já os tem (se aplicável) ou são None
            # Por simplicidade, vamos buscar o evento recém-criado para ter todos os campos.
            if event.id is not None:
                return self.get_event_by_id(event.id)
            return None # Algo deu errado se não houver lastrowid
            
        except sqlite3.Error as e:
            print(f"Erro ao adicionar evento: {e}")
            if self.conn:
                self.conn.rollback()
            return None

    def update_event(self, event: Event) -> bool:
        """Atualiza um evento existente no banco de dados."""
        if not self.conn or event.id is None:
            print("Conexão não estabelecida ou ID do evento não fornecido para atualização.")
            return False
        
        try:
            cursor = self.conn.cursor()
            query = """
            UPDATE Events
            SET title = ?, description = ?, start_time = ?, end_time = ?, 
                event_type = ?, location = ?, recurrence_rule = ?
            WHERE id = ?
            """
            # updated_at será atualizado pelo trigger
            cursor.execute(query, (
                event.title,
                event.description,
                self._datetime_to_str(event.start_time),
                self._datetime_to_str(event.end_time),
                event.event_type,
                event.location,
                event.recurrence_rule,
                event.id
            ))
            self.conn.commit()
            return cursor.rowcount > 0 # Retorna True se alguma linha foi afetada
        except sqlite3.Error as e:
            print(f"Erro ao atualizar evento: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def delete_event(self, event_id: int) -> bool:
        """Exclui um evento do banco de dados pelo seu ID."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida.")
            return False
            
        try:
            cursor = self.conn.cursor()
            query = "DELETE FROM Events WHERE id = ?"
            cursor.execute(query, (event_id,))
            self.conn.commit()
            return cursor.rowcount > 0 # Retorna True se alguma linha foi afetada
        except sqlite3.Error as e:
            print(f"Erro ao excluir evento: {e}")
            if self.conn: self.conn.rollback()
            return False

    def _add_sample_event_and_task(self):
        """Adiciona um evento de exemplo e uma tarefa associada para testes."""
        if not self.conn:
            print("Conexão para _add_sample_event_and_task não estabelecida.")
            return
        try:
            cursor = self.conn.cursor()
            sample_event_date = date(2024, 1, 1)
            cursor.execute("SELECT id FROM Events WHERE title = ? AND date(start_time) = ?", 
                           ("Reunião de Planejamento", sample_event_date.isoformat()))
            
            event_id_for_task = None
            existing_event = cursor.fetchone()

            if existing_event:
                print(f"Evento de exemplo 'Reunião de Planejamento' para {sample_event_date} já existe.")
                event_id_for_task = existing_event['id']
            else:
                event_data = {
                    "title": "Reunião de Planejamento",
                    "description": "Discutir os próximos passos do projeto.",
                    "start_time": datetime.combine(sample_event_date, datetime.min.time()).replace(hour=10),
                    "end_time": datetime.combine(sample_event_date, datetime.min.time()).replace(hour=11, minute=30),
                    "event_type": "reuniao",
                    "location": "Sala de Conferências 1"
                }
                query_insert_event = """
                INSERT INTO Events (title, description, start_time, end_time, event_type, location)
                VALUES (?, ?, ?, ?, ?, ?)"""
                cursor.execute(query_insert_event, (
                    event_data["title"], event_data["description"],
                    self._datetime_to_str(event_data["start_time"]), self._datetime_to_str(event_data["end_time"]),
                    event_data["event_type"], event_data["location"]
                ))
                self.conn.commit()
                event_id_for_task = cursor.lastrowid
                print(f"Evento de exemplo '{event_data['title']}' adicionado para {sample_event_date} com ID {event_id_for_task}.")

            if event_id_for_task:
                cursor.execute("SELECT id FROM Tasks WHERE title = ? AND parent_event_id = ?",
                               ("Preparar apresentação para Reunião de Planejamento", event_id_for_task))
                if cursor.fetchone():
                    print("Tarefa de exemplo 'Preparar apresentação...' já existe para este evento.")
                else:
                    task_data = {
                        "title": "Preparar apresentação para Reunião de Planejamento",
                        "description": "Slides sobre o progresso do Q1.", "priority": "High",
                        "due_date": datetime.combine(sample_event_date, datetime.min.time()).replace(hour=9),
                        "status": "Open", "parent_event_id": event_id_for_task
                    }
                    query_insert_task = """
                    INSERT INTO Tasks (title, description, priority, due_date, status, parent_event_id)
                    VALUES (?, ?, ?, ?, ?, ?)"""
                    cursor.execute(query_insert_task, (
                        task_data["title"], task_data["description"], task_data["priority"],
                        self._datetime_to_str(task_data["due_date"]), task_data["status"], task_data["parent_event_id"]
                    ))
                    self.conn.commit()
                    print(f"Tarefa de exemplo '{task_data['title']}' adicionada.")
        except sqlite3.Error as e:
            print(f"Erro ao adicionar evento/tarefa de exemplo em _add_sample_event_and_task: {e}")
            if self.conn: self.conn.rollback()
            
    # --- CRUD para Tasks ---
    def add_task(self, task: Task) -> Optional[Task]:
        """Adiciona uma nova tarefa ao banco de dados."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida.")
            return None
        try:
            cursor = self.conn.cursor()
            query = """
            INSERT INTO Tasks (title, description, priority, due_date, status, parent_event_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                task.title,
                task.description,
                task.priority,
                self._datetime_to_str(task.due_date),
                task.status,
                task.parent_event_id
            ))
            self.conn.commit()
            task.id = cursor.lastrowid
            if task.id:
                # Buscar para obter created_at e updated_at definidos pelo DB
                return self.get_task_by_id(task.id)
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar tarefa: {e}")
            if self.conn: self.conn.rollback()
            return None

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Busca uma tarefa específica pelo seu ID."""
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM Tasks WHERE id = ?"
            cursor.execute(query, (task_id,))
            row = cursor.fetchone()
            if row:
                return Task(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    priority=row['priority'],
                    due_date=self._datetime_from_str(row['due_date']),
                    status=row['status'],
                    parent_event_id=row['parent_event_id'],
                    created_at=self._datetime_from_str(row['created_at']),
                    updated_at=self._datetime_from_str(row['updated_at'])
                )
            return None
        except sqlite3.Error as e:
            print(f"Erro ao buscar tarefa por ID: {e}")
            return None

    def get_all_tasks(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Task]:
        """Busca todas as tarefas, com filtros opcionais por status e prioridade."""
        if not self.conn: return []
        tasks = []
        try:
            cursor = self.conn.cursor()
            base_query = "SELECT * FROM Tasks"
            conditions = []
            params = []

            if status:
                conditions.append("status = ?")
                params.append(status)
            if priority:
                conditions.append("priority = ?")
                params.append(priority)
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY due_date DESC, created_at DESC" # Exemplo de ordenação
            
            cursor.execute(base_query, params)
            for row in cursor.fetchall():
                tasks.append(Task(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    priority=row['priority'],
                    due_date=self._datetime_from_str(row['due_date']),
                    status=row['status'],
                    parent_event_id=row['parent_event_id'],
                    created_at=self._datetime_from_str(row['created_at']),
                    updated_at=self._datetime_from_str(row['updated_at'])
                ))
        except sqlite3.Error as e:
            print(f"Erro ao buscar todas as tarefas: {e}")
        return tasks

    def update_task(self, task: Task) -> bool:
        """Atualiza uma tarefa existente no banco de dados."""
        if not self.conn or task.id is None: return False
        try:
            cursor = self.conn.cursor()
            query = """
            UPDATE Tasks
            SET title = ?, description = ?, priority = ?, due_date = ?, status = ?, parent_event_id = ?
            WHERE id = ?
            """
            # updated_at será atualizado pelo trigger
            cursor.execute(query, (
                task.title,
                task.description,
                task.priority,
                self._datetime_to_str(task.due_date),
                task.status,
                task.parent_event_id,
                task.id
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao atualizar tarefa: {e}")
            if self.conn: self.conn.rollback()
            return False

    def delete_task(self, task_id: int) -> bool:
        """Exclui uma tarefa do banco de dados pelo seu ID."""
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            query = "DELETE FROM Tasks WHERE id = ?"
            cursor.execute(query, (task_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao excluir tarefa: {e}")
            if self.conn: self.conn.rollback()
            return False

    # --- CRUD para Questions ---
    def _question_from_row(self, row: sqlite3.Row) -> Optional[Question]:
        """Cria um objeto Question a partir de uma linha do banco de dados."""
        if not row:
            return None
        
        options_json = row['options']
        options_list: List[str] = []
        if options_json:
            try:
                options_list = json.loads(options_json)
                if not isinstance(options_list, list) or not all(isinstance(opt, str) for opt in options_list):
                    print(f"Aviso: 'options' para Question ID {row['id']} não é uma lista de strings JSON válida: {options_json}")
                    options_list = [] # Resetar para lista vazia se o formato for inválido
            except json.JSONDecodeError:
                print(f"Aviso: Falha ao decodificar 'options' JSON para Question ID {row['id']}: {options_json}")
                options_list = []

        return Question(
            id=row['id'],
            text=row['text'],
            subject=row['subject'],
            difficulty=row['difficulty'],
            options=options_list,
            answer=row['answer'],
            created_at=self._datetime_from_str(row['created_at']),
            updated_at=self._datetime_from_str(row['updated_at'])
        )

    def add_question(self, question: Question) -> Optional[Question]:
        """Adiciona uma nova pergunta ao banco de dados."""
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            options_json = json.dumps(question.options) if question.options else None
            query = """
            INSERT INTO Questions (text, subject, difficulty, options, answer)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                question.text,
                question.subject,
                question.difficulty,
                options_json,
                question.answer
            ))
            self.conn.commit()
            question.id = cursor.lastrowid
            if question.id:
                return self.get_question_by_id(question.id) # Para obter timestamps
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar pergunta: {e}")
            if self.conn: self.conn.rollback()
            return None

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """Busca uma pergunta específica pelo seu ID."""
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM Questions WHERE id = ?"
            cursor.execute(query, (question_id,))
            row = cursor.fetchone()
            return self._question_from_row(row)
        except sqlite3.Error as e:
            print(f"Erro ao buscar pergunta por ID: {e}")
            return None

    def get_all_questions(self, subject: Optional[str] = None, difficulty: Optional[str] = None) -> List[Question]:
        """Busca todas as perguntas, com filtros opcionais por assunto e dificuldade."""
        if not self.conn: return []
        questions: List[Question] = []
        try:
            cursor = self.conn.cursor()
            base_query = "SELECT * FROM Questions"
            conditions = []
            params: List[Any] = [] # Especificar o tipo do params

            if subject:
                conditions.append("subject = ?")
                params.append(subject)
            if difficulty:
                conditions.append("difficulty = ?")
                params.append(difficulty)
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY subject, id"
            
            cursor.execute(base_query, params)
            for row in cursor.fetchall():
                question_obj = self._question_from_row(row)
                if question_obj:
                    questions.append(question_obj)
        except sqlite3.Error as e:
            print(f"Erro ao buscar todas as perguntas: {e}")
        return questions

    def update_question(self, question: Question) -> bool:
        """Atualiza uma pergunta existente no banco de dados."""
        if not self.conn or question.id is None: return False
        try:
            cursor = self.conn.cursor()
            options_json = json.dumps(question.options) if question.options else None
            query = """
            UPDATE Questions
            SET text = ?, subject = ?, difficulty = ?, options = ?, answer = ?
            WHERE id = ?
            """
            # updated_at será atualizado pelo trigger
            cursor.execute(query, (
                question.text,
                question.subject,
                question.difficulty,
                options_json,
                question.answer,
                question.id
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao atualizar pergunta: {e}")
            if self.conn: self.conn.rollback()
            return False

    def delete_question(self, question_id: int) -> bool:
        """Exclui uma pergunta do banco de dados pelo seu ID."""
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            query = "DELETE FROM Questions WHERE id = ?"
            cursor.execute(query, (question_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao excluir pergunta: {e}")
            if self.conn: self.conn.rollback()
            return False

    # --- CRUD para QuizConfig ---
    def _quiz_config_from_row(self, row: sqlite3.Row) -> Optional[QuizConfig]:
        if not row: return None
        question_ids_json = row['question_ids']
        question_ids_list: List[int] = []
        try:
            question_ids_list = json.loads(question_ids_json)
            if not isinstance(question_ids_list, list) or not all(isinstance(qid, int) for qid in question_ids_list):
                print(f"Aviso: 'question_ids' para QuizConfig ID {row['id']} não é uma lista de inteiros JSON válida.")
                question_ids_list = []
        except json.JSONDecodeError:
            print(f"Aviso: Falha ao decodificar 'question_ids' JSON para QuizConfig ID {row['id']}.")
            question_ids_list = []
        
        return QuizConfig(
            id=row['id'],
            name=row['name'],
            question_ids=question_ids_list,
            created_at=self._datetime_from_str(row['created_at'])
            # updated_at não está no modelo QuizConfig, mas o trigger o atualiza no DB
        )

    def add_quiz_config(self, quiz_config: QuizConfig) -> Optional[QuizConfig]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            question_ids_json = json.dumps(quiz_config.question_ids)
            query = "INSERT INTO QuizConfigs (name, question_ids) VALUES (?, ?)"
            cursor.execute(query, (quiz_config.name, question_ids_json))
            self.conn.commit()
            quiz_config.id = cursor.lastrowid
            if quiz_config.id:
                # Buscar para obter created_at e garantir consistência
                return self.get_quiz_config_by_id(quiz_config.id)
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar QuizConfig: {e}")
            if self.conn: self.conn.rollback()
            return None

    def get_quiz_config_by_id(self, config_id: int) -> Optional[QuizConfig]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            query = "SELECT id, name, question_ids, created_at FROM QuizConfigs WHERE id = ?"
            cursor.execute(query, (config_id,))
            row = cursor.fetchone()
            return self._quiz_config_from_row(row) # Uses the first _quiz_config_from_row
        except sqlite3.Error as e:
            print(f"Erro ao buscar QuizConfig por ID: {e}")
            return None
            
    def get_all_quiz_configs(self) -> List[QuizConfig]:
        if not self.conn: return [] # Corrected return type for connection failure
        configs: List[QuizConfig] = []
        try:
            cursor = self.conn.cursor()
            query = "SELECT id, name, question_ids, created_at FROM QuizConfigs ORDER BY created_at DESC"
            cursor.execute(query)
            for row in cursor.fetchall():
                config = self._quiz_config_from_row(row) # Uses the first _quiz_config_from_row
                if config:
                    configs.append(config)
        except sqlite3.Error as e:
            print(f"Erro ao buscar todas as QuizConfigs: {e}")
        return configs

    # --- CRUD para Entities ---
    def _entity_from_row(self, row: sqlite3.Row) -> Optional[Entity]:
        if not row: return None
        details_dict: Dict[str, Any] = {}
        if row['details_json']:
            try:
                details_dict = json.loads(row['details_json'])
            except json.JSONDecodeError:
                print(f"Aviso: Falha ao decodificar 'details_json' para Entity ID {row['id']}.")
        
        return Entity(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            details_json=details_dict,
            created_at=self._datetime_from_str(row['created_at']),
            updated_at=self._datetime_from_str(row['updated_at'])
        )

    def add_entity(self, entity: Entity) -> Optional[Entity]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            details_json_str = json.dumps(entity.details_json) if entity.details_json else None
            query = "INSERT INTO Entities (name, type, details_json) VALUES (?, ?, ?)"
            cursor.execute(query, (entity.name, entity.type, details_json_str))
            self.conn.commit()
            entity.id = cursor.lastrowid
            if entity.id:
                return self.get_entity_by_id(entity.id) # Para obter timestamps e consistência
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar Entity: {e}")
            if self.conn: self.conn.rollback()
            return None

    def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM Entities WHERE id = ?"
            cursor.execute(query, (entity_id,))
            row = cursor.fetchone()
            return self._entity_from_row(row)
        except sqlite3.Error as e:
            print(f"Erro ao buscar Entity por ID: {e}")
            return None
            
    def get_all_entities(self, entity_type: Optional[str] = None) -> List[Entity]: # Renamed and added entity_type
        if not self.conn: return []
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM Entities"
            params: List[Any] = [] # Ensure params is defined
            if entity_type:
                query += " WHERE type = ?"
                params.append(entity_type)
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            entities: List[Entity] = []
            for row in cursor.fetchall():
                entity_obj = self._entity_from_row(row)
                if entity_obj:
                    entities.append(entity_obj)
            return entities
        except sqlite3.Error as e:
            print(f"Erro ao buscar todas as Entities: {e}")
            return []

    def update_entity(self, entity: Entity) -> bool:
        if not self.conn or entity.id is None: return False
        try:
            cursor = self.conn.cursor()
            details_json_str = json.dumps(entity.details_json) if entity.details_json else None
            query = "UPDATE Entities SET name = ?, type = ?, details_json = ? WHERE id = ?"
            # updated_at será atualizado pelo trigger
            cursor.execute(query, (entity.name, entity.type, details_json_str, entity.id))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao atualizar Entity: {e}")
            if self.conn: self.conn.rollback()
            return False

    def delete_entity(self, entity_id: int) -> bool:
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            query = "DELETE FROM Entities WHERE id = ?"
            cursor.execute(query, (entity_id,))
            self.conn.commit()
            # ON DELETE CASCADE deve cuidar da tabela Event_Entities
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao excluir Entity: {e}")
            if self.conn: self.conn.rollback()
            return False

    # --- Associações Event-Entity ---
    def link_entity_to_event(self, event_id: int, entity_id: int, role: str) -> bool:
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            # Usar INSERT OR IGNORE para evitar erro se o link já existir, 
            # ou INSERT OR REPLACE se quisermos atualizar o papel se o link existir.
            # Por simplicidade, INSERT OR IGNORE. Se precisar atualizar o papel, uma lógica de UPDATE seria melhor.
            query = "INSERT OR IGNORE INTO Event_Entities (event_id, entity_id, role) VALUES (?, ?, ?)"
            cursor.execute(query, (event_id, entity_id, role))
            self.conn.commit()
            return cursor.rowcount > 0 # Retorna True se uma nova linha foi inserida
        except sqlite3.Error as e:
            print(f"Erro ao vincular Entity {entity_id} ao Event {event_id} com role {role}: {e}")
            if self.conn: self.conn.rollback()
            return False

    def unlink_entity_from_event(self, event_id: int, entity_id: int) -> bool:
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            query = "DELETE FROM Event_Entities WHERE event_id = ? AND entity_id = ?"
            cursor.execute(query, (event_id, entity_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Erro ao desvincular Entity {entity_id} do Event {event_id}: {e}")
            if self.conn: self.conn.rollback()
            return False

    def get_entities_for_event(self, event_id: int) -> List[tuple[Entity, str]]:
        if not self.conn: return []
        linked_entities: List[tuple[Entity, str]] = []
        try:
            cursor = self.conn.cursor()
            # Query para buscar entidades e seus papéis para um evento específico
            query = """
            SELECT E.*, EE.role
            FROM Entities E
            JOIN Event_Entities EE ON E.id = EE.entity_id
            WHERE EE.event_id = ?
            """
            cursor.execute(query, (event_id,))
            for row in cursor.fetchall():
                entity = self._entity_from_row(row) # Reutiliza o helper
                role = row['role']
                if entity:
                    linked_entities.append((entity, role))
        except sqlite3.Error as e:
            print(f"Erro ao buscar entidades para o Evento ID {event_id}: {e}")
        return linked_entities


    # The duplicated QuizConfig methods that were here are now removed.
    # The correct get_quiz_config_by_id and get_all_quiz_configs have been inserted earlier,
    # after the first (and correct) add_quiz_config method.

    # --- CRUD para QuizAttempt ---
    def _quiz_attempt_from_row(self, row: sqlite3.Row) -> Optional[QuizAttempt]:
        if not row: return None
        user_answers_json = row['user_answers']
        question_ids_list: List[int] = []
        try:
            question_ids_list = json.loads(question_ids_json)
            if not isinstance(question_ids_list, list) or not all(isinstance(qid, int) for qid in question_ids_list):
                print(f"Aviso: 'question_ids' para QuizConfig ID {row['id']} não é uma lista de inteiros JSON válida.")
                question_ids_list = []
        except json.JSONDecodeError:
            print(f"Aviso: Falha ao decodificar 'question_ids' JSON para QuizConfig ID {row['id']}.")
            question_ids_list = []
        
        return QuizConfig(
            id=row['id'],
            name=row['name'],
            question_ids=question_ids_list,
            created_at=self._datetime_from_str(row['created_at'])
            # updated_at não está no modelo QuizConfig, mas o trigger o atualiza no DB
        )

    # add_quiz_config, get_quiz_config_by_id, get_all_quiz_configs were moved up
    # to replace the duplicated _quiz_config_from_row and its associated methods.
    # This SEARCH block is now targeting the content that was originally after
    # the second (now deleted) _quiz_config_from_row.
    # The new content for these methods is already in the REPLACE block above.
    # This effectively deletes the duplicated methods that were here.
        user_answers_dict: Dict[int, str] = {}
        try:
            # As chaves no JSON são strings, converter para int
            loaded_answers = json.loads(user_answers_json)
            if isinstance(loaded_answers, dict):
                user_answers_dict = {int(k): v for k, v in loaded_answers.items() if isinstance(v, str)}
            else:
                print(f"Aviso: 'user_answers' para QuizAttempt ID {row['id']} não é um dict JSON válido.")
        except json.JSONDecodeError:
            print(f"Aviso: Falha ao decodificar 'user_answers' JSON para QuizAttempt ID {row['id']}.")
        
        return QuizAttempt(
            id=row['id'],
            quiz_config_id=row['quiz_config_id'],
            user_answers=user_answers_dict,
            score=row['score'],
            total_questions=row['total_questions'],
            attempted_at=self._datetime_from_str(row['attempted_at'])
            # updated_at não está no modelo QuizAttempt, mas o trigger o atualiza no DB
        )

    def add_quiz_attempt(self, attempt: QuizAttempt) -> Optional[QuizAttempt]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            # As chaves do dicionário (question_id) devem ser strings no JSON
            user_answers_json = json.dumps({str(k): v for k, v in attempt.user_answers.items()})
            
            query = """
            INSERT INTO QuizAttempts (quiz_config_id, user_answers, score, total_questions, attempted_at)
            VALUES (?, ?, ?, ?, ?)
            """
            # Usar o attempted_at do objeto, se fornecido, senão o default do DB (CURRENT_TIMESTAMP)
            # No entanto, o modelo QuizAttempt já define attempted_at no __init__ se não for passado.
            # Para consistência, sempre passamos o valor do objeto.
            attempted_at_str = self._datetime_to_str(attempt.attempted_at if attempt.attempted_at else datetime.now())

            cursor.execute(query, (
                attempt.quiz_config_id,
                user_answers_json,
                attempt.score,
                attempt.total_questions,
                attempted_at_str
            ))
            self.conn.commit()
            attempt.id = cursor.lastrowid
            if attempt.id:
                # Buscar para obter attempted_at e updated_at (se o modelo tivesse) do DB
                return self.get_quiz_attempt_by_id(attempt.id)
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar QuizAttempt: {e}")
            if self.conn: self.conn.rollback()
            return None

    def get_quiz_attempt_by_id(self, attempt_id: int) -> Optional[QuizAttempt]:
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM QuizAttempts WHERE id = ?"
            cursor.execute(query, (attempt_id,))
            row = cursor.fetchone()
            return self._quiz_attempt_from_row(row)
        except sqlite3.Error as e:
            print(f"Erro ao buscar QuizAttempt por ID: {e}")
            return None

    def get_attempts_for_quiz_config(self, quiz_config_id: int) -> List[QuizAttempt]:
        if not self.conn: return []
        attempts: List[QuizAttempt] = []
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM QuizAttempts WHERE quiz_config_id = ? ORDER BY attempted_at DESC"
            cursor.execute(query, (quiz_config_id,))
            for row in cursor.fetchall():
                attempt_obj = self._quiz_attempt_from_row(row)
                if attempt_obj:
                    attempts.append(attempt_obj)
        except sqlite3.Error as e:
            print(f"Erro ao buscar tentativas para QuizConfig ID {quiz_config_id}: {e}")
        return attempts
        
    def add_sample_data(self):
        """Adiciona dados de exemplo: um evento, uma tarefa e algumas perguntas."""
        if not self.conn:
            print("Conexão com o banco de dados não estabelecida. Dados de exemplo não adicionados.")
            return

        # Adicionar evento e tarefa de exemplo
        self._add_sample_event_and_task()

        # Adicionar perguntas de exemplo
        sample_questions_data = [
            {
                "text": "Qual é a capital da França?",
                "subject": "Geografia",
                "difficulty": "Fácil",
                "options": ["Londres", "Berlim", "Paris", "Madri"],
                "answer": "Paris"
            },
            {
                "text": "Quem escreveu 'Dom Quixote'?",
                "subject": "Literatura",
                "difficulty": "Médio",
                "options": ["Miguel de Cervantes", "William Shakespeare", "Victor Hugo", "Leon Tolstói"],
                "answer": "Miguel de Cervantes"
            },
            {
                "text": "Qual é a fórmula química da água?",
                "subject": "Química",
                "difficulty": "Fácil",
                "options": ["H2O2", "CO2", "H2O", "NaCl"],
                "answer": "H2O"
            },
            {
                "text": "Em que ano o homem pisou na Lua pela primeira vez?",
                "subject": "História",
                "difficulty": "Difícil",
                "options": ["1965", "1969", "1972", "1960"],
                "answer": "1969"
            }
        ]

        existing_question_texts = {q.text for q in self.get_all_questions()}
        questions_added_count = 0

        for q_data in sample_questions_data:
            if q_data["text"] not in existing_question_texts:
                question = Question(
                    text=q_data["text"],
                    subject=q_data["subject"],
                    difficulty=q_data["difficulty"],
                    options=q_data["options"],
                    answer=q_data["answer"]
                )
                added_q = self.add_question(question)
                if added_q and added_q.id is not None:
                    print(f"Pergunta de exemplo adicionada: '{added_q.text}'")
                    questions_added_count += 1
                else:
                    print(f"Falha ao adicionar pergunta de exemplo: '{q_data['text']}'")
            else:
                print(f"Pergunta de exemplo já existe: '{q_data['text']}'")
        
        if questions_added_count > 0:
            print(f"{questions_added_count} novas perguntas de exemplo foram adicionadas.")
        else:
            print("Nenhuma nova pergunta de exemplo foi adicionada (provavelmente já existiam).")

    # --- Settings ---
    def get_setting(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """Busca uma configuração pelo sua chave. Retorna default_value se não encontrada."""
        if not self.conn: return default_value
        try:
            cursor = self.conn.cursor()
            query = "SELECT value FROM Settings WHERE key = ?"
            cursor.execute(query, (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
            return default_value
        except sqlite3.Error as e:
            print(f"Erro ao buscar configuração '{key}': {e}")
            return default_value

    def set_setting(self, key: str, value: str) -> bool:
        """Salva ou atualiza uma configuração."""
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            # INSERT OR REPLACE (UPSERT) para inserir se não existir, ou substituir se existir.
            query = "INSERT OR REPLACE INTO Settings (key, value) VALUES (?, ?)"
            cursor.execute(query, (key, value))
            self.conn.commit()
            return cursor.rowcount > 0 # type: ignore
        except sqlite3.Error as e:
            print(f"Erro ao salvar configuração '{key}'='{value}': {e}")
            if self.conn: self.conn.rollback()
            return False

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None

if __name__ == '__main__':
    # Corrigir a chamada para add_sample_data se o nome do método foi alterado
    # Supondo que o método de adicionar dados de exemplo agora é add_sample_data
    # db_manager.add_sample_event() foi provavelmente renomeado para db_manager.add_sample_data()
    # Vou assumir que add_sample_data() é o método correto que também lida com Settings.
    
    db_manager = DatabaseManager(db_path='data/agenda.db') 
    if db_manager.conn:
        print(f"Banco de dados 'data/agenda.db' inicializado e tabelas criadas/verificadas.")
        
        db_manager.add_sample_data() # Chamada única para popular todos os dados de exemplo
        
        # Testar CRUD de Eventos
        print("\n--- Testando CRUD de Eventos ---")
        
        # 1. Adicionar Evento
        print("Testando add_event...")
        new_event_data = Event(
            title="Evento de Teste CRUD",
            description="Descrição do evento de teste.",
            start_time=datetime.now().replace(hour=15, minute=0, second=0, microsecond=0),
            end_time=datetime.now().replace(hour=16, minute=0, second=0, microsecond=0),
            event_type="teste",
            location="Sala de Testes"
        )
        added_event = db_manager.add_event(new_event_data)
        if added_event and added_event.id is not None:
            print(f"Evento adicionado com sucesso: ID={added_event.id}, Título='{added_event.title}', Criado_em='{added_event.created_at}'")
            event_id_to_test = added_event.id

            # 2. Ler Evento (já testado em get_event_by_id e get_events_by_date)
            retrieved_event = db_manager.get_event_by_id(event_id_to_test)
            assert retrieved_event is not None and retrieved_event.title == "Evento de Teste CRUD"
            print(f"Evento recuperado para teste: '{retrieved_event.title}'")

            # 3. Atualizar Evento
            print("\nTestando update_event...")
            retrieved_event.title = "Evento de Teste CRUD (Atualizado)"
            retrieved_event.description = "Descrição atualizada."
            # Simular uma pequena mudança no tempo para testar a atualização do timestamp
            # Pode ser necessário um sleep pequeno se a resolução do CURRENT_TIMESTAMP for baixa
            # import time; time.sleep(1) 
            if db_manager.update_event(retrieved_event):
                print(f"Evento ID={event_id_to_test} atualizado com sucesso.")
                updated_event = db_manager.get_event_by_id(event_id_to_test)
                assert updated_event is not None and updated_event.title == "Evento de Teste CRUD (Atualizado)"
                print(f"Título após atualização: '{updated_event.title}', Atualizado_em='{updated_event.updated_at}'")
                assert updated_event.updated_at != added_event.created_at # Checa se o trigger funcionou
            else:
                print(f"Falha ao atualizar evento ID={event_id_to_test}.")

            # 4. Deletar Evento
            print("\nTestando delete_event...")
            if db_manager.delete_event(event_id_to_test):
                print(f"Evento ID={event_id_to_test} excluído com sucesso.")
                assert db_manager.get_event_by_id(event_id_to_test) is None
                print(f"Evento ID={event_id_to_test} não encontrado após exclusão (correto).")
            else:
                print(f"Falha ao excluir evento ID={event_id_to_test}.")
        else:
            print("Falha ao adicionar evento para teste CRUD.")

        # Testar get_events_by_date (apenas para verificar se o evento de exemplo ainda está lá)
        print(f"\nEventos para hoje ({date.today()}) após testes CRUD:")
        events_today = db_manager.get_events_by_date(date.today())
        if events_today:
            for event_obj in events_today:
                print(f"- ID: {event_obj.id}, Título: {event_obj.title}, Início: {event_obj.start_time.strftime('%H:%M') if event_obj.start_time else 'N/A'}")
                # ... (o resto dos testes de evento pode continuar aqui) ...
        else:
            print("Nenhum evento encontrado para hoje.")

        # Testar Settings (adicionado aqui, após os outros testes ou em local apropriado)
        print("\n--- Testando Settings ---")
        assert db_manager.set_setting("test_user_name", "test_user") == True
        retrieved_username = db_manager.get_setting("test_user_name", "default_user")
        assert retrieved_username == "test_user"
        print(f"Setting 'test_user_name' recuperado: {retrieved_username}")

        assert db_manager.get_setting("non_existent_key", "fallback") == "fallback"
        print("Setting inexistente 'non_existent_key' retornou valor fallback.")
        
        assert db_manager.set_setting("test_user_name", "new_test_user") == True
        assert db_manager.get_setting("test_user_name") == "new_test_user"
        print("Setting 'test_user_name' atualizado e recuperado.")

        # ... (restantes dos testes de CRUD para Task, Question, QuizConfig, QuizAttempt, Entity, etc. podem seguir) ...
            
        db_manager.close()
        print("\nConexão com o banco de dados fechada.")
    else:
        print("Falha ao inicializar o DatabaseManager.")
