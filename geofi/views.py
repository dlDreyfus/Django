from django.shortcuts import render, get_object_or_404
from .models import RelacaoContratos, RelacaoMedicoesRealizadas
from django.db.models import Q, CharField, Sum
from django.db.models.functions import Cast

# Create your views here.

def lista_contratos(request):
    # Começa com todos os contratos
    contratos = RelacaoContratos.objects.all()

    # Captura os parâmetros da URL (GET)
    filtro_uasg = request.GET.get('uasg', '')
    filtro_nome_uasg = request.GET.get('nomeUasg', '')
    filtro_contrato = request.GET.get('numContrato', '')
    filtro_objeto = request.GET.get('objetoContrato', '')
    filtro_inicio = request.GET.get('inicioVigenciaContrato', '')
    filtro_fim = request.GET.get('fimVigenciaContrato', '')
    filtro_identificador = request.GET.get('identificadorContrato', '')
    filtro_pi = request.GET.get('pi', '')
    search_query = request.GET.get('q', '') # Novo campo de busca geral
    ordenacao = request.GET.get('ordenacao', '')

    # Lógica para o link de ordenação cíclica na coluna de valor
    query_params_valor = request.GET.copy()
    if ordenacao == 'menor_valor':
        # Se já está ordenado por menor, o próximo clique ordena por maior
        query_params_valor['ordenacao'] = 'maior_valor'
    elif ordenacao == 'maior_valor':
        # Se está ordenado por maior, o próximo clique remove a ordenação (padrão)
        if 'ordenacao' in query_params_valor:
            del query_params_valor['ordenacao']
    else:
        # Se está na ordenação padrão, o primeiro clique ordena por menor valor
        query_params_valor['ordenacao'] = 'menor_valor'
    url_ordenacao_valor = query_params_valor.urlencode()

    # Lógica para ordenação de Início da Vigência
    query_params_inicio = request.GET.copy()
    if ordenacao == 'inicio_asc':
        query_params_inicio['ordenacao'] = 'inicio_desc'
    elif ordenacao == 'inicio_desc':
        if 'ordenacao' in query_params_inicio:
            del query_params_inicio['ordenacao']
    else:
        query_params_inicio['ordenacao'] = 'inicio_asc'
    url_ordenacao_inicio = query_params_inicio.urlencode()

    # Lógica para ordenação de Fim da Vigência
    query_params_fim = request.GET.copy()
    if ordenacao == 'fim_asc':
        query_params_fim['ordenacao'] = 'fim_desc'
    elif ordenacao == 'fim_desc':
        if 'ordenacao' in query_params_fim:
            del query_params_fim['ordenacao']
    else:
        query_params_fim['ordenacao'] = 'fim_asc'
    url_ordenacao_fim = query_params_fim.urlencode()

    # Aplica os filtros se os valores existirem
    if filtro_uasg:
        contratos = contratos.filter(uasg__icontains=filtro_uasg)
    
    if filtro_nome_uasg:
        contratos = contratos.filter(nomeUasg=filtro_nome_uasg)
    
    if filtro_contrato:
        contratos = contratos.filter(numContrato__icontains=filtro_contrato)
    
    if filtro_objeto:
        contratos = contratos.filter(objetoContrato__icontains=filtro_objeto)
        
    if filtro_inicio:
        contratos = contratos.filter(inicioVigenciaContrato=filtro_inicio)

    if filtro_fim:
        contratos = contratos.filter(fimVigenciaContrato=filtro_fim)

    if filtro_identificador:
        contratos = contratos.filter(identificadorContrato__icontains=filtro_identificador)

    if filtro_pi:
        contratos = contratos.filter(pi=filtro_pi)

    # Aplica o filtro de busca geral se houver um termo de busca
    if search_query:
        contratos = contratos.annotate(
            search_inicio=Cast('inicioVigenciaContrato', CharField()),
            search_fim=Cast('fimVigenciaContrato', CharField()),
            search_valor=Cast('valorMensalPrevisto', CharField())
        ).filter(
            Q(identificadorContrato__icontains=search_query) |
            Q(nomeUasg__icontains=search_query) |
            Q(numContrato__icontains=search_query) |
            Q(objetoContrato__icontains=search_query) |
            Q(pi__icontains=search_query) |
            Q(search_inicio__icontains=search_query) |
            Q(search_fim__icontains=search_query) |
            Q(search_valor__icontains=search_query)
        )

    # Aplica a ordenação baseada no parâmetro (antes de formatar o valor para string)
    if ordenacao == 'maior_valor':
        contratos = contratos.order_by('-valorMensalPrevisto')
    elif ordenacao == 'menor_valor':
        contratos = contratos.order_by('valorMensalPrevisto')
    elif ordenacao == 'inicio_asc':
        contratos = contratos.order_by('inicioVigenciaContrato')
    elif ordenacao == 'inicio_desc':
        contratos = contratos.order_by('-inicioVigenciaContrato')
    elif ordenacao == 'fim_asc':
        contratos = contratos.order_by('fimVigenciaContrato')
    elif ordenacao == 'fim_desc':
        contratos = contratos.order_by('-fimVigenciaContrato')
    else:
        # Ordenação padrão se nenhum parâmetro de ordenação for passado
        contratos = contratos.order_by('nomeUasg', 'inicioVigenciaContrato')

    # --- Lógica do Gráfico (Timeline 2026) ---
    meses_ordem = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Agrega os valores liquidados por mês para o ano de 2026
    dados_grafico = RelacaoMedicoesRealizadas.objects.filter(
        anoMedicao=2026,
        identificadorContrato__in=contratos
    ).values('mesMedicao').annotate(
        total_liquidado=Sum('valorLiquidado')
    )
    
    # Calcula o total previsto mensal somando o valor de todos os contratos filtrados
    total_previsto_mensal = contratos.aggregate(total=Sum('valorMensalPrevisto'))['total'] or 0

    # Transforma em dicionário para mapeamento rápido
    dados_map = {d['mesMedicao']: d for d in dados_grafico}
    
    # Prepara as listas ordenadas para o Chart.js
    chart_labels = meses_ordem
    chart_data_liquidado = []
    chart_data_previsto = []
    
    for mes in meses_ordem:
        dados = dados_map.get(mes, {})
        chart_data_liquidado.append(float(dados.get('total_liquidado', 0)))
        chart_data_previsto.append(float(total_previsto_mensal))

    # Formata os valores para exibição no padrão brasileiro (R$ 1.234,56)
    contratos_exibicao = []
    for contrato in contratos:
        valor_formatado = f"{contrato.valorMensalPrevisto:,.2f}"
        # Troca vírgula por X, ponto por vírgula, X por ponto para inverter o padrão US para BR
        contrato.valorMensalPrevisto = valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')
        contratos_exibicao.append(contrato)

    context = {
        'contratos': contratos_exibicao,
        'uasg_choices': RelacaoContratos.UASG_CHOICES,
        'pi_choices': RelacaoContratos.PI_CHOICES,
        'filtro_uasg': filtro_uasg,
        'filtro_nome_uasg': filtro_nome_uasg,
        'filtro_contrato': filtro_contrato,
        'filtro_objeto': filtro_objeto,
        'filtro_inicio': filtro_inicio,
        'filtro_fim': filtro_fim,
        'filtro_identificador': filtro_identificador,
        'filtro_pi': filtro_pi,
        'search_query': search_query,
        'ordenacao': ordenacao,
        'url_ordenacao_valor': url_ordenacao_valor,
        'url_ordenacao_inicio': url_ordenacao_inicio,
        'url_ordenacao_fim': url_ordenacao_fim,
        'chart_labels': chart_labels,
        'chart_data_liquidado': chart_data_liquidado,
        'chart_data_previsto': chart_data_previsto,
    }
    return render(request, 'geofi/lista_contratos.html', context)

