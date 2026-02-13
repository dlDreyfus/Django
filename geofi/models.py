from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class RelacaoContratos(models.Model):
    # Opções para o campo nomeUasg
    UASG_CHOICES = [
        ('UC', 'UC'),
        ('RF 01', 'RF 01'),
        ('RF 02', 'RF 02'),
        ('RF 03', 'RF 03'),
        ('RF 04', 'RF 04'),
        ('RF 05', 'RF 05'),
        ('RF 06', 'RF 06'),
        ('RF 07', 'RF 07'),
        ('RF 08', 'RF 08'),
        ('RF 09', 'RF 09'),
        ('RF 10', 'RF 10'),
    ]

    PI_CHOICES = [
        ('Custeio', 'Custeio'),
        ('Investimento', 'Investimento'),
        ('PIU', 'PIU'),
    ]

    # Campos solicitados
    uasg = models.IntegerField(
        verbose_name="UASG",
        help_text="Número inteiro com seis dígitos",
        validators=[MinValueValidator(100000), MaxValueValidator(999999)]
    )
    nomeUasg = models.CharField(
        max_length=10,
        choices=UASG_CHOICES,
        verbose_name="Nome UASG"
    )
    numContrato = models.CharField(
        max_length=20,
        verbose_name="Número do Contrato",
        help_text="Ex: 03/2025"
    )
    objetoContrato = models.TextField(
        verbose_name="Objeto do Contrato",
        help_text="Ex: motoristas, apoio administrativo"
    )
    inicioVigenciaContrato = models.DateField(
        verbose_name="Início da Vigência"
    )
    fimVigenciaContrato = models.DateField(
        verbose_name="Fim da Vigência"
    )
    pi = models.CharField(
        max_length=20,
        choices=PI_CHOICES,
        verbose_name="PI",
        default='Custeio'
    )
    valorMensalPrevisto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Mensal Previsto",
        default=0.00
    )
    
    # Campo identificador gerado automaticamente
    identificadorContrato = models.CharField(
        max_length=50,
        blank=True,
        editable=False,
        verbose_name="Id do Contrato"
    )

    def save(self, *args, **kwargs):
        # Concatena uasg e numContrato para formar o identificador antes de salvar
        # Exemplo: 123456 + "03/2025" = "12345603/2025"
        self.identificadorContrato = f"{self.uasg}{self.numContrato}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.identificadorContrato

    class Meta:
        verbose_name = "Relação de Contrato"
        verbose_name_plural = "Relações de Contratos"

class RelacaoMedicoesRealizadas(models.Model):
    MESES_CHOICES = [
        ('JAN', 'JAN'), ('FEV', 'FEV'), ('MAR', 'MAR'), ('ABR', 'ABR'),
        ('MAI', 'MAI'), ('JUN', 'JUN'), ('JUL', 'JUL'), ('AGO', 'AGO'),
        ('SET', 'SET'), ('OUT', 'OUT'), ('NOV', 'NOV'), ('DEZ', 'DEZ'),
    ]

    identificadorContrato = models.ForeignKey(
        RelacaoContratos,
        on_delete=models.CASCADE,
        verbose_name="Contrato"
    )
    mesMedicao = models.CharField(
        max_length=3,
        choices=MESES_CHOICES,
        verbose_name="Mês da Medição"
    )
    anoMedicao = models.IntegerField(
        verbose_name="Ano da Medição"
    )
    valorLiquidado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Liquidado",
        default=0.00
    )
    identificadorMedicao = models.CharField(
        max_length=100,
        blank=True,
        editable=False,
        verbose_name="Id da Medição"
    )

    def save(self, *args, **kwargs):
        # Concatena: identificadorContrato (str) + mes + ano + valor
        # O str(self.identificadorContrato) usa o __str__ da classe RelacaoContratos
        self.identificadorMedicao = f"{self.identificadorContrato}{self.mesMedicao}{self.anoMedicao}{self.valorLiquidado}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Relação de Medição Realizada"
        verbose_name_plural = "Relações de Medições Realizadas"
