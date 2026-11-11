# -*- coding: utf-8 -*-
"""
Dados reais extraídos e higienizados da planilha financeira da Igreja (2023, 2025 e 2026)
Com os 10 Grupos de Despesas idênticos ao Slide de Apresentação da Assembleia (PowerPoint)
e os 15 Ministérios com Realizado 2025, Orçamento 2026 e Observações.
"""

MINISTERIOS_REAIS = [
    ("Ministério Viver", "Coord. Projeto Viver", 11030.20, 12500.00, "Compras de uniformes, chuteiras, intercâmbio", "#10b981"),
    ("EBD (Escola Bíblica)", "Superintendência EBD", 7028.00, 6900.00, "Literatura, café, brindes", "#f59e0b"),
    ("Ministério Infantil", "Coord. Infantil", 5555.58, 6000.00, "EBF, materiais didáticos, lanche", "#ec4899"),
    ("Ministério Eventos", "Comissão de Eventos", 4275.33, 4650.00, "Eventos da igreja e ministérios", "#8b5cf6"),
    ("Ministério Ação Social", "Coord. Ação Social", 4197.22, 4200.00, "Falecimento, coroa, auxílio emergencial", "#ef4444"),
    ("Ministério Sonoplastia", "Equipe de Som e Mídia", 3196.06, 3200.00, "Cabos, pilhas, manutenção dos equipamentos", "#0ea5e9"),
    ("Ministério Missões", "Conselho Missionário", 2925.07, 4020.00, "Acampamentos, Campanhas, oferta a missionários", "#14b8a6"),
    ("Ministério de Casais", "Casal Líder", 2630.02, 3000.00, "Encontros e presentes etc.", "#f43f5e"),
    ("Ministério Jovens e Adolescentes", "Liderança de Jovens", 5562.70, 7400.00, "Saída para acampamento de 2025 e encontros mensais", "#6366f1"),
    ("Ministério Homens", "Liderança Masculina", 1317.46, 1500.00, "Encontros e atividades de homens", "#3b82f6"),
    ("Ministério Coral", "Regência do Coral", 677.97, 760.00, "Partituras, pastas e apresentações", "#a855f7"),
    ("Ministério Mulheres Batista", "Liderança Feminina (MCM)", 675.24, 2500.00, "Em 2025 não utilizava a verba mensal, por isso essa diferença grande.", "#d946ef"),
    ("Ministério Comunicação", "Equipe Comunica", 397.90, 1160.00, "No comunica, colocamos as mesmas despesas de 2025, com o acréscimo.", "#06b6d4"),
    ("Ministério Louvor", "Líder de Louvor", 279.99, 279.99, "Sem orçamento fixo definido.", "#4f46e5"),
    ("Ministério Diáconos", "Corpo Diaconal", 253.43, 253.43, "Sem orçamento fixo definido.", "#64748b"),
    ("Diretoria", "Pastor Presidente & Diretoria Executiva", 0.0, 0.0, "Diretoria Estatutária da Igreja: Pastor Presidente, Vice-Presidente, Secretários e Tesoureiros.", "#1e293b"),
]

# Os 10 grupos oficiais de despesas idênticos ao gráfico "RESUMO DESPESAS" do PowerPoint da Igreja:
# 1. Despesas Fixas
# 2. Folha de Pagamento
# 3. Impostos
# 4. Desp. banco/Cartório/Sistema
# 5. Convenção/Campanhas Miss.
# 6. Missionários Fixos
# 7. Despesas com Ministérios
# 8. Manutenção/Patrimônio/Equip.
# 9. Despesas Operacionais
# 10. Gráfica /Livraria/ADM

