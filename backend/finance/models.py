from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        PIX = 'PIX', 'Pix'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SETTLED = 'SETTLED', 'Settled'

    rental_id = models.PositiveBigIntegerField()
    customer_id = models.PositiveBigIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=8, choices=Method.choices)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    is_deposit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.rental_id} - {self.amount} ({self.status})'


class Fine(models.Model):
    class FineType(models.TextChoices):
        LATE = 'LATE', 'Late'
        DAMAGE = 'DAMAGE', 'Damage'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'

    rental_id = models.PositiveBigIntegerField()
    customer_id = models.PositiveBigIntegerField()
    fine_type = models.CharField(max_length=8, choices=FineType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.rental_id} - {self.fine_type} ({self.amount})'
