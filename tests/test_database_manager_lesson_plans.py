import unittest
import os
import sys
from datetime import datetime

# Add src directory to sys.path to allow direct import of modules
# This might need adjustment based on the actual project structure and how tests are run
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_dir)

from core.database_manager import DatabaseManager
from core.models import LessonPlan, LessonPlanFile, LessonPlanLink, Entity

class TestDatabaseManagerLessonPlans(unittest.TestCase):

    def setUp(self):
        """Set up a new in-memory database for each test."""
        self.db_manager = DatabaseManager(db_path=':memory:')
        # Ensure tables are created (DatabaseManager's __init__ should do this)
        # We might need to pre-populate some data, like Entities for classes/teachers if necessary
        self._setup_initial_entities()

    def _setup_initial_entities(self):
        """Helper to create some initial entities like teachers and classes."""
        # Example: Teacher Entity (assuming teacher_id in LessonPlan refers to an Entity's ID)
        self.teacher1 = self.db_manager.add_entity(Entity(name="Prof. Testador", type="teacher"))
        self.teacher2 = self.db_manager.add_entity(Entity(name="Prof. Outro", type="teacher"))

        # Example: Class Entities
        self.class1 = self.db_manager.add_entity(Entity(name="Turma Teste 101", type="turma"))
        self.class2 = self.db_manager.add_entity(Entity(name="Turma Teste 102", type="turma"))
        self.class3 = self.db_manager.add_entity(Entity(name="Turma Teste 201", type="turma"))

    def tearDown(self):
        """Close the database connection after each test."""
        if self.db_manager:
            self.db_manager.close()

    def test_dummy(self): # A dummy test to ensure the setup works
        self.assertTrue(True)

    def test_add_lesson_plan_and_get_by_id(self):
        """Test adding a complete lesson plan and retrieving it by ID."""
        self.assertIsNotNone(self.teacher1.id, "Teacher1 ID should not be None")
        self.assertIsNotNone(self.class1.id, "Class1 ID should not be None")
        self.assertIsNotNone(self.class2.id, "Class2 ID should not be None")

        original_files = [
            LessonPlanFile(lesson_plan_id=0, file_name="test_file.pdf", file_path="/fake/path/test_file.pdf", uploaded_at=datetime.now()),
            LessonPlanFile(lesson_plan_id=0, file_name="another_file.docx", file_path="/fake/path/another_file.docx", uploaded_at=datetime.now())
        ]
        original_links = [
            LessonPlanLink(lesson_plan_id=0, url="https://example.com", title="Example Site", added_at=datetime.now()),
            LessonPlanLink(lesson_plan_id=0, url="https://test.org", title="Test Org", added_at=datetime.now())
        ]
        original_class_ids = [self.class1.id, self.class2.id]
        lesson_date_val = datetime(2024, 1, 15, 10, 0, 0)

        new_plan_data = LessonPlan(
            teacher_id=self.teacher1.id,
            title="Meu Plano de Teste Completo",
            lesson_date=lesson_date_val,
            objectives="<p>Objetivos HTML do Plano</p>",
            program_content="<p>Conteúdo Programático em HTML</p>",
            methodology="<p>Metodologia Detalhada em HTML</p>",
            resources_text="<p>Recursos Textuais Adicionais em HTML</p>",
            assessment_method="<p>Método de Avaliação em HTML</p>",
            class_ids=original_class_ids,
            files=original_files,
            links=original_links,
            created_at=datetime.now(), # Should be handled by DB manager if None, but good to set
            updated_at=datetime.now()  # Should be handled by DB manager if None
        )

        added_plan = self.db_manager.add_lesson_plan(new_plan_data)
        self.assertIsNotNone(added_plan, "add_lesson_plan should return the added plan.")
        self.assertIsNotNone(added_plan.id, "Added plan ID should not be None.")
        self.assertTrue(added_plan.id > 0, "Added plan ID should be positive.")

        # Fetch the plan
        fetched_plan = self.db_manager.get_lesson_plan_by_id(added_plan.id, self.teacher1.id)
        self.assertIsNotNone(fetched_plan, "get_lesson_plan_by_id should retrieve the plan.")

        # Assertions
        self.assertEqual(fetched_plan.title, new_plan_data.title)
        self.assertEqual(fetched_plan.teacher_id, self.teacher1.id)
        self.assertEqual(fetched_plan.objectives, new_plan_data.objectives)
        self.assertEqual(fetched_plan.program_content, new_plan_data.program_content)
        self.assertEqual(fetched_plan.methodology, new_plan_data.methodology)
        self.assertEqual(fetched_plan.resources_text, new_plan_data.resources_text)
        self.assertEqual(fetched_plan.assessment_method, new_plan_data.assessment_method)

        # Compare dates (ensure they are both datetime objects or consistent string representations)
        # The db_manager's _datetime_from_str and _datetime_to_str should ensure consistency
        self.assertEqual(fetched_plan.lesson_date, lesson_date_val)

        self.assertListEqual(sorted(fetched_plan.class_ids), sorted(original_class_ids))

        self.assertEqual(len(fetched_plan.files), len(original_files))
        if fetched_plan.files and original_files:
            # Sort by file_name for consistent comparison if order is not guaranteed
            fetched_plan.files.sort(key=lambda f: f.file_name)
            original_files.sort(key=lambda f: f.file_name)
            for i in range(len(original_files)):
                self.assertEqual(fetched_plan.files[i].file_name, original_files[i].file_name)
                self.assertEqual(fetched_plan.files[i].file_path, original_files[i].file_path)
                self.assertIsNotNone(fetched_plan.files[i].id)
                self.assertEqual(fetched_plan.files[i].lesson_plan_id, fetched_plan.id)
                # self.assertEqual(fetched_plan.files[i].uploaded_at, original_files[i].uploaded_at) # Timestamps can be tricky due to DB precision

        self.assertEqual(len(fetched_plan.links), len(original_links))
        if fetched_plan.links and original_links:
            # Sort by URL for consistent comparison
            fetched_plan.links.sort(key=lambda l: l.url)
            original_links.sort(key=lambda l: l.url)
            for i in range(len(original_links)):
                self.assertEqual(fetched_plan.links[i].url, original_links[i].url)
                self.assertEqual(fetched_plan.links[i].title, original_links[i].title)
                self.assertIsNotNone(fetched_plan.links[i].id)
                self.assertEqual(fetched_plan.links[i].lesson_plan_id, fetched_plan.id)
                # self.assertEqual(fetched_plan.links[i].added_at, original_links[i].added_at) # Timestamps

        # Test fetching with incorrect teacher_id
        fetched_should_be_none = self.db_manager.get_lesson_plan_by_id(added_plan.id, self.teacher2.id)
        self.assertIsNone(fetched_should_be_none, "Plan should not be fetched with incorrect teacher_id.")

    def test_get_lesson_plans_by_teacher(self):
        """Test retrieving lesson plans with various filters for a teacher."""
        # Add plans for teacher1
        lp1_t1 = self.db_manager.add_lesson_plan(LessonPlan(teacher_id=self.teacher1.id, title="Plan Alpha", class_ids=[self.class1.id]))
        lp2_t1 = self.db_manager.add_lesson_plan(LessonPlan(teacher_id=self.teacher1.id, title="Python Plan Beta", class_ids=[self.class2.id]))
        lp3_t1 = self.db_manager.add_lesson_plan(LessonPlan(teacher_id=self.teacher1.id, title="Python Plan Gamma", class_ids=[self.class1.id, self.class2.id]))

        # Add plan for teacher2
        self.db_manager.add_lesson_plan(LessonPlan(teacher_id=self.teacher2.id, title="Plan Omega", class_ids=[self.class3.id]))

        # Test: Get all plans for teacher1
        plans_t1 = self.db_manager.get_lesson_plans_by_teacher(self.teacher1.id)
        self.assertEqual(len(plans_t1), 3)
        for plan in plans_t1:
            self.assertEqual(plan.teacher_id, self.teacher1.id)

        # Test: Filter by associated_class_id for teacher1
        plans_t1_class1 = self.db_manager.get_lesson_plans_by_teacher(self.teacher1.id, associated_class_id=self.class1.id)
        self.assertEqual(len(plans_t1_class1), 2)
        retrieved_ids_class1 = sorted([p.id for p in plans_t1_class1])
        expected_ids_class1 = sorted([lp1_t1.id, lp3_t1.id])
        self.assertListEqual(retrieved_ids_class1, expected_ids_class1)

        # Test: Filter by title_keyword for teacher1
        plans_t1_keyword_python = self.db_manager.get_lesson_plans_by_teacher(self.teacher1.id, title_keyword="Python Plan")
        self.assertEqual(len(plans_t1_keyword_python), 2)
        retrieved_ids_keyword = sorted([p.id for p in plans_t1_keyword_python])
        expected_ids_keyword = sorted([lp2_t1.id, lp3_t1.id])
        self.assertListEqual(retrieved_ids_keyword, expected_ids_keyword)

        plans_t1_keyword_alpha = self.db_manager.get_lesson_plans_by_teacher(self.teacher1.id, title_keyword="Alpha")
        self.assertEqual(len(plans_t1_keyword_alpha), 1)
        self.assertEqual(plans_t1_keyword_alpha[0].id, lp1_t1.id)

        # Test: Filter by combination of class_id and title_keyword for teacher1
        plans_t1_combo = self.db_manager.get_lesson_plans_by_teacher(
            self.teacher1.id,
            associated_class_id=self.class1.id,
            title_keyword="Python"
        )
        self.assertEqual(len(plans_t1_combo), 1)
        self.assertEqual(plans_t1_combo[0].id, lp3_t1.id)

        # Test: Teacher with no plans
        teacher3 = self.db_manager.add_entity(Entity(name="Prof. Novo", type="teacher"))
        self.assertIsNotNone(teacher3)
        self.assertIsNotNone(teacher3.id)
        plans_t3 = self.db_manager.get_lesson_plans_by_teacher(teacher3.id)
        self.assertEqual(len(plans_t3), 0)

    def test_update_lesson_plan(self):
        """Test updating an existing lesson plan, including its associations."""
        # 1. Add an initial LessonPlan
        initial_files = [
            LessonPlanFile(lesson_plan_id=0, file_name="file_A.pdf", file_path="/path/A.pdf"),
            LessonPlanFile(lesson_plan_id=0, file_name="file_B.txt", file_path="/path/B.txt")
        ]
        initial_links = [
            LessonPlanLink(lesson_plan_id=0, url="http://linkX.com", title="Link X"),
            LessonPlanLink(lesson_plan_id=0, url="http://linkY.org", title="Link Y")
        ]
        initial_plan = LessonPlan(
            teacher_id=self.teacher1.id,
            title="Plano Original para Update",
            lesson_date=datetime(2024, 2, 10),
            objectives="Objetivos originais.",
            class_ids=[self.class1.id, self.class2.id],
            files=initial_files,
            links=initial_links
        )
        added_original_plan = self.db_manager.add_lesson_plan(initial_plan)
        self.assertIsNotNone(added_original_plan)
        self.assertIsNotNone(added_original_plan.id)

        # Keep track of original file/link IDs that we expect to persist
        original_file_a_id = None
        for f in added_original_plan.files:
            if f.file_name == "file_A.pdf":
                original_file_a_id = f.id
                break
        self.assertIsNotNone(original_file_a_id, "Original file A not found after add.")

        original_link_x_id = None
        for l_link in added_original_plan.links:
            if l_link.url == "http://linkX.com":
                original_link_x_id = l_link.id
                break
        self.assertIsNotNone(original_link_x_id, "Original link X not found after add.")


        # 2. Prepare updates
        plan_to_update = LessonPlan(
            id=added_original_plan.id, # Critical: ID must be set for update
            teacher_id=self.teacher1.id, # Must match for secure update
            title="Plano Atualizado com Sucesso",
            lesson_date=datetime(2024, 2, 12),
            objectives="Objetivos atualizados e melhorados.",
            program_content="Novo conteúdo programático.",
            class_ids=[self.class2.id, self.class3.id], # class1 removed, class3 added
            created_at=added_original_plan.created_at, # Should not change
            updated_at=datetime.now() # Will be updated by trigger, but good to set
        )

        # Files: Keep file_A, remove file_B, add file_C
        updated_files_list = []
        for f in added_original_plan.files: # Iterate over files from the *added* plan
            if f.file_name == "file_A.pdf":
                updated_files_list.append(f) # Keep this one (it has its ID and lesson_plan_id)
        updated_files_list.append(LessonPlanFile(lesson_plan_id=0, file_name="file_C.md", file_path="/path/C.md"))
        plan_to_update.files = updated_files_list

        # Links: Keep link_X, remove link_Y, add link_Z
        updated_links_list = []
        for l_link in added_original_plan.links: # Iterate over links from the *added* plan
            if l_link.url == "http://linkX.com":
                updated_links_list.append(l_link) # Keep this one
        updated_links_list.append(LessonPlanLink(lesson_plan_id=0, url="http://linkZ.net", title="Link Z"))
        plan_to_update.links = updated_links_list

        # 3. Call Update
        update_success = self.db_manager.update_lesson_plan(plan_to_update)
        self.assertTrue(update_success, "update_lesson_plan should return True on success.")

        # 4. Fetch and Assert
        updated_fetched_plan = self.db_manager.get_lesson_plan_by_id(plan_to_update.id, self.teacher1.id)
        self.assertIsNotNone(updated_fetched_plan)
        self.assertEqual(updated_fetched_plan.title, "Plano Atualizado com Sucesso")
        self.assertEqual(updated_fetched_plan.objectives, "Objetivos atualizados e melhorados.")
        self.assertEqual(updated_fetched_plan.program_content, "Novo conteúdo programático.")
        self.assertEqual(updated_fetched_plan.lesson_date, datetime(2024, 2, 12))
        self.assertListEqual(sorted(updated_fetched_plan.class_ids), sorted([self.class2.id, self.class3.id]))

        # Assert files
        self.assertEqual(len(updated_fetched_plan.files), 2)
        file_names_fetched = sorted([f.file_name for f in updated_fetched_plan.files])
        self.assertListEqual(file_names_fetched, sorted(["file_A.pdf", "file_C.md"]))

        file_a_fetched = next((f for f in updated_fetched_plan.files if f.file_name == "file_A.pdf"), None)
        self.assertIsNotNone(file_a_fetched)
        self.assertEqual(file_a_fetched.id, original_file_a_id) # Should be the same DB record

        file_c_fetched = next((f for f in updated_fetched_plan.files if f.file_name == "file_C.md"), None)
        self.assertIsNotNone(file_c_fetched)
        self.assertIsNotNone(file_c_fetched.id) # Should have a new ID
        self.assertNotEqual(file_c_fetched.id, original_file_a_id)


        # Assert links
        self.assertEqual(len(updated_fetched_plan.links), 2)
        link_urls_fetched = sorted([l.url for l in updated_fetched_plan.links])
        self.assertListEqual(link_urls_fetched, sorted(["http://linkX.com", "http://linkZ.net"]))

        link_x_fetched = next((l for l in updated_fetched_plan.links if l.url == "http://linkX.com"), None)
        self.assertIsNotNone(link_x_fetched)
        self.assertEqual(link_x_fetched.id, original_link_x_id)

        link_z_fetched = next((l for l in updated_fetched_plan.links if l.url == "http://linkZ.net"), None)
        self.assertIsNotNone(link_z_fetched)
        self.assertIsNotNone(link_z_fetched.id)
        self.assertNotEqual(link_z_fetched.id, original_link_x_id)


        # 5. Security Test (Teacher ID change attempt)
        plan_to_update.teacher_id = self.teacher2.id # Attempt to change owner
        update_fail_result = self.db_manager.update_lesson_plan(plan_to_update)
        self.assertFalse(update_fail_result, "Update should fail if trying to change owner via teacher_id mismatch.")

        refetched_plan_after_failed_update = self.db_manager.get_lesson_plan_by_id(plan_to_update.id, self.teacher1.id)
        self.assertIsNotNone(refetched_plan_after_failed_update)
        self.assertEqual(refetched_plan_after_failed_update.teacher_id, self.teacher1.id, "Teacher ID should not have changed.")
        self.assertEqual(refetched_plan_after_failed_update.title, "Plano Atualizado com Sucesso", "Title should remain as per the last successful update.")

    def test_delete_lesson_plan(self):
        """Test deleting a lesson plan and verifying cascade deletes."""
        # 1. Add a LessonPlan for teacher1
        plan_files = [LessonPlanFile(lesson_plan_id=0, file_name="del_test.txt", file_path="/path/del.txt")]
        plan_links = [LessonPlanLink(lesson_plan_id=0, url="http://delete.me", title="Delete Me")]
        plan_classes = [self.class1.id]

        lp1_t1_data = LessonPlan(
            teacher_id=self.teacher1.id,
            title="Plan to be Deleted",
            class_ids=plan_classes,
            files=plan_files,
            links=plan_links
        )
        lp1_t1 = self.db_manager.add_lesson_plan(lp1_t1_data)
        self.assertIsNotNone(lp1_t1)
        self.assertIsNotNone(lp1_t1.id)
        lp1_t1_id = lp1_t1.id

        # 2. Failed delete attempt (wrong teacher)
        delete_fail_result = self.db_manager.delete_lesson_plan(lp1_t1_id, teacher_id=self.teacher2.id)
        self.assertFalse(delete_fail_result, "Delete should fail with incorrect teacher_id.")

        still_exists_plan = self.db_manager.get_lesson_plan_by_id(lp1_t1_id, self.teacher1.id)
        self.assertIsNotNone(still_exists_plan, "Plan should still exist after failed delete attempt.")

        # 3. Successful delete attempt (correct teacher)
        delete_success_result = self.db_manager.delete_lesson_plan(lp1_t1_id, teacher_id=self.teacher1.id)
        self.assertTrue(delete_success_result, "Delete should succeed with correct teacher_id.")

        # 4. Verify deletion of main plan
        deleted_plan_fetched = self.db_manager.get_lesson_plan_by_id(lp1_t1_id, self.teacher1.id)
        self.assertIsNone(deleted_plan_fetched, "Plan should be None after successful deletion.")

        # 5. Verify Cascade Deletion
        files_after_delete = self.db_manager.get_files_for_lesson_plan(lp1_t1_id)
        self.assertEqual(len(files_after_delete), 0, "Files associated with the plan should be cascade deleted.")

        links_after_delete = self.db_manager.get_links_for_lesson_plan(lp1_t1_id)
        self.assertEqual(len(links_after_delete), 0, "Links associated with the plan should be cascade deleted.")

        # _get_linked_classes_for_lesson_plan is an internal method, but it's the most direct way
        # to check the junction table via the DatabaseManager's API for this test.
        classes_after_delete = self.db_manager._get_linked_classes_for_lesson_plan(lp1_t1_id)
        self.assertEqual(len(classes_after_delete), 0, "Class associations should be cascade deleted.")

        # 6. Isolation Test
        lp2_t1_data = LessonPlan(teacher_id=self.teacher1.id, title="Another Plan for T1")
        lp2_t1 = self.db_manager.add_lesson_plan(lp2_t1_data)
        self.assertIsNotNone(lp2_t1)
        lp2_t1_id = lp2_t1.id

        lp1_t2_data = LessonPlan(teacher_id=self.teacher2.id, title="Plan for T2")
        lp1_t2 = self.db_manager.add_lesson_plan(lp1_t2_data)
        self.assertIsNotNone(lp1_t2)
        lp1_t2_id = lp1_t2.id

        delete_lp2_t1_result = self.db_manager.delete_lesson_plan(lp2_t1_id, teacher_id=self.teacher1.id)
        self.assertTrue(delete_lp2_t1_result)

        # Verify lp1_t2 for teacher2 still exists
        lp1_t2_still_exists = self.db_manager.get_lesson_plan_by_id(lp1_t2_id, self.teacher2.id)
        self.assertIsNotNone(lp1_t2_still_exists, "Plan for teacher2 should still exist.")
        self.assertEqual(lp1_t2_still_exists.id, lp1_t2_id)


    # Test methods for add_lesson_plan, get_lesson_plan_by_id, etc., will be added here.

if __name__ == '__main__':
    unittest.main()