MATRIZ_2025 = [
    # ENTRADAS 2025 (Total: R$ 358.641,60)
    (2025, "ENTRADA", "Entradas", "Saldo em Conta Itaú", [15933.39, 11902.05, 23195.14, 16999.62, 43732.28, 21511.19, 14322.14, 15464.82, 20145.18, 18025.42, 18706.47, 19307.68]),
    (2025, "ENTRADA", "Entradas", "Dízimos Gasofilácio", [6442.57, 5119.69, 3992.19, 4595.47, 4631.10, 5219.80, 3954.75, 4937.00, 4540.07, 5497.38, 5869.75, 5367.20]),
    (2025, "ENTRADA", "Entradas", "Saldo em Conta Bradesco", [1953.00, 1979.23, 2055.78, 1519.85, 2388.31, 2902.81, 2080.09, 2183.56, 2635.57, 2781.32, 2626.23, 3534.08]),
    (2025, "ENTRADA", "Entradas", "Oferta das Campanhas JMM/JMN/CBESP", [0, 0, 3217.73, 2435.00, 0, 0, 1541.86, 0, 726.75, 516.50, 108.00, 0]),
    (2025, "ENTRADA", "Entradas", "Outro / Retiro / Piquenique / Camiseta Aniv.", [0, 0, 0, 3465.00, 0, 0, 0, 0, 0, 2221.00, 2396.50, 0]),
    (2025, "ENTRADA", "Entradas", "Reembolso / Devolução", [0, 0, 4814.85, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    (2025, "ENTRADA", "Entradas", "Cantina e Bazar", [863.56, 0, 750.00, 0, 0, 1000.00, 992.38, 300.00, 0, 0, 0, 0]),
    (2025, "ENTRADA", "Entradas", "Panetones Cristolândia", [250.00, 0, 0, 0, 0, 0, 0, 0, 0, 0, 500.00, 1300.00]),
    (2025, "ENTRADA", "Entradas", "Promessa de Fé", [631.00, 248.00, 0, 0, 257.70, 120.55, 0, 425.60, 0, 0, 0, 65.00]),
    (2025, "ENTRADA", "Entradas", "Oferta Projeto Viver", [0, 0, 0, 0, 112.33, 0, 830.01, 300.10, 0, 0, 0, 0]),
    (2025, "ENTRADA", "Entradas", "Oferta Educação Cristã", [0, 0, 0, 0, 200.00, 0, 0, 0, 0, 0, 0, 0]),

    # SAÍDAS 2025 - 10 GRUPOS DO SLIDE
    (2025, "SAIDA", "Despesas Fixas", "Conta de Internet Telefone", [145.64, 131.35, 119.89, 119.75, 119.86, 119.89, 130.27, 130.27, 130.27, 130.27, 130.27, 130.27]),
    (2025, "SAIDA", "Despesas Fixas", "Conta de Água (Sabesp)", [156.96, 153.96, 244.29, 153.96, 153.83, 153.96, 184.07, 184.07, 244.29, 214.18, 304.51, 153.96]),
    (2025, "SAIDA", "Despesas Fixas", "Conta de Energia (Enel)", [317.42, 1007.03, 605.26, 438.18, 439.17, 484.57, 852.85, 917.64, 1038.73, 0, 0, 0]),
    (2025, "SAIDA", "Despesas Fixas", "Contador Cardoso & Garisto", [530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00, 530.00]),
    (2025, "SAIDA", "Despesas Fixas", "Monitoramento Sistema ADT", [408.95, 408.95, 408.95, 408.95, 408.95, 408.95, 408.95, 408.95, 408.96, 408.00, 408.95, 0]),

    (2025, "SAIDA", "Folha de Pagamento", "Renda Eclesiástica (IVAN)", [4644.41, 0, 13994.55, 4664.65, 4664.85, 4687.11, 5305.05, 4687.11, 4687.11, 4687.11, 4687.11, 4013.21]),
    (2025, "SAIDA", "Folha de Pagamento", "Fundo Ministerial", [416.67, 416.67, 416.67, 416.67, 439.17, 416.67, 416.67, 416.67, 416.67, 416.67, 416.67, 408.95]),
    (2025, "SAIDA", "Folha de Pagamento", "13º Salário", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2500.00, 2500.00]),
    (2025, "SAIDA", "Folha de Pagamento", "Diarista (Viviane)", [1800.00, 1600.00, 1600.00, 1800.00, 1800.00, 1800.00, 1800.00, 1800.00, 1800.00, 1900.00, 1900.00, 1800.00]),
    (2025, "SAIDA", "Folha de Pagamento", "Cesta Natalina / Outros Folha", [163.90, 0, 0, 0, 0, 0, 0, 0, 306.69, 0, 0, 0]),

    (2025, "SAIDA", "Impostos", "DARF / Ministério Pastoral IRRF", [616.00, 863.49, 355.52, 355.52, 355.52, 333.26, 333.26, 548.83, 333.26, 333.26, 333.26, 1007.16]),
    (2025, "SAIDA", "Impostos", "ISS Imposto de Serviços", [8.96, 8.96, 8.76, 8.96, 8.76, 17.52, 8.76, 8.96, 8.96, 8.96, 8.76, 8.76]),
    (2025, "SAIDA", "Impostos", "TFE Taxa de Fiscalização", [0, 0, 0, 0, 0, 0, 232.66, 0, 0, 0, 0, 0]),

    (2025, "SAIDA", "Desp. banco/Cartório/Sistema", "Despesas Bancárias Itaú", [155.98, 128.22, 183.91, 198.74, 195.22, 177.91, 236.85, 199.56, 205.88, 210.44, 238.73, 163.07]),
    (2025, "SAIDA", "Desp. banco/Cartório/Sistema", "Despesas Bancárias Bradesco", [171.70, 171.70, 171.70, 171.70, 171.70, 171.70, 177.05, 177.05, 177.05, 177.70, 177.05, 0]),
    (2025, "SAIDA", "Desp. banco/Cartório/Sistema", "Seguro Itaú", [126.92, 0, 126.92, 0, 0, 0, 236.85, 0, 0, 0, 126.92, 126.92]),
    (2025, "SAIDA", "Desp. banco/Cartório/Sistema", "Canva / Microsoft / Sistema Justus / Cert. Digital", [34.90, 34.90, 798.05, 270.29, 264.60, 34.90, 34.90, 266.90, 34.90, 64.90, 34.90, 34.90]),

    (2025, "SAIDA", "Convenção/Campanhas Miss.", "Plano Cooperativo", [0, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00]),
    (2025, "SAIDA", "Convenção/Campanhas Miss.", "Associação Sudocap", [100.38, 100.39, 100.39, 100.39, 100.39, 100.39, 100.38, 100.38, 100.38, 100.38, 100.38, 100.38]),
    (2025, "SAIDA", "Convenção/Campanhas Miss.", "Recanto dos Avós", [50.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00, 150.00]),
    (2025, "SAIDA", "Convenção/Campanhas Miss.", "Campanhas JMM / JMN / JME / Panetones / Convidados", [0, 540.00, 300.00, 0, 3956.94, 200.00, 0, 2040.00, 1000.62, 2525.00, 0, 1800.00]),

    (2025, "SAIDA", "Missionários Fixos", "Missionários Fixos da JMN", [240.00, 240.00, 240.00, 140.00, 240.00, 0, 240.00, 240.00, 240.00, 240.00, 240.00, 240.00]),
    (2025, "SAIDA", "Missionários Fixos", "Pr. Cláudio do Balneário + Auxílio Aluguel", [800.00, 200.00, 500.00, 500.00, 500.00, 500.00, 500.00, 500.00, 500.00, 500.00, 500.00, 500.00]),
    (2025, "SAIDA", "Missionários Fixos", "Pr. Nino / Miss. Valmir / Gás Cristolândia", [120.00, 250.00, 250.00, 120.00, 190.00, 120.00, 380.00, 120.00, 250.00, 120.00, 255.00, 195.00]),

    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Viver", [0, 0, 714.01, 701.40, 759.20, 1843.19, 812.39, 1329.98, 1053.45, 1050.00, 1558.67, 1207.91]),
    (2025, "SAIDA", "Despesas com Ministérios", "EBD (Café / Material / Brindes)", [138.09, 609.80, 1010.19, 1108.04, 412.63, 603.94, 577.71, 581.46, 506.26, 650.00, 466.90, 362.98]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Infantil", [84.00, 253.10, 536.68, 150.00, 256.30, 2179.77, 322.39, 259.96, 150.00, 1063.38, 150.00, 150.00]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Eventos", [0, 174.27, 292.20, 136.96, 557.79, 344.69, 460.02, 723.57, 329.43, 0, 0, 1256.40]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Ação Social", [1350.00, 150.00, 500.00, 205.80, 150.00, 539.18, 150.00, 150.00, 150.00, 150.00, 150.00, 552.24]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Sonoplastia", [0, 40.39, 0, 104.00, 639.47, 0, 85.80, 0, 1775.00, 380.00, 0, 171.40]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Missões", [0, 730.00, 0, 0, 199.00, 0, 322.59, 888.12, 63.48, 536.41, 185.47, 0]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério de Casais", [0, 0, 0, 0, 0, 1510.02, 0, 0, 0, 0, 1120.00, 0]),
    (2025, "SAIDA", "Despesas com Ministérios", "Ministério Jovens e Adolescentes", [150.00, 250.00, 190.00, 159.03, 150.00, 150.00, 0, 213.67, 250.00, 0, 0, 350.00]),
    (2025, "SAIDA", "Despesas com Ministérios", "Homens / Mulheres / Coral / Comunica / Louvor / Diáconos / Outros", [0, 362.70, 817.65, 761.98, 0, 1052.35, 737.26, 808.31, 1105.78, 681.10, 0, 174.30]),

    (2025, "SAIDA", "Manutenção/Patrimônio/Equip.", "Obra Central Sul", [0, 0, 0, 0, 9800.00, 10460.00, 6160.00, 7960.00, 7860.00, 7398.25, 3238.25, 2700.00]),
    (2025, "SAIDA", "Manutenção/Patrimônio/Equip.", "Elétrica / Luminária", [0, 0, 0, 867.86, 0, 9678.91, 11524.20, 7285.71, 4560.41, 10861.03, 3709.84, 2581.41]),
    (2025, "SAIDA", "Manutenção/Patrimônio/Equip.", "Manutenção Geral e Pintura", [0, 188.79, 1982.70, 0, 397.71, 0, 0, 9271.75, 7392.15, 4152.01, 2700.00, 0]),
    (2025, "SAIDA", "Manutenção/Patrimônio/Equip.", "Patrimônio, Extintores/CLCB, Taxas e Diversos", [787.53, 1342.60, 0, 30.00, 332.27, 438.25, 548.25, 1019.50, 4607.13, 2017.64, 1124.54, 1124.54]),

    (2025, "SAIDA", "Despesas Operacionais", "Eventos da Igreja (Retiro / Aniversário)", [0, 0, 0, 5470.00, 541.69, 0, 0, 0, 463.55, 4339.38, 4717.50, 0]),
    (2025, "SAIDA", "Despesas Operacionais", "Descartáveis, Limpeza, Ceia, Cozinha e Gás", [135.00, 785.64, 1090.51, 686.66, 607.12, 400.00, 638.76, 159.98, 1096.68, 875.58, 0, 250.74]),

    (2025, "SAIDA", "Gráfica /Livraria/ADM", "Gráfica, Bíblias, Livraria e Material de Escritório", [272.68, 0, 0, 21.00, 357.30, 0, 420.33, 0, 762.87, 0, 330.00, 0]),
]

# EXERCÍCIO 2026 COM TODAS AS 113 LINHAS DETALHADAS SOLICITADAS
MATRIZ_2026 = [
# ENTRADAS 2026 (14 rubricas)
    (2026, "ENTRADA", "Entradas", "Dízimos (Média de Entrada)", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Oferta das Campanhas JMM/ JMN/ JME", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Cantina", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Bazar", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Promessa de Fé", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Oferta Projeto Viver", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Leilão de Missionário", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Dízimos Gasofilácio", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Saldo em Conta Itaú", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Saldo em Conta Bradesco", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Panetones Cristolândia", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Oferta Educação Cristã", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Reembolso/ Devolução/Estorno", [0.0] * 12),
    (2026, "ENTRADA", "Entradas", "Outro/Retiro/Piquenique /Camiseta aniv.", [0.0] * 12),

    # 1. DESPESAS FIXAS (5 rubricas)
    (2026, "SAIDA", "Despesas Fixas", "Conta de Internet Telefone", [0.0] * 12),
    (2026, "SAIDA", "Despesas Fixas", "Conta de Água (Sabesp)", [0.0] * 12),
    (2026, "SAIDA", "Despesas Fixas", "Conta de Energia (Enel)", [0.0] * 12),
    (2026, "SAIDA", "Despesas Fixas", "Contador Cardoso & Garisto", [0.0] * 12),
    (2026, "SAIDA", "Despesas Fixas", "Monitoramento Sistema ADT", [0.0] * 12),

    # 2. FOLHA DE PAGAMENTO (7 rubricas)
    (2026, "SAIDA", "Folha de Pagamento", "Renda Eclesiástica (IVAN)", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "Fundo Ministerial", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "13º Salário", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "1/3 de Férias", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "Diarista (Viviane)", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "Cesta Natalina", [0.0] * 12),
    (2026, "SAIDA", "Folha de Pagamento", "Outros (Folha de Pagamento)", [0.0] * 12),

    # 3. IMPOSTOS (4 rubricas)
    (2026, "SAIDA", "Impostos", "DARF/ Ministério Pastoral IRRF", [0.0] * 12),
    (2026, "SAIDA", "Impostos", "ISS Imposto de Serviços", [0.0] * 12),
    (2026, "SAIDA", "Impostos", "IPTU", [0.0] * 12),
    (2026, "SAIDA", "Impostos", "TFE Taxa de Fiscalização de Estabelecimento", [0.0] * 12),

    # 4. DESPESAS BANCÁRIAS / CARTÓRIO / SISTEMA (11 rubricas)
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Despesas bancárias Itaú", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Despesas bancárias / Bradesco", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Seguro Itaú", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Assinatura Microsoft anual", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Sistema Gileade Escalas", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Cartório", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Jurídico", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Sistema Justus", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Advogado", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Certificado Digital", [0.0] * 12),
    (2026, "SAIDA", "Desp. banco/Cartório/Sistema", "Motoboy", [0.0] * 12),

    # 5. CONVENÇÃO BATISTA / CAMPANHAS (9 rubricas)
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Plano Cooperativo", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Associação Sudocap", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Recanto dos Avós", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Campanha de Missões Mundiais", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Campanha de Missões Nacionais", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Campanha de Missões Estaduais", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Educação Cristã", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Campanha Panetones", [0.0] * 12),
    (2026, "SAIDA", "Convenção/Campanhas Miss.", "Oferta p/Missionário Convidado", [0.0] * 12),

    # 6. MISSIONÁRIO FIXO (7 rubricas)
    (2026, "SAIDA", "Missionários Fixos", "Missionários Fixos da JMN", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Pr. Cláudio do Balneário", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Auxílio Aluguel do Balneário", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Pr. Nino", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Missionário Valmir", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Gás Cristolândia", [0.0] * 12),
    (2026, "SAIDA", "Missionários Fixos", "Outros (Missionários Fixos)", [0.0] * 12),

    # 7. DESPESAS COM MINISTÉRIOS (15 rubricas)
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Mulheres Batista", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Homens", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Jovens e Adolescentes", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério de Casais", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Ação Social", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Viver", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Infantil", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Sonoplastia", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Louvor", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Eventos", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Comunicação", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Coral", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério Missões", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "Ministério dos Diáconos", [0.0] * 12),
    (2026, "SAIDA", "Despesas com Ministérios", "EBD = Café/Material/Brindes", [0.0] * 12),

    # 8. MANUTENÇÃO / PATRIMÔNIO / REGULARIZAÇÃO (24 rubricas)
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Manutenção", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Patrimônio", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Tinta/Pintor", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Central Sul", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Elétrica / Luminária", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Equipamentos", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Cópias de Chaves", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Limpeza da Praça", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Marceneiro", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Filtro do Bebedouro", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Recarga de Extintores/CLCB", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Botijão de Gás", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Máquina de Plastificação", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "EPIs / Placa de Sinalização", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Impressora / Tinta", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Instalação Central de Gás", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Caçamba Entulho", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "ART - Anotação de Responsabilidade Técnica", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Documentação Terreno/ Escritura/Registro", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Regularização do Imóvel (CALEGARI)", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Licença de Funcionamento", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Elaboração da Planta Atualizada com ART", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Taxas Diversas (Documentação)", [0.0] * 12),
    (2026, "SAIDA", "Manutenção/Patrimônio/Equip.", "Outros (Manutenção / Obras)", [0.0] * 12),

    # 9. DESPESAS OPERACIONAIS DA IGREJA (10 rubricas)
    (2026, "SAIDA", "Despesas Operacionais", "Eventos (Retiro/Aniversário)", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Material Descartável (Copos - Papel Higiênico)", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Material de Limpeza", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Tapete Capacho", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Alimento da Ceia", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Utensílios da Cozinha", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Transporte Uber", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Gás Igreja", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Tecido para Toalha de Mesa", [0.0] * 12),
    (2026, "SAIDA", "Despesas Operacionais", "Outros (Despesas Operacionais)", [0.0] * 12),

    # 10. GRÁFICA / LIVRARIA / ADM (7 rubricas)
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Kalunga", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Material Evangelístico", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Treinamento", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Gráfica", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Livraria Cristã Sarzedas/União Feminina", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Bíblia", [0.0] * 12),
    (2026, "SAIDA", "Gráfica /Livraria/ADM", "Material de Escritório", [0.0] * 12),
]

