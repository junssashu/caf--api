from django.db import models


class Settings(models.Model):
    id = models.IntegerField(primary_key=True, default=1)
    taux_commission = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        help_text='Taux de commission en pourcentage (ex: 2.00 = 2%)',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settings'
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
