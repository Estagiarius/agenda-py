import unittest
import os
import json
from datetime import date, datetime, timedelta

from src.core.database_manager import DatabaseManager
from src.core.models import Event, Entity, ClassRegistry, AttendanceRecord

# Helper function to get current datetime without microseconds for comparisons
def now_no_ms():
    return datetime.now().replace(microsecond=0)

class TestDatabaseManagerClassRegistry(unittest.TestCase):

    def setUp(self):
        """Set up a new in-memory database for each test."""
        self.db_manager = DatabaseManager(db_path=':memory:')
        # The DatabaseManager calls _create_tables() in its __init__,
        # so tables including ClassRegistries should be created.

        # Helper data
        self.teacher1 = Entity(name="Prof. Testador", type="teacher")
        self.teacher1 = self.db_manager.add_entity(self.teacher1)

        self.student1 = Entity(name="Aluno Um", type="student")
        self.student1 = self.db_manager.add_entity(self.student1)
        self.student2 = Entity(name="Aluna Dois", type="student")
        self.student2 = self.db_manager.add_entity(self.student2)

        self.event1_today = Event(title="Aula de Testes 1", event_type="aula", start_time=now_no_ms().replace(hour=9))
        self.event1_today = self.db_manager.add_event(self.event1_today)
        self.db_manager.link_entity_to_event(self.event1_today.id, self.teacher1.id, "teacher")
        self.db_manager.link_entity_to_event(self.event1_today.id, self.student1.id, "student")
        self.db_manager.link_entity_to_event(self.event1_today.id, self.student2.id, "student")

        self.event2_yesterday = Event(title="Aula de Testes 2", event_type="aula", start_time=(now_no_ms() - timedelta(days=1)).replace(hour=10))
        self.event2_yesterday = self.db_manager.add_event(self.event2_yesterday)
        self.db_manager.link_entity_to_event(self.event2_yesterday.id, self.teacher1.id, "teacher")
        self.db_manager.link_entity_to_event(self.event2_yesterday.id, self.student1.id, "student")


    def tearDown(self):
        """Close the database connection after each test."""
        self.db_manager.close()

    def test_create_class_registry_table(self):
        """Test if the ClassRegistries table is created."""
        # Check by trying to insert and select data, or query schema
        # For simplicity, we assume if other tests pass, table was created.
        # A more direct check:
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ClassRegistries';")
        self.assertIsNotNone(cursor.fetchone(), "ClassRegistries table should exist.")

    def test_save_and_get_class_registry(self):
        """Test saving a new class registry and retrieving it."""
        today = date.today()
        attendance_records_initial: List[AttendanceRecord] = [
            {"student_id": self.student1.id, "status": "Presente", "student_name": self.student1.name},
            {"student_id": self.student2.id, "status": "Ausente", "student_name": self.student2.name}
        ]

        registry_to_save = ClassRegistry(
            event_id=self.event1_today.id,
            class_date=today,
            content_taught="Conteúdo inicial da aula.",
            attendance_records=attendance_records_initial
        )

        saved_registry = self.db_manager.save_class_registry(registry_to_save)

        self.assertIsNotNone(saved_registry)
        self.assertIsNotNone(saved_registry.id, "Saved registry should have an ID.")
        self.assertEqual(saved_registry.event_id, self.event1_today.id)
        self.assertEqual(saved_registry.class_date, today)
        self.assertEqual(saved_registry.content_taught, "Conteúdo inicial da aula.")
        self.assertEqual(len(saved_registry.attendance_records), 2)
        self.assertEqual(saved_registry.attendance_records[0]['status'], "Presente")
        self.assertIsNotNone(saved_registry.created_at)
        self.assertIsNotNone(saved_registry.updated_at)

        # Test get_class_registry
        fetched_registry = self.db_manager.get_class_registry(self.event1_today.id, today)
        self.assertIsNotNone(fetched_registry)
        self.assertEqual(fetched_registry.id, saved_registry.id)
        self.assertEqual(fetched_registry.content_taught, "Conteúdo inicial da aula.")
        self.assertEqual(fetched_registry.attendance_records[1]['student_id'], self.student2.id)

        # Test get_class_registry_by_id
        fetched_by_id = self.db_manager.get_class_registry_by_id(saved_registry.id)
        self.assertIsNotNone(fetched_by_id)
        self.assertEqual(fetched_by_id.content_taught, "Conteúdo inicial da aula.")

        # Test that created_at and updated_at are datetime objects
        self.assertIsInstance(fetched_by_id.created_at, datetime)
        self.assertIsInstance(fetched_by_id.updated_at, datetime)


    def test_update_class_registry(self):
        """Test updating an existing class registry."""
        today = date.today()
        initial_content = "Conteúdo antes da atualização."
        registry_to_save = ClassRegistry(
            event_id=self.event1_today.id,
            class_date=today,
            content_taught=initial_content,
            attendance_records=[]
        )
        saved_registry = self.db_manager.save_class_registry(registry_to_save)
        self.assertIsNotNone(saved_registry)
        original_updated_at = saved_registry.updated_at

        # Wait a moment to ensure updated_at timestamp can change
        # In a real scenario with a fast DB, this might not be enough, but for :memory: it's often fine.
        # Consider mocking datetime.now if precise control is needed.
        try:
            import time
            time.sleep(0.01)
        except ImportError: pass


        updated_content = "Conteúdo foi atualizado."
        updated_attendance: List[AttendanceRecord] = [
            {"student_id": self.student1.id, "status": "Atrasado", "student_name": self.student1.name}
        ]

        # To update, use the ID of the saved_registry
        registry_to_update = ClassRegistry(
            id=saved_registry.id,
            event_id=self.event1_today.id, # event_id and class_date still needed for save logic if it uses them for lookup
            class_date=today,
            content_taught=updated_content,
            attendance_records=updated_attendance
        )

        updated_registry = self.db_manager.save_class_registry(registry_to_update)
        self.assertIsNotNone(updated_registry)
        self.assertEqual(updated_registry.id, saved_registry.id)
        self.assertEqual(updated_registry.content_taught, updated_content)
        self.assertEqual(len(updated_registry.attendance_records), 1)
        self.assertEqual(updated_registry.attendance_records[0]['status'], "Atrasado")

        # Check if updated_at timestamp has changed due to trigger
        # Allow for slight timing discrepancies if not mocking time
        self.assertTrue(updated_registry.updated_at > original_updated_at,
                        f"Updated_at not changed: new {updated_registry.updated_at} vs old {original_updated_at}")

    def test_save_class_registry_upsert_behavior(self):
        """Test ON CONFLICT DO UPDATE behavior for unique (event_id, class_date)."""
        today = date.today()
        registry1 = ClassRegistry(
            event_id=self.event1_today.id,
            class_date=today,
            content_taught="Primeira versão",
            attendance_records=[]
        )
        saved1 = self.db_manager.save_class_registry(registry1)
        self.assertIsNotNone(saved1)
        self.assertIsNotNone(saved1.id)

        registry2_upsert = ClassRegistry(
            # No ID specified, should trigger ON CONFLICT based on event_id, class_date
            event_id=self.event1_today.id,
            class_date=today,
            content_taught="Segunda versão (UPSERT)",
            attendance_records=[{"student_id": self.student1.id, "status": "Presente"}]
        )

        upserted_registry = self.db_manager.save_class_registry(registry2_upsert)
        self.assertIsNotNone(upserted_registry)
        self.assertEqual(upserted_registry.id, saved1.id, "UPSERT should update existing row, keeping ID.")
        self.assertEqual(upserted_registry.content_taught, "Segunda versão (UPSERT)")
        self.assertEqual(len(upserted_registry.attendance_records), 1)


    def test_get_classes_for_teacher_today(self):
        """Test fetching classes for a teacher scheduled for today."""
        # event1_today is already set up for self.teacher1 today.
        # Add another event for today for a different teacher
        teacher2 = self.db_manager.add_entity(Entity(name="Outro Prof", type="teacher"))
        event_other_teacher = self.db_manager.add_event(
            Event(title="Aula Outro Prof", event_type="aula", start_time=now_no_ms().replace(hour=14))
        )
        self.db_manager.link_entity_to_event(event_other_teacher.id, teacher2.id, "teacher")

        # Add an event for self.teacher1 but not of type 'aula'
        non_aula_event = self.db_manager.add_event(
            Event(title="Reunião Teste", event_type="reuniao", start_time=now_no_ms().replace(hour=15))
        )
        self.db_manager.link_entity_to_event(non_aula_event.id, self.teacher1.id, "teacher")

        classes_for_teacher1 = self.db_manager.get_classes_for_teacher_today(self.teacher1.id)
        self.assertEqual(len(classes_for_teacher1), 1)
        self.assertEqual(classes_for_teacher1[0].id, self.event1_today.id)
        self.assertEqual(classes_for_teacher1[0].title, "Aula de Testes 1")

        classes_for_teacher2 = self.db_manager.get_classes_for_teacher_today(teacher2.id)
        self.assertEqual(len(classes_for_teacher2), 1)
        self.assertEqual(classes_for_teacher2[0].id, event_other_teacher.id)

        # Test with a teacher ID that has no classes today
        teacher3_no_classes = self.db_manager.add_entity(Entity(name="Prof Sem Aulas", type="teacher"))
        self.assertEqual(len(self.db_manager.get_classes_for_teacher_today(teacher3_no_classes.id)), 0)


    def test_get_students_for_class(self):
        """Test fetching students linked to a specific class (event)."""
        students = self.db_manager.get_students_for_class(self.event1_today.id)
        self.assertEqual(len(students), 2)
        student_ids = {s.id for s in students}
        self.assertIn(self.student1.id, student_ids)
        self.assertIn(self.student2.id, student_ids)

        # Test for an event with no students
        event_no_students = self.db_manager.add_event(
            Event(title="Aula Vazia", event_type="aula", start_time=now_no_ms())
        )
        self.db_manager.link_entity_to_event(event_no_students.id, self.teacher1.id, "teacher")
        students_empty_class = self.db_manager.get_students_for_class(event_no_students.id)
        self.assertEqual(len(students_empty_class), 0)

        # Test for an invalid event_id (should not error, return empty list)
        self.assertEqual(len(self.db_manager.get_students_for_class(99999)), 0)


    def test_get_class_registries_for_date(self):
        """Test fetching class registries for a teacher on a specific date."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Registry for event1_today (today)
        reg1_content = "Conteúdo da Aula de Hoje"
        self.db_manager.save_class_registry(ClassRegistry(
            event_id=self.event1_today.id, class_date=today, content_taught=reg1_content, attendance_records=[]
        ))

        # Registry for event2_yesterday (yesterday)
        reg2_content = "Conteúdo da Aula de Ontem"
        self.db_manager.save_class_registry(ClassRegistry(
            event_id=self.event2_yesterday.id, class_date=yesterday, content_taught=reg2_content, attendance_records=[]
        ))

        # Add another event for today for teacher1, but without a registry
        event3_today_no_reg = Event(title="Aula Extra Hoje", event_type="aula", start_time=now_no_ms().replace(hour=16))
        event3_today_no_reg = self.db_manager.add_event(event3_today_no_reg)
        self.db_manager.link_entity_to_event(event3_today_no_reg.id, self.teacher1.id, "teacher")


        # --- Test for today ---
        results_today = self.db_manager.get_class_registries_for_date(self.teacher1.id, today)
        self.assertEqual(len(results_today), 2, "Should have two classes for teacher1 today")

        found_event1 = False
        found_event3 = False
        for event, registry in results_today:
            if event.id == self.event1_today.id:
                found_event1 = True
                self.assertIsNotNone(registry, "Registry for event1_today should exist.")
                self.assertEqual(registry.content_taught, reg1_content)
            elif event.id == event3_today_no_reg.id:
                found_event3 = True
                self.assertIsNone(registry, "Registry for event3_today_no_reg should NOT exist.")
        self.assertTrue(found_event1, "Event 1 today was not found in results.")
        self.assertTrue(found_event3, "Event 3 today (no reg) was not found in results.")


        # --- Test for yesterday ---
        results_yesterday = self.db_manager.get_class_registries_for_date(self.teacher1.id, yesterday)
        self.assertEqual(len(results_yesterday), 1, "Should have one class for teacher1 yesterday")
        event_y, registry_y = results_yesterday[0]
        self.assertEqual(event_y.id, self.event2_yesterday.id)
        self.assertIsNotNone(registry_y)
        self.assertEqual(registry_y.content_taught, reg2_content)

        # --- Test for a date with no classes ---
        two_days_ago = today - timedelta(days=2)
        results_other_day = self.db_manager.get_class_registries_for_date(self.teacher1.id, two_days_ago)
        self.assertEqual(len(results_other_day), 0)


if __name__ == '__main__':
    unittest.main()
