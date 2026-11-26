from decimal import Decimal

from core.domain.money import to_money
from django.db import models


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BLOCKED = "BLOCKED", "Blocked"

    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    birth_date = models.DateField()
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.ACTIVE
    )
    completed_rentals = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.full_name


class DriverLicense(models.Model):
    class Category(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        AB = "AB", "AB"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="licenses"
    )
    number = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=2, choices=Category.choices)
    expires_on = models.DateField()

    def __str__(self):
        return f"{self.number} ({self.category})"


class Insurance(models.Model):
    """Seguro (classe base). Use BasicInsurance ou FullInsurance.

    O cálculo do custo do cliente em caso de avaria muda em cada filha
    (polimorfismo): a base apenas define o contrato.
    """

    name = models.CharField(max_length=100, unique=True)
    daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")
    deductible = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")
    coverage_limit = models.DecimalField(
        max_digits=10, decimal_places=2, default="0.00"
    )

    def __str__(self):
        return self.name

    def get_real(self):
        """Devolve a instância da classe filha (BasicInsurance ou FullInsurance).

        Quem busca por Insurance.objects.get(pk=...) recebe a classe base;
        este método encontra a filha para que o cálculo certo seja usado.
        """
        for child_name in ("basicinsurance", "fullinsurance"):
            child = getattr(self, child_name, None)
            if child is not None:
                return child
        return self

    def calculate_daily_cost(self):
        return to_money(self.daily_cost)

    def calculate_customer_damage_cost(self, damage_value):
        raise NotImplementedError(
            "Use BasicInsurance ou FullInsurance: a classe base não define o custo da avaria."
        )


class BasicInsurance(Insurance):
    """Franquia alta e cobertura limitada: o cliente arca com a maior parte da avaria."""

    customer_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("80.00"),
    )

    def get_real(self):
        return self

    def calculate_customer_damage_cost(self, damage_value):
        damage = to_money(damage_value)
        return to_money(damage * self.customer_share_percent / Decimal("100"))


class FullInsurance(Insurance):
    """Franquia baixa, terceiros e assistência: o cliente paga no máximo a franquia."""

    third_party_coverage = models.BooleanField(default=False)
    roadside_assistance = models.BooleanField(default=False)

    def get_real(self):
        return self

    def calculate_customer_damage_cost(self, damage_value):
        damage = to_money(damage_value)
        return min(damage, to_money(self.deductible))
