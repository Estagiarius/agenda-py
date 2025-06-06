import unittest
from datetime import date, datetime
from typing import List, cast

from src.core.models import ClassRegistry, AttendanceRecord, Event # Assuming Event might be needed for context

class TestClassRegistry(unittest.TestCase):

    def test_class_registry_initialization_defaults(self):
        """Test ClassRegistry initialization with minimal required fields."""
        event_id = 1
        class_dt = date(2023, 10, 26)
        attendance: List[AttendanceRecord] = []

        registry = ClassRegistry(
            event_id=event_id,
            class_date=class_dt,
            attendance_records=attendance
        )

        self.assertIsNone(registry.id)
        self.assertEqual(registry.event_id, event_id)
        self.assertEqual(registry.class_date, class_dt)
        self.assertEqual(registry.attendance_records, attendance)
        self.assertIsNone(registry.content_taught)
        self.assertIsNone(registry.created_at)
        self.assertIsNone(registry.updated_at)
        self.assertEqual(registry.attendance_records, [])


    def test_class_registry_initialization_all_fields(self):
        """Test ClassRegistry initialization with all fields provided."""
        registry_id = 100
        event_id = 2
        class_dt = date(2023, 10, 27)
        content = "<p>Conteúdo da aula.</p>"
        created_timestamp = datetime(2023, 10, 27, 10, 0, 0)
        updated_timestamp = datetime(2023, 10, 27, 11, 0, 0)

        attendance_list: List[AttendanceRecord] = [
            AttendanceRecord(student_id=1, status="Presente", student_name="Aluno A"),
            AttendanceRecord(student_id=2, status="Ausente", student_name="Aluno B")
        ]
        # If AttendanceRecord is a TypedDict, direct casting might be needed for type checkers
        # For runtime, it's a dict.

        registry = ClassRegistry(
            id=registry_id,
            event_id=event_id,
            class_date=class_dt,
            content_taught=content,
            attendance_records=attendance_list,
            created_at=created_timestamp,
            updated_at=updated_timestamp
        )

        self.assertEqual(registry.id, registry_id)
        self.assertEqual(registry.event_id, event_id)
        self.assertEqual(registry.class_date, class_dt)
        self.assertEqual(registry.content_taught, content)
        self.assertEqual(len(registry.attendance_records), 2)
        self.assertEqual(registry.attendance_records[0]['student_id'], 1)
        self.assertEqual(registry.attendance_records[0]['status'], "Presente")
        self.assertEqual(registry.attendance_records[1]['student_name'], "Aluno B")
        self.assertEqual(registry.created_at, created_timestamp)
        self.assertEqual(registry.updated_at, updated_timestamp)

    def test_class_registry_repr(self):
        """Test the __repr__ method of ClassRegistry."""
        registry = ClassRegistry(
            id=1,
            event_id=10,
            class_date=date(2023, 1, 1),
            attendance_records=[]
        )
        expected_repr = "<ClassRegistry(id=1, event_id=10, class_date='2023-01-01', records=0)>"
        self.assertEqual(repr(registry), expected_repr)

        registry_no_id = ClassRegistry(
            event_id=11,
            class_date=date(2023, 1, 2),
            attendance_records=[AttendanceRecord(student_id=1, status="Presente")]
        )
        expected_repr_no_id = "<ClassRegistry(id=None, event_id=11, class_date='2023-01-02', records=1)>"
        self.assertEqual(repr(registry_no_id), expected_repr_no_id)


class TestAttendanceRecord(unittest.TestCase):

    def test_attendance_record_creation(self):
        """Test creating AttendanceRecord instances (as dicts)."""
        record1: AttendanceRecord = {
            "student_id": 1,
            "status": "Presente",
            "student_name": "João Silva"
        }
        self.assertEqual(record1['student_id'], 1)
        self.assertEqual(record1['status'], "Presente")
        self.assertEqual(record1['student_name'], "João Silva")

        record2: AttendanceRecord = {
            "student_id": 2,
            "status": "Ausente"
            # student_name is Optional
        }
        self.assertEqual(record2['student_id'], 2)
        self.assertEqual(record2['status'], "Ausente")
        self.assertNotIn('student_name', record2) # Or self.assertIsNone(record2.get('student_name')) if it could be None

        # Example of how it might be used in ClassRegistry
        class_reg = ClassRegistry(event_id=1, class_date=date.today(), attendance_records=[record1, record2])
        self.assertEqual(len(class_reg.attendance_records), 2)
        self.assertEqual(class_reg.attendance_records[1]['status'], "Ausente")


if __name__ == '__main__':
    unittest.main()