# HISTÓRICO 2023
MATRIZ_2023 = [
    (2023, "ENTRADA", "Entradas", "Dízimos (Média de Entrada)", [19827.72, 16110.62, 24091.39, 20874.12, 21921.65, 21971.51, 25143.73, 20336.48, 23342.56, 22451.49, 25693.07, 0]),
    (2023, "ENTRADA", "Entradas", "Ofertas Missões JMM / JMN / JME", [592.00, 150.00, 1733.95, 3372.40, 3143.03, 100.00, 2222.10, 1402.00, 1033.40, 2150.70, 486.00, 0]),
    (2023, "ENTRADA", "Entradas", "Projeto Viver / Leilão / Reembolsos / Outros", [650.00, 1269.06, 200.00, 200.00, 200.00, 293.39, 200.00, 200.00, 200.00, 7093.90, 2836.38, 0]),
    (2023, "SAIDA", "Despesas Fixas", "Despesas Fixas, Folha, Prebenda e Ministérios Fixos", [4589.45, 5148.83, 8740.88, 7933.49, 11542.08, 10950.47, 12775.51, 10173.02, 2143.51, 1750.00, 1750.00, 2250.00]),
    (2023, "SAIDA", "Despesas Operacionais", "Campanhas, IPTU, Manutenção, Equipamentos e Geral", [3816.49, 7441.06, 3806.73, 2806.47, 20436.25, 6178.25, 7299.33, 8756.26, 0, 0, 0, 0]),
    (2023, "SAIDA", "Manutenção/Patrimônio/Equip.", "Licença de Funcionamento e Regularização", [1390.00, 2390.00, 0, 0, 0, 0, 0, 4590.00, 0, 0, 0, 0]),
]
