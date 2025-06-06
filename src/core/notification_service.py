from datetime import datetime, timedelta, time
from typing import List, Optional

from src.core.database_manager import DatabaseManager
from src.core.models import Notification, Event, Task

class NotificationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _has_existing_notification(self, related_item_id: int, notification_type: str, unique_marker: str) -> bool:
        """
        Checks if a notification with a similar unique marker already exists.
        The unique_marker could be part of the title or description.
        """
        # This is a simplified check. A more robust way would be to query based on a dedicated sub_type field.
        # For now, we assume the marker is in the title.
        existing_notifications = self.db_manager.get_notifications(
            notification_type=notification_type,
            # related_item_id=related_item_id # Removed for now, as get_notifications doesn't support it yet
        )
        for notif in existing_notifications:
            if notif.related_item_id == related_item_id and unique_marker in notif.title:
                return True
        return False

    def generate_event_reminders(self):
        if not self.db_manager.get_notification_preference('event_reminder'):
            # print("Lembretes de evento estão desabilitados.")
            return

        now = datetime.now()
        # Define reminder windows (relative to event start_time)
        # Format: (timedelta_before, textual_marker_for_title, notification_timestamp_offset)
        # notification_timestamp_offset is how long before the event the notification's own timestamp should be.
        reminder_configs = [
            (timedelta(days=1), "[1 dia antes]", timedelta(days=1)),
            (timedelta(hours=1), "[1 hora antes]", timedelta(hours=1)),
            (timedelta(minutes=15), "[15 mins antes]", timedelta(minutes=15)),
        ]

        # Fetch events for a reasonable future window, e.g., next 2 days
        # This might fetch more than needed, but avoids missing events across midnight if check runs late.
        # A more optimized DB query would be get_events_in_range(start, end)
        events_to_check: List[Event] = []
        for i in range(2): # Today and tomorrow
            target_date = now.date() + timedelta(days=i)
            events_to_check.extend(self.db_manager.get_events_by_date(target_date))

        # print(f"Checando {len(events_to_check)} eventos para lembretes...")

        for event in events_to_check:
            if not event.start_time or event.id is None:
                continue

            for delta_before, marker, ts_offset in reminder_configs:
                reminder_time = event.start_time - delta_before

                # Only create reminder if current time is past the intended reminder time,
                # but before the event itself has started.
                if now >= reminder_time and now < event.start_time:
                    if not self._has_existing_notification(event.id, 'event_reminder', marker):
                        notif_title = f"{event.title} {marker}"
                        notif_desc = f"Seu evento/aula começa às {event.start_time.strftime('%H:%M')} em {event.start_time.strftime('%d/%m/%Y')}."

                        # Notification timestamp should be when it's relevant (the reminder_time)
                        # or slightly adjusted if the check is late.
                        # For simplicity, using the calculated reminder_time for the notification's timestamp.
                        notification_timestamp = event.start_time - ts_offset

                        new_notification = Notification(
                            title=notif_title,
                            description=notif_desc,
                            timestamp=notification_timestamp,
                            type='event_reminder',
                            related_item_id=event.id
                        )
                        self.db_manager.add_notification(new_notification)
                        print(f"Lembrete de evento criado: {notif_title}")

    def generate_task_deadline_reminders(self):
        if not self.db_manager.get_notification_preference('task_deadline'):
            # print("Lembretes de prazo de tarefa estão desabilitados.")
            return

        now = datetime.now()
        # Reminder for tasks due today or tomorrow
        reminder_configs = [
            (timedelta(days=0), "[Vence Hoje]", timedelta(days=0)), # Due today
            (timedelta(days=1), "[Vence Amanhã]", timedelta(days=1)), # Due tomorrow
        ]

        all_tasks: List[Task] = self.db_manager.get_all_tasks()
        active_tasks = [t for t in all_tasks if t.status != 'Completed' and t.due_date and t.id is not None]

        # print(f"Checando {len(active_tasks)} tarefas ativas para lembretes de prazo...")

        for task in active_tasks:
            if task.id is None or task.due_date is None: continue # Should be filtered by active_tasks

            for day_offset, marker, _ in reminder_configs: # ts_offset not used for tasks here
                # Target due date for this reminder type (e.g., today, tomorrow)
                target_due_date_reminder = now.date() + day_offset

                # Check if task's due date matches the target for this reminder type
                if task.due_date.date() == target_due_date_reminder:
                    # Check if it's not too late in the day for "Due Today" if we want to avoid late-night notifs
                    # For now, any time during the reminder day is fine.
                    if not self._has_existing_notification(task.id, 'task_deadline', marker):
                        notif_title = f"Prazo da Tarefa: {task.title} {marker}"
                        notif_desc = f"Vence em {task.due_date.strftime('%d/%m/%Y')}."

                        # Timestamp for task deadline notifications can be beginning of the day or now.
                        # Using start of the day for "Due Today/Tomorrow" makes sense for sorting.
                        notification_timestamp = datetime.combine(task.due_date.date(), time.min)

                        new_notification = Notification(
                            title=notif_title,
                            description=notif_desc,
                            timestamp=notification_timestamp, # Or datetime.now() if preferred
                            type='task_deadline',
                            related_item_id=task.id
                        )
                        self.db_manager.add_notification(new_notification)
                        print(f"Lembrete de tarefa criado: {notif_title}")

