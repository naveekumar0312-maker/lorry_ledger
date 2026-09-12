from django.core.management.base import BaseCommand
from vehicles.models import VehicleDocument
from datetime import date

class Command(BaseCommand):
    help = 'Checks vehicle documents for expiry and generates reminders'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting document expiry check..."))

        today = date.today()
        # The threshold days requested by the user
        reminder_days = [30, 15, 7, 3, 1, 0]

        active_docs = VehicleDocument.objects.filter(is_active=True, expiry_date__isnull=False)

        alerts_generated = 0

        from django.db import IntegrityError

        for doc in active_docs:
            days_left = (doc.expiry_date - today).days

            if days_left in reminder_days:
                
                # Determine urgency for logging
                if days_left == 0:
                    urgency = "EXPIRED TODAY"
                elif days_left == 1:
                    urgency = "EXPIRING TOMORROW"
                else:
                    urgency = f"EXPIRING IN {days_left} DAYS"

                try:
                    from vehicles.models import VehicleDocumentReminder
                    # Attempt to create the reminder. If it exists for this document and reminder_type, it will fail due to unique_together.
                    reminder, created = VehicleDocumentReminder.objects.get_or_create(
                        document=doc,
                        reminder_type=days_left,
                    )
                    
                    if created:
                        alerts_generated += 1
                        msg = (
                            f"[{urgency}] Vehicle: {doc.vehicle.vehicle_number} | "
                            f"Document: {doc.get_document_type_display()} | "
                            f"Expiry: {doc.expiry_date.strftime('%Y-%m-%d')} | "
                            f"Remaining: {days_left} days"
                        )
                        self.stdout.write(self.style.WARNING(msg))
                        
                except IntegrityError:
                    # Duplicate reminder for this period already exists, ignore
                    pass

            elif days_left < 0:
                # Already expired, can optionally log or handle daily past-due alerts
                pass

        self.stdout.write(self.style.SUCCESS(f"Check complete. {alerts_generated} reminders generated today."))