def detalhe_contrato(request, contrato_id):
    # Busca o contrato pelo ID (Primary Key) ou retorna erro 404 se não existir
    contrato = get_object_or_404(RelacaoContratos, pk=contrato_id)
    
    # Busca as medições relacionadas a este contrato
    medicoes = RelacaoMedicoesRealizadas.objects.filter(identificadorContrato=contrato).order_by('anoMedicao', 'id')
    
    # --- Lógica do Gráfico (Timeline 2026) ---
    meses_ordem = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Agrega os valores liquidados para este contrato em 2026
    dados_grafico = RelacaoMedicoesRealizadas.objects.filter(
        identificadorContrato=contrato,
        anoMedicao=2026
    ).values('mesMedicao').annotate(
        total_liquidado=Sum('valorLiquidado')
    )
    
    dados_map = {d['mesMedicao']: d['total_liquidado'] for d in dados_grafico}
    
    chart_labels = meses_ordem
    chart_data_liquidado = []
    chart_data_previsto = []
    
    valor_previsto = float(contrato.valorMensalPrevisto)
    
    for mes in meses_ordem:
        chart_data_liquidado.append(float(dados_map.get(mes, 0)))
        chart_data_previsto.append(valor_previsto)

    # Formata os valores liquidados para o padrão brasileiro
    medicoes_exibicao = []
    for medicao in medicoes:
        valor_formatado = f"{medicao.valorLiquidado:,.2f}"
        medicao.valorLiquidado = valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')
        medicoes_exibicao.append(medicao)

    return render(request, 'geofi/detalhe_contrato.html', {
        'contrato': contrato,
        'medicoes': medicoes_exibicao,
        'chart_labels': chart_labels,
        'chart_data_liquidado': chart_data_liquidado,
        'chart_data_previsto': chart_data_previsto,
    })