if __name__ == '__main__':
    # This is a basic test block.
    # It requires a 'test.db' or similar and some sample data.
    print("Testing NotificationService...")
    # Mock or use a real DB Manager
    # db_path = 'data/agenda_test_notifications.db'
    # print(f"Using DB: {db_path}")
    # test_db_manager = DatabaseManager(db_path=db_path)

    # # Ensure settings allow notifications for testing
    # test_db_manager.set_notification_preference('event_reminder', True)
    # test_db_manager.set_notification_preference('task_deadline', True)

    # # Create some sample events and tasks if DB is empty
    # # Example: Event starting in 50 minutes
    # event_time_soon = datetime.now() + timedelta(minutes=50)
    # try:
    #     test_db_manager.add_event(Event(title="Reunião Teste Iminente", start_time=event_time_soon, event_type="reuniao"))
    #     # Event starting in 23 hours
    #     event_time_later = datetime.now() + timedelta(hours=23)
    #     test_db_manager.add_event(Event(title="Palestra Teste Amanhã", start_time=event_time_later, event_type="palestra"))

    #     # Task due today
    #     task_due_today = datetime.now().replace(hour=23, minute=59)
    #     test_db_manager.add_task(Task(title="Relatório Urgente Teste", due_date=task_due_today, priority="High"))
    #     # Task due tomorrow
    #     task_due_tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=17, minute=0)
    #     test_db_manager.add_task(Task(title="Planejamento Semanal Teste", due_date=task_due_tomorrow))
    # except Exception as e:
    #     print(f"Error adding sample data: {e}")


    # service = NotificationService(test_db_manager)

    # print("\n--- Gerando Lembretes de Evento ---")
    # service.generate_event_reminders()

    # print("\n--- Gerando Lembretes de Prazo de Tarefa ---")
    # service.generate_task_deadline_reminders()

    # print("\n--- Verificando notificações criadas (as 5 mais recentes) ---")
    # notifications = test_db_manager.get_notifications(limit=5) # Assuming get_notifications sorts by newest
    # if notifications:
    #     for n in notifications:
    #         print(f"- ID: {n.id}, Título: {n.title}, Timestamp: {n.timestamp}, Tipo: {n.type}, Lido: {n.is_read}")
    # else:
    #     print("Nenhuma notificação encontrada.")

    # test_db_manager.close()
    print("Teste básico concluído. Descomente e adapte o bloco de teste com um DB para uso real.")
