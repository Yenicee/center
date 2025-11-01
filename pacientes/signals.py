from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Session, Payment, Expense, Notification

@receiver(post_save, sender=Session)
def check_session_notifications(sender, instance, created, **kwargs):
    """
    notificación automática cuando una sesión es para mañana.
    Se ejecuta cada vez que se guarda una sesión.
    """
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Solo para sesiones programadas para mañana
    if instance.date == tomorrow and instance.status in [Session.STATUS_PENDING_PLANNED, Session.STATUS_PENDING_UNPLANNED]:
        Notification.create_session_reminder(instance)


@receiver(post_save, sender=Payment)
def check_payment_notifications(sender, instance, created, **kwargs):
    """
    notificación automática para pagos atrasados.
    
    """
    today = timezone.now().date()
    
    # Solo si el pago NO está pagado y la sesión ya pasó
    if not instance.is_paid and instance.session.date < today:
        Notification.create_payment_overdue(instance)


@receiver(post_save, sender=Expense)
def check_expense_notifications(sender, instance, created, **kwargs):
    """
    Genera notificaciones automáticas para gastos.
  
    """
    if not instance.due_date or instance.paid:
        return
    
    today = timezone.now().date()
    days_until_due = (instance.due_date - today).days
    
    # Gasto que vence en 3 días
    if days_until_due == 3:
        Notification.create_expense_due(instance)
    
    # Gasto vencido
    elif instance.due_date < today:
        Notification.create_expense_overdue(instance)


# Señal para limpiar notificaciones cuando se paga un gasto o pago
@receiver(post_save, sender=Payment)
def clear_payment_notifications_on_paid(sender, instance, **kwargs):
    """
    Elimina notificaciones de pago atrasado cuando se marca como pagado.
    """
    if instance.is_paid:
        # Marcar como leídas las notificaciones relacionadas
        Notification.objects.filter(
            payment=instance,
            notification_type='payment_overdue',
            is_read=False
        ).update(is_read=True, read_at=timezone.now())


@receiver(post_save, sender=Expense)
def clear_expense_notifications_on_paid(sender, instance, **kwargs):
    """
    Elimina notificaciones de gasto cuando se marca como pagado.
    """
    if instance.paid:
        # Marcar como leídas las notificaciones relacionadas
        Notification.objects.filter(
            expense=instance,
            notification_type__in=['expense_due', 'expense_overdue'],
            is_read=False
        ).update(is_read=True, read_at=timezone.now())