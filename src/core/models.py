from datetime import datetime
from typing import List, Optional, Dict, Any

class Entity:
    def __init__(self,
                 name: str,
                 type: str,
                 details_json: Optional[Dict[str, Any]] = None,
                 id: Optional[int] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.type = type
        self.details_json = details_json if details_json is not None else {}
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"<Entity(id={self.id}, name='{self.name}', type='{self.type}')>"

class Event:
    def __init__(self,
                 title: str,
                 start_time: datetime,
                 event_type: str,
                 id: Optional[int] = None,
                 description: Optional[str] = None,
                 end_time: Optional[datetime] = None,
                 location: Optional[str] = None,
                 recurrence_rule: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.event_type = event_type
        self.location = location
        self.recurrence_rule = recurrence_rule
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', start_time='{self.start_time}')>"

class Task:
    def __init__(self,
                 title: str,
                 id: Optional[int] = None,
                 description: Optional[str] = None,
                 priority: str = 'Medium',
                 due_date: Optional[datetime] = None,
                 status: str = 'Open',
                 parent_event_id: Optional[int] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.status = status
        self.parent_event_id = parent_event_id
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class Question:
    def __init__(self,
                 text: str,
                 answer: str, # Resposta correta (texto da opção)
                 id: Optional[int] = None,
                 subject: Optional[str] = None,
                 difficulty: Optional[str] = None, # Ex: 'Fácil', 'Médio', 'Difícil'
                 options: Optional[List[str]] = None, # Lista de opções de resposta
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.text = text
        self.subject = subject
        self.difficulty = difficulty
        self.options = options if options is not None else []
        self.answer = answer
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"<Question(id={self.id}, text='{self.text[:50]}...', subject='{self.subject}')>"


class QuizConfig:
    def __init__(self,
                 question_ids: List[int],
                 id: Optional[int] = None,
                 name: Optional[str] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.question_ids = question_ids if question_ids is not None else []
        self.created_at = created_at

    def __repr__(self):
        return f"<QuizConfig(id={self.id}, name='{self.name}', num_questions={len(self.question_ids)})>"

class QuizAttempt:
    def __init__(self,
                 quiz_config_id: int,
                 user_answers: Dict[int, str], # question_id: answer_text
                 score: int,
                 total_questions: int,
                 id: Optional[int] = None,
                 attempted_at: Optional[datetime] = None):
        self.id = id
        self.quiz_config_id = quiz_config_id
        self.user_answers = user_answers if user_answers is not None else {}
        self.score = score
        self.total_questions = total_questions
        self.attempted_at = attempted_at if attempted_at is not None else datetime.now()

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, config_id={self.quiz_config_id}, score={self.score}/{self.total_questions})>"


class LessonPlanFile:
    def __init__(self,
                 lesson_plan_id: int,
                 file_name: str, # Nome original do arquivo
                 file_path: str, # Caminho no sistema de arquivos onde o arquivo está armazenado
                 id: Optional[int] = None,
                 uploaded_at: Optional[datetime] = None):
        self.id = id
        self.lesson_plan_id = lesson_plan_id
        self.file_name = file_name
        self.file_path = file_path
        self.uploaded_at = uploaded_at if uploaded_at is not None else datetime.now()

    def __repr__(self):
        return f"<LessonPlanFile(id={self.id}, name='{self.file_name}', lesson_plan_id={self.lesson_plan_id})>"

class LessonPlanLink:
    def __init__(self,
                 lesson_plan_id: int,
                 url: str,
                 id: Optional[int] = None,
                 title: Optional[str] = None, # Título opcional para o link
                 added_at: Optional[datetime] = None):
        self.id = id
        self.lesson_plan_id = lesson_plan_id
        self.url = url
        self.title = title
        self.added_at = added_at if added_at is not None else datetime.now()

    def __repr__(self):
        return f"<LessonPlanLink(id={self.id}, url='{self.url}', lesson_plan_id={self.lesson_plan_id})>"

class LessonPlan:
    def __init__(self,
                 title: str,
                 teacher_id: int, # ID do professor que criou o plano
                 id: Optional[int] = None,
                 lesson_date: Optional[datetime] = None,
                 # Turmas associadas: Lista de IDs das turmas.
                 # A gestão da tabela de associação (M-M) será feita no database_manager.
                 class_ids: Optional[List[int]] = None,
                 objectives: Optional[str] = None, # Campo de texto rico
                 program_content: Optional[str] = None, # Campo de texto rico
                 methodology: Optional[str] = None, # Campo de texto rico
                 resources_text: Optional[str] = None, # Campo de texto rico para descrição geral de recursos
                 assessment_method: Optional[str] = None, # Campo de texto rico
                 # Arquivos e links serão armazenados em tabelas separadas e ligados pelo lesson_plan_id
                 # Estes campos podem ser populados após carregar o plano principal.
                 files: Optional[List[LessonPlanFile]] = None,
                 links: Optional[List[LessonPlanLink]] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.teacher_id = teacher_id
        self.lesson_date = lesson_date
        self.class_ids = class_ids if class_ids is not None else []
        self.objectives = objectives
        self.program_content = program_content
        self.methodology = methodology
        self.resources_text = resources_text
        self.assessment_method = assessment_method
        self.files = files if files is not None else [] # Estes são objetos, não apenas IDs
        self.links = links if links is not None else [] # Estes são objetos, não apenas IDs
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"<LessonPlan(id={self.id}, title='{self.title}', teacher_id={self.teacher_id})>"


if __name__ == '__main__':
    # Exemplos de uso (apenas para teste rápido e demonstração)
    
    # Criando uma Entidade
    entity1 = Entity(name="Prof. Silva", type="professor", details_json={"department": "Computer Science", "office": "Room 101"})
    print(entity1)
    print(entity1.details_json)

    # Criando um Evento
    event_start = datetime(2024, 8, 15, 14, 0, 0)
    event_end = datetime(2024, 8, 15, 16, 0, 0)
    event1 = Event(title="Aula de Python Avançado",
                   start_time=event_start,
                   end_time=event_end,
                   event_type="aula",
                   location="Sala 3B",
                   description="Discussão sobre metaprogramação e design patterns.")
    print(event1)

    # Criando uma Tarefa
    task_due_date = datetime(2024, 8, 20, 23, 59, 59)
    task1 = Task(title="Preparar slides para aula",
                 description="Cobrir os tópicos de geradores e decoradores.",
                 priority="High",
                 due_date=task_due_date,
                 parent_event_id=event1.id if event1.id else None) # Supondo que o evento já teria um ID se viesse do DB
    print(task1)

    task2 = Task(title="Revisar PRs", status="In Progress")
    print(task2)

    # Exemplo de entidade sem detalhes
    entity2 = Entity(name="Monitor João", type="aluno")
    print(entity2)
    print(entity2.details_json) # Deve ser {}

    # Exemplo de evento sem campos opcionais
    simple_event_start = datetime.now()
    simple_event = Event(title="Reunião Rápida", start_time=simple_event_start, event_type="reuniao")
    print(simple_event)
    
    # Criando uma Pergunta
    question1_options = ["Paris", "Londres", "Berlim", "Madri"]
    question1 = Question(text="Qual é a capital da França?", 
                         subject="Geografia", 
                         difficulty="Fácil", 
                         options=question1_options, 
                         answer="Paris")
    print(question1)
    print(f"  Opções: {question1.options}")
    print(f"  Resposta: {question1.answer}")

    question2 = Question(text="Quem escreveu 'Dom Quixote'?",
                         subject="Literatura",
                         difficulty="Médio",
                         options=["Miguel de Cervantes", "William Shakespeare", "Victor Hugo"],
                         answer="Miguel de Cervantes")
    print(question2)

    # Criando uma Configuração de Quiz
    quiz_config1 = QuizConfig(name="Quiz Rápido de Geografia", question_ids=[1, question1.id if question1.id else 2])
    print(quiz_config1)

    # Criando uma Tentativa de Quiz
    attempt1_answers = {1: "Paris", (question1.id if question1.id else 2): "Errado"}
    quiz_attempt1 = QuizAttempt(quiz_config_id=(quiz_config1.id if quiz_config1.id else 1),
                                user_answers=attempt1_answers,
                                score=1,
                                total_questions=2)
    print(quiz_attempt1)
    print(f"  Respostas: {quiz_attempt1.user_answers}")
