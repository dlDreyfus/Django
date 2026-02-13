import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from geofi.models import RelacaoContratos, RelacaoMedicoesRealizadas

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados aleatórios para RelacaoContratos'

    def handle(self, *args, **kwargs):
        objetos_lista = [
            "Serviços de Limpeza", "Vigilância Armada", "Apoio Administrativo",
            "Manutenção Predial", "Motoristas", "Recepcionistas",
            "Jardinagem", "Copeiragem", "Suporte de TI", "Consultoria Especializada"
        ]

        # Obtém as opções definidas no model
        uasg_choices = RelacaoContratos.UASG_CHOICES
        pi_choices = ["Custeio", "Investimento", "PIU"]
        
        total_criados = 0

        self.stdout.write('Iniciando a criação de contratos...')

        for codigo_uasg, _ in uasg_choices:
            # Define aleatoriamente entre 10 e 15 registros para esta UASG
            qtd_registros = random.randint(10, 15)
            
            for _ in range(qtd_registros):
                uasg_num = random.randint(100000, 999999)
                # Gera número de contrato ex: 05/2024
                num_contrato = f"{random.randint(1, 150):02d}/{random.randint(2023, 2026)}"
                objeto = random.choice(objetos_lista)
                
                start_date = date(2023, 1, 1) + timedelta(days=random.randint(0, 700))
                end_date = start_date + timedelta(days=365)
                pi_valor = random.choice(pi_choices)
                valor_mensal = round(random.uniform(5000.00, 150000.00), 2)

                RelacaoContratos.objects.create(
                    uasg=uasg_num,
                    nomeUasg=codigo_uasg,
                    numContrato=num_contrato,
                    objetoContrato=objeto,
                    inicioVigenciaContrato=start_date,
                    fimVigenciaContrato=end_date,
                    pi=pi_valor,
                    valorMensalPrevisto=valor_mensal
                )
                total_criados += 1
        
        # Atualiza registros antigos que possam estar com valor 0 (popular base existente)
        self.stdout.write('Verificando e atualizando contratos existentes sem valor definido...')
        contratos_existentes = RelacaoContratos.objects.filter(valorMensalPrevisto=0)
        for contrato in contratos_existentes:
            contrato.valorMensalPrevisto = round(random.uniform(5000.00, 150000.00), 2)
            contrato.save()
            total_criados += 1 # Contabiliza como "processado/criado" para o output final

        # Gera medições para JAN e FEV de 2026 para todos os contratos
        self.stdout.write('Gerando medições para JAN e FEV de 2026...')
        todos_contratos = RelacaoContratos.objects.all()
        medicoes_criadas = 0
        meses_alvo = ['JAN', 'FEV']
        ano_alvo = 2026

        for contrato in todos_contratos:
            for mes in meses_alvo:
                # Gera um valor liquidado próximo ao valor previsto (variação de +/- 5%)
                valor_base = float(contrato.valorMensalPrevisto)
                valor_real = valor_base * random.uniform(0.95, 1.05)
                
                RelacaoMedicoesRealizadas.objects.get_or_create(
                    identificadorContrato=contrato,
                    mesMedicao=mes,
                    anoMedicao=ano_alvo,
                    defaults={'valorLiquidado': round(valor_real, 2)}
                )
                medicoes_criadas += 1

        self.stdout.write(self.style.SUCCESS(f'Sucesso! {total_criados} contratos processados e {medicoes_criadas} medições verificadas/criadas.'))