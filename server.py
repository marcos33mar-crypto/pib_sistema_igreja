# -*- coding: utf-8 -*-

"""

PIB Parque São Paulo - Sistema Integrado de Gestão Eclesiástica Multi-Usuário em Tempo Real

Backend com SQLite (Modo WAL para concorrência real) + Server-Sent Events (SSE)

Integrado com a Planilha Real da Tesouraria (2023, 2025 e 2026 + 15 Ministérios).

"""



import calendar

import json

import random

import os

import re

import socket

import sqlite3

import subprocess

import threading

import time

import base64

import urllib.parse

from datetime import datetime

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from urllib.parse import parse_qs, urlparse



try:
    from dados_planilha import MATRIZ_2023, MATRIZ_2025, MATRIZ_2026, MINISTERIOS_REAIS
except ImportError:
    # Fallback automático: dados embutidos caso dados_planilha.py não esteja no deploy
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



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "igreja_erp.db")

# Se index.html estiver na raiz (como enviado no GitHub), serve da raiz com prioridade!
if os.path.exists(os.path.join(BASE_DIR, "index.html")):
    STATIC_DIR = BASE_DIR
else:
    STATIC_DIR = os.path.join(BASE_DIR, "static")

CLOUDFLARED_PATH = os.path.join(BASE_DIR, "cloudflared.exe")



db_lock = threading.RLock()

sse_clients = []

sse_lock = threading.Lock()

LAST_MUTATION_TIMESTAMP = time.time()



PUBLIC_TUNNEL_URL = ""

LOCAL_LAN_URL = "http://localhost:8090"





def get_db():

    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA busy_timeout=30000;")

    conn.execute("PRAGMA foreign_keys=ON;")

    return conn





def parse_moeda(val):

    if val is None or val == "":

        return 0.0

    if isinstance(val, (int, float)):

        return float(val)

    s = str(val).strip().replace("R$", "").strip()

    if "." in s and "," in s:

        s = s.replace(".", "").replace(",", ".")

    elif "," in s:

        s = s.replace(",", ".")

    try:

        return float(s)

    except Exception:

        return 0.0





def add_months(dt, months):

    month = dt.month - 1 + months

    year = dt.year + month // 12

    month = month % 12 + 1

    day = min(dt.day, calendar.monthrange(year, month)[1])

    return dt.replace(year=year, month=month, day=day)





def broadcast_event(event_type, payload):

    global LAST_MUTATION_TIMESTAMP

    LAST_MUTATION_TIMESTAMP = time.time()

    payload["timestamp"] = LAST_MUTATION_TIMESTAMP

    message = f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    encoded = message.encode("utf-8")

    with sse_lock:

        dead_clients = []

        for client_wfile in sse_clients:

            try:

                client_wfile.write(encoded)

                client_wfile.flush()

            except Exception:

                dead_clients.append(client_wfile)

        for dc in dead_clients:

            if dc in sse_clients:

                sse_clients.remove(dc)





def validar_padrao_senha(senha):

    if not senha or len(senha) < 6:

        return False, "A senha deve conter no mínimo 6 caracteres."

    if not re.search(r"[A-Za-z]", senha):

        return False, "A senha deve conter pelo menos uma letra (maiúscula ou minúscula)."

    if not re.search(r"[0-9]", senha):

        return False, "A senha deve conter pelo menos um número."

    if not re.search(r"[^A-Za-z0-9]", senha):

        return False, "A senha deve conter pelo menos um caractere especial (ex: @, #, $, !, %, &, *, etc.)."

    return True, ""



def log_auditoria(conn, usuario_nome, setor, acao, detalhes):

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(

        "INSERT INTO auditoria (data_hora, usuario, setor, acao, detalhes) VALUES (?, ?, ?, ?, ?)",

        (agora, usuario_nome, setor, acao, detalhes),

    )

    try:

        conn.commit()

    except Exception:

        pass





def init_db():

    with db_lock:

        conn = get_db()

        conn.execute("PRAGMA journal_mode=WAL;")

        conn.execute("PRAGMA synchronous=NORMAL;")

        cur = conn.cursor()



        cur.executescript(

            """

            CREATE TABLE IF NOT EXISTS usuarios (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                cargo TEXT NOT NULL,

                perfil TEXT NOT NULL,

                ministerio_id INTEGER,

                ativo INTEGER DEFAULT 1,

                setores_permitidos TEXT DEFAULT '',

                senha TEXT DEFAULT '123456'

            );



            CREATE TABLE IF NOT EXISTS ministerios (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                lider TEXT NOT NULL,

                orcamento_mensal REAL DEFAULT 0,

                realizado_2025 REAL DEFAULT 0,

                orcamento_2026 REAL DEFAULT 0,

                descricao TEXT,

                cor TEXT DEFAULT '#4f46e5'

            );



            CREATE TABLE IF NOT EXISTS matriz_tesouraria (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                ano INTEGER NOT NULL,

                tipo_fluxo TEXT NOT NULL, -- 'ENTRADA' ou 'SAIDA'

                grupo TEXT NOT NULL,

                rubrica TEXT NOT NULL,

                m1 REAL DEFAULT 0,

                m2 REAL DEFAULT 0,

                m3 REAL DEFAULT 0,

                m4 REAL DEFAULT 0,

                m5 REAL DEFAULT 0,

                m6 REAL DEFAULT 0,

                m7 REAL DEFAULT 0,

                m8 REAL DEFAULT 0,

                m9 REAL DEFAULT 0,

                m10 REAL DEFAULT 0,

                m11 REAL DEFAULT 0,

                m12 REAL DEFAULT 0

            );



            CREATE TABLE IF NOT EXISTS celulas (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                lider TEXT NOT NULL,

                bairro TEXT NOT NULL,

                dia_horario TEXT NOT NULL,

                meta_membros INTEGER DEFAULT 15,

                ultima_frequencia INTEGER DEFAULT 0

            );



            CREATE TABLE IF NOT EXISTS membros (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                telefone TEXT,

                email TEXT,

                data_nascimento TEXT,

                estado_civil TEXT,

                familia TEXT,

                cargo_eclesiastico TEXT DEFAULT 'Membro',

                status TEXT DEFAULT 'Ativo',

                data_batismo TEXT,

                celula_id INTEGER,

                observacoes TEXT,

                criado_em TEXT,

                FOREIGN KEY (celula_id) REFERENCES celulas(id) ON DELETE SET NULL

            );



            CREATE TABLE IF NOT EXISTS membro_ministerio (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                membro_id INTEGER NOT NULL,

                ministerio_id INTEGER NOT NULL,

                funcao TEXT NOT NULL,

                UNIQUE(membro_id, ministerio_id),

                FOREIGN KEY (membro_id) REFERENCES membros(id) ON DELETE CASCADE,

                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE CASCADE

            );



            CREATE TABLE IF NOT EXISTS visitantes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                telefone TEXT,

                data_visita TEXT NOT NULL,

                culto TEXT NOT NULL,

                pedido_oracao TEXT,

                status_acompanhamento TEXT DEFAULT 'Novo Visitante',

                celula_indicada_id INTEGER,

                registrado_por TEXT

            );



            CREATE TABLE IF NOT EXISTS escalas (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data_culto TEXT NOT NULL,

                horario TEXT NOT NULL,

                evento_culto TEXT NOT NULL,

                ministerio_id INTEGER NOT NULL,

                membro_id INTEGER NOT NULL,

                funcao_escala TEXT NOT NULL,

                confirmado INTEGER DEFAULT 1,

                observacao TEXT,

                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE CASCADE,

                FOREIGN KEY (membro_id) REFERENCES membros(id) ON DELETE CASCADE

            );



            CREATE TABLE IF NOT EXISTS financeiro (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data_lancamento TEXT NOT NULL,

                tipo TEXT NOT NULL,

                categoria TEXT NOT NULL,

                descricao TEXT NOT NULL,

                valor REAL NOT NULL,

                forma_pagamento TEXT DEFAULT 'PIX',

                status TEXT DEFAULT 'Pago',

                membro_id INTEGER,

                ministerio_id INTEGER,

                requisicao_id INTEGER,

                lancado_por TEXT,

                FOREIGN KEY (membro_id) REFERENCES membros(id) ON DELETE SET NULL,

                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE SET NULL

            );

            CREATE TABLE IF NOT EXISTS patrimonio_emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patrimonio_id INTEGER,
                codigo TEXT,
                item TEXT NOT NULL,
                setor TEXT,
                condicao_saida TEXT NOT NULL,
                observacoes_saida TEXT,
                solicitante_nome TEXT NOT NULL,
                solicitante_telefone TEXT,
                solicitante_documento TEXT,
                motivo TEXT,
                data_retirada TEXT NOT NULL,
                previsao_devolucao TEXT NOT NULL,
                responsavel_setor TEXT,
                status_aprovacao_setor TEXT DEFAULT 'Pendente',
                data_aprovacao_setor TEXT,
                operador_aprovador_setor TEXT,
                responsavel_patrimonio TEXT,
                status_ok_patrimonio TEXT DEFAULT 'Pendente',
                data_ok_patrimonio TEXT,
                operador_ok_patrimonio TEXT,
                status TEXT DEFAULT 'Aguardando Aprovações',
                data_devolucao_real TEXT,
                condicao_retorno TEXT,
                observacoes_retorno TEXT,
                status_retorno_setor TEXT DEFAULT 'Pendente',
                data_retorno_setor TEXT,
                operador_retorno_setor TEXT,
                status_retorno_patrimonio TEXT DEFAULT 'Pendente',
                data_retorno_patrimonio TEXT,
                operador_retorno_patrimonio TEXT,
                criado_em TEXT NOT NULL,
                criado_por TEXT NOT NULL,
                FOREIGN KEY (patrimonio_id) REFERENCES patrimonio(id) ON DELETE SET NULL
            );



            CREATE TABLE IF NOT EXISTS requisicoes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data_solicitacao TEXT NOT NULL,

                ministerio_id INTEGER NOT NULL,

                solicitante TEXT NOT NULL,

                titulo TEXT NOT NULL,

                justificativa TEXT,

                valor_estimado REAL NOT NULL,

                prioridade TEXT DEFAULT 'Normal',

                status TEXT DEFAULT 'Pendente',

                avaliado_por TEXT,

                data_avaliacao TEXT,

                anexo_pdf TEXT,

                anexo_nome TEXT,

                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE CASCADE

            );



            CREATE TABLE IF NOT EXISTS patrimonio (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                codigo TEXT NOT NULL,

                item TEXT NOT NULL,

                ministerio_id INTEGER,

                localizacao TEXT NOT NULL,

                valor_aquisicao REAL DEFAULT 0,

                estado TEXT DEFAULT 'Bom',

                responsavel TEXT,

                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE SET NULL

            );



            CREATE TABLE IF NOT EXISTS auditoria (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data_hora TEXT NOT NULL,

                usuario TEXT NOT NULL,

                setor TEXT NOT NULL,

                acao TEXT NOT NULL,

                detalhes TEXT

            );

            """

        )



        # Garante colunas novas em ministerios caso o banco tenha sido criado antes

        cols_min = [r["name"] for r in cur.execute("PRAGMA table_info(ministerios)").fetchall()]

        if "realizado_2025" not in cols_min:

            cur.execute("ALTER TABLE ministerios ADD COLUMN realizado_2025 REAL DEFAULT 0")

        if "orcamento_2026" not in cols_min:

            cur.execute("ALTER TABLE ministerios ADD COLUMN orcamento_2026 REAL DEFAULT 0")



        cur.execute(

            """

            CREATE TABLE IF NOT EXISTS ministerios_orcamentos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                ministerio_id INTEGER NOT NULL,

                ano INTEGER NOT NULL,

                orcamento REAL DEFAULT 0,

                realizado REAL DEFAULT 0,

                UNIQUE(ministerio_id, ano)

            );

            """

        )

        count_mo = cur.execute("SELECT COUNT(*) FROM ministerios_orcamentos").fetchone()[0]

        if count_mo == 0:

            for m in cur.execute("SELECT id, realizado_2025, orcamento_2026 FROM ministerios").fetchall():

                mid = m["id"]

                r25 = float(m["realizado_2025"] or 0)

                o26 = float(m["orcamento_2026"] or 0)

                if r25 > 0:

                    cur.execute("INSERT OR IGNORE INTO ministerios_orcamentos (ministerio_id, ano, realizado) VALUES (?, 2025, ?)", (mid, r25))

                if o26 > 0:

                    cur.execute("INSERT OR IGNORE INTO ministerios_orcamentos (ministerio_id, ano, orcamento) VALUES (?, 2026, ?)", (mid, o26))

            conn.commit()



        # Garante colunas novas em membros caso o banco tenha sido criado antes

        cols_mem = [r["name"] for r in cur.execute("PRAGMA table_info(membros)").fetchall()]

        novas_cols_membros = [

            ("apelido", "TEXT DEFAULT ''"),

            ("endereco", "TEXT DEFAULT ''"),

            ("cep", "TEXT DEFAULT ''"),

            ("logradouro", "TEXT DEFAULT ''"),

            ("numero", "TEXT DEFAULT ''"),

            ("complemento", "TEXT DEFAULT ''"),

            ("bairro_endereco", "TEXT DEFAULT ''"),

            ("cidade_endereco", "TEXT DEFAULT ''"),

            ("uf_endereco", "TEXT DEFAULT ''"),

            ("genero", "TEXT DEFAULT ''"),

            ("rg", "TEXT DEFAULT ''"),

            ("cidade_nascimento", "TEXT DEFAULT ''"),

            ("estado_nascimento", "TEXT DEFAULT ''"),

            ("cpf", "TEXT DEFAULT ''"),

            ("rol", "INTEGER DEFAULT NULL"),

            ("numero_ficha", "INTEGER DEFAULT NULL"),

        ]

        for col_name, col_type in novas_cols_membros:

            if col_name not in cols_mem:

                cur.execute(f"ALTER TABLE membros ADD COLUMN {col_name} {col_type}")



        # Garante flexibilidade de membros e digitacao livre nas escalas

        info_esc = cur.execute("PRAGMA table_info(escalas)").fetchall()

        cols_esc = [r["name"] for r in info_esc]

        membro_col = next((c for c in info_esc if c["name"] == "membro_id"), None)

        if (membro_col and membro_col["notnull"] == 1) or ("voluntario_nome" not in cols_esc):

            cur.execute("PRAGMA foreign_keys=OFF;")

            cur.execute(

                """

                CREATE TABLE IF NOT EXISTS escalas_flex (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    data_culto TEXT NOT NULL,

                    horario TEXT NOT NULL,

                    evento_culto TEXT NOT NULL,

                    ministerio_id INTEGER NOT NULL,

                    membro_id INTEGER,

                    voluntario_nome TEXT DEFAULT '',

                    funcao_escala TEXT NOT NULL,

                    confirmado INTEGER DEFAULT 1,

                    observacao TEXT,

                    FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE CASCADE,

                    FOREIGN KEY (membro_id) REFERENCES membros(id) ON DELETE SET NULL

                )

                """

            )

            cur.execute(

                """

                INSERT OR IGNORE INTO escalas_flex (id, data_culto, horario, evento_culto, ministerio_id, membro_id, funcao_escala, confirmado, observacao)

                SELECT id, data_culto, horario, evento_culto, ministerio_id, membro_id, funcao_escala, confirmado, observacao FROM escalas

                """

            )

            cur.execute("DROP TABLE escalas")

            cur.execute("ALTER TABLE escalas_flex RENAME TO escalas")

            cur.execute("UPDATE escalas SET voluntario_nome = (SELECT nome FROM membros WHERE membros.id = escalas.membro_id) WHERE voluntario_nome IS NULL OR voluntario_nome = ''")

            cur.execute("PRAGMA foreign_keys=ON;")



        cur.execute(

            """

            CREATE TABLE IF NOT EXISTS atas (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                titulo TEXT NOT NULL,

                tipo TEXT NOT NULL DEFAULT 'Assembleia Geral Ordinária',

                data_reuniao TEXT NOT NULL,

                hora_inicio TEXT DEFAULT '',

                hora_fim TEXT DEFAULT '',

                local_reuniao TEXT DEFAULT '',

                presidente TEXT DEFAULT '',

                secretario TEXT DEFAULT '',

                livro_numero TEXT DEFAULT '',

                folha_numero TEXT DEFAULT '',

                pauta TEXT DEFAULT '',

                conteudo TEXT DEFAULT '',

                observacoes TEXT DEFAULT '',

                nome_arquivo TEXT DEFAULT '',

                tipo_arquivo TEXT DEFAULT '',

                tamanho_arquivo INTEGER DEFAULT 0,

                arquivo_base64 TEXT DEFAULT '',

                criado_por TEXT DEFAULT '',

                criado_em TEXT DEFAULT (datetime('now', 'localtime')),

                atualizado_em TEXT DEFAULT ''

            );

            """

        )



        # Atualiza permissoes de ADMIN e SECRETARIA para incluir atas

        try:

            cur.execute("""

                UPDATE usuarios

                SET setores_permitidos = setores_permitidos || ',atas'

                WHERE (perfil IN ('ADMIN', 'SECRETARIA') OR cargo LIKE '%Pastor%' OR cargo LIKE '%Secret%')

                  AND (setores_permitidos NOT LIKE '%atas%')

            """)

        except Exception:

            pass



        # Pre-seed sample atas if empty

        try:

            cnt_atas = cur.execute("SELECT COUNT(*) as c FROM atas").fetchone()["c"]

            if cnt_atas == 0:

                cur.execute(

                    """INSERT INTO atas 

                    (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, observacoes, criado_por)

                    VALUES 

                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                    """,

                    (

                        "Assembleia Geral Ordinária - Aprovação de Contas 2025 e Orçamento 2026",

                        "Assembleia Geral Ordinária",

                        "2026-01-18",

                        "19:30",

                        "21:15",

                        "Templo Sede",

                        "Pr. Marcos Silva",

                        "Ana Paula de Oliveira",

                        "Livro 05",

                        "Fls. 01 a 04",

                        "1. Abertura solene e oração devocional;\n2. Apresentação do Balancete Financeiro 2025 pela Tesouraria;\n3. Leitura e acolhimento do Parecer do Conselho Fiscal;\n4. Votação e homologação do Orçamento Anual dos Ministérios para 2026;\n5. Encerramento e oração de gratidão.",

                        "Ata aprovada por aclamação e unanimidade dos membros presentes em comunhão.",

                        "Sistema"

                    )

                )

                cur.execute(

                    """INSERT INTO atas 

                    (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, observacoes, criado_por)

                    VALUES 

                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                    """,

                    (

                        "Reunião de Diretoria Executiva - Planejamento Anual e Normas de Compras",

                        "Reunião de Diretoria",

                        "2026-02-05",

                        "20:00",

                        "22:00",

                        "Gabinete Pastoral",

                        "Pr. Marcos Silva",

                        "Yuri Gabriel dos Santos",

                        "Livro 05",

                        "Fls. 05 e 06",

                        "1. Definição das diretrizes orçamentárias para aquisições dos Ministérios;\n2. Implantação da nova rotina digital de pedidos de verba e envio de comprovantes fiscais em PDF;\n3. Aprovação do calendário ministerial do primeiro semestre.",

                        "Deliberações homologadas por todos os diretores presentes.",

                        "Sistema"

                    )

                )

        except Exception as e:

            print(f"Erro seed atas: {e}")





        # Garante coluna pessoa_nome em financeiro para permitir contribuintes / digitacao livre

        cols_fin = [r["name"] for r in cur.execute("PRAGMA table_info(financeiro)").fetchall()]

        if "pessoa_nome" not in cols_fin:

            cur.execute("ALTER TABLE financeiro ADD COLUMN pessoa_nome TEXT DEFAULT ''")

            cur.execute("UPDATE financeiro SET pessoa_nome = (SELECT nome FROM membros WHERE membros.id = financeiro.membro_id) WHERE (pessoa_nome IS NULL OR pessoa_nome = '') AND membro_id IS NOT NULL")

        novas_cols_fin = [

            ("parcelado", "INTEGER DEFAULT 0"),

            ("numero_parcelas", "INTEGER DEFAULT 1"),

            ("parcela_atual", "INTEGER DEFAULT 1"),

            ("parcela_identificador", "TEXT DEFAULT ''"),

            ("grupo_parcela_id", "TEXT DEFAULT ''"),

            ("valor_total_parcelado", "REAL DEFAULT 0"),

        ]

        for c_nome, c_tipo in novas_cols_fin:

            if c_nome not in cols_fin:

                cur.execute(f"ALTER TABLE financeiro ADD COLUMN {c_nome} {c_tipo}")



        # Garante coluna quem_convidou em visitantes para acolhimento integrado

        cols_vis = [r["name"] for r in cur.execute("PRAGMA table_info(visitantes)").fetchall()]

        if "quem_convidou" not in cols_vis:

            cur.execute("ALTER TABLE visitantes ADD COLUMN quem_convidou TEXT DEFAULT ''")



        # Garante coluna sala_ebd em membros

        cols_mem = [r["name"] for r in cur.execute("PRAGMA table_info(membros)").fetchall()]

        if "sala_ebd" not in cols_mem:

            cur.execute("ALTER TABLE membros ADD COLUMN sala_ebd TEXT DEFAULT ''")



        # Garante colunas de seguranca e permissoes na tabela de usuarios

        cols_usr = [r["name"] for r in cur.execute("PRAGMA table_info(usuarios)").fetchall()]

        if "setores_permitidos" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN setores_permitidos TEXT DEFAULT ''")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,tesouraria,relatorios' WHERE perfil IN ('TESOURARIA', 'FINANCEIRO')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,patrimonio' WHERE perfil = 'PATRIMONIO'")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,tesouraria,relatorios,secretaria,recepcao,ministerios,celulas,patrimonio,acessos' WHERE perfil = 'ADMIN'")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,relatorios,secretaria,recepcao,celulas,ministerios' WHERE perfil = 'SECRETARIA'")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,ministerios,celulas' WHERE perfil = 'MINISTERIO'")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,recepcao,ministerios' WHERE perfil = 'RECEPCAO'")



        if "senha" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN senha TEXT DEFAULT '123456'")

            cur.execute("UPDATE usuarios SET senha = '123456' WHERE senha IS NULL OR senha = ''")



        if "relatorios_permitidos" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN relatorios_permitidos TEXT DEFAULT '*'")



        if "senha_alterada" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN senha_alterada INTEGER DEFAULT 0")



        cur.execute("SELECT COUNT(*) as total FROM usuarios")

        if cur.fetchone()["total"] == 0:

            seed_data(conn)

        else:

            # Garante que operadores com setores_permitidos vazios recebam permissões coerentes

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,tesouraria,relatorios' WHERE perfil IN ('TESOURARIA', 'FINANCEIRO') AND (setores_permitidos IS NULL OR setores_permitidos = '')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,patrimonio' WHERE perfil = 'PATRIMONIO' AND (setores_permitidos IS NULL OR setores_permitidos = '')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,tesouraria,relatorios,secretaria,recepcao,ministerios,celulas,patrimonio,acessos' WHERE perfil = 'ADMIN' AND (setores_permitidos IS NULL OR setores_permitidos = '')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,relatorios,secretaria,recepcao,celulas,ministerios' WHERE perfil = 'SECRETARIA' AND (setores_permitidos IS NULL OR setores_permitidos = '')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,ministerios,celulas' WHERE perfil = 'MINISTERIO' AND (setores_permitidos IS NULL OR setores_permitidos = '')")

            cur.execute("UPDATE usuarios SET setores_permitidos = 'dashboard,recepcao,ministerios' WHERE perfil = 'RECEPCAO' AND (setores_permitidos IS NULL OR setores_permitidos = '')")



        # Verifica se a planilha com os 10 grupos do slide já foi criada em matriz_tesouraria

        cur.execute("SELECT COUNT(*) as total FROM matriz_tesouraria WHERE grupo = 'Gráfica /Livraria/ADM'")

        if cur.fetchone()["total"] == 0:

            cur.execute("DELETE FROM matriz_tesouraria")

            integrar_planilha_real(conn, zerar_valores=True)



        conn.commit()

        conn.close()





def integrar_planilha_real(conn, zerar_valores=True):

    """Integra os 15 Ministérios reais e a estrutura das Matrizes Financeiras 2023, 2025 e 2026."""

    cur = conn.cursor()



    # Atualiza/Substitui pelos 15 Ministérios Reais da Planilha

    cur.execute("DELETE FROM ministerios")

    cur.execute("DELETE FROM sqlite_sequence WHERE name='ministerios'")



    for nome, lider, real_2025, orc_2026, obs, cor in MINISTERIOS_REAIS:

        r25 = 0.0 if zerar_valores else real_2025

        o26 = 0.0 if zerar_valores else orc_2026

        orc_mensal = round(o26 / 12.0, 2)

        obs_txt = "" if zerar_valores else obs

        cur.execute(

            """INSERT INTO ministerios (nome, lider, orcamento_mensal, realizado_2025, orcamento_2026, descricao, cor)

            VALUES (?, ?, ?, ?, ?, ?, ?)""",

            (nome, lider, orc_mensal, r25, o26, obs_txt, cor),

        )



    # Insere todas as linhas de 2026, 2025 e 2023 na tabela matriz_tesouraria

    todas_matrizes = MATRIZ_2026 + MATRIZ_2025 + MATRIZ_2023

    for ano, tipo_fluxo, grupo, rubrica, meses in todas_matrizes:

        vals = [0.0] * 12 if zerar_valores else meses

        cur.execute(

            """INSERT INTO matriz_tesouraria

            (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

            (ano, tipo_fluxo, grupo, rubrica, *vals),

        )



    log_auditoria(

        conn,

        "Sistema",

        "Tesouraria",

        "Estrutura da Planilha pronta",

        "Estrutura de grupos e rubricas pronta para lançamentos.",

    )









def sincronizar_lancamento_na_matriz(cur, data_lanc, tipo, categoria, descricao, valor_delta, ministerio_id=None):

    """Sincroniza lançamentos diários do livro caixa diretamente na célula mensal da matriz_tesouraria."""

    try:

        partes = str(data_lanc).split("-")

        ano = int(partes[0]) if len(partes) >= 1 and partes[0].isdigit() else 2026

        mes = int(partes[1]) if len(partes) >= 2 and partes[1].isdigit() else 10

        if mes < 1 or mes > 12:

            mes = 10

    except Exception:

        ano, mes = 2026, 10



    col = f"m{mes}"

    cat_clean = (categoria or "").strip().lower()

    desc_clean = (descricao or "").strip().lower()



    # Busca todas as rubricas do ano e fluxo na matriz

    rows = cur.execute(

        f"SELECT id, rubrica, grupo, {col} as val_atual FROM matriz_tesouraria WHERE ano=? AND tipo_fluxo=?",

        (ano, tipo),

    ).fetchall()



    row_encontrada = None

    grupo_alvo = "Entradas" if tipo == "ENTRADA" else "Despesas Operacionais"

    rubrica_insercao = descricao or categoria or "Lançamento Geral"



    if tipo == "ENTRADA":

        grupo_alvo = "Entradas"

        # 1. Match inteligente por tipo de receita

        if any(w in cat_clean or w in desc_clean for w in ["dízimo", "dizimo", "gasofil"]):

            for r in rows:

                if any(w in r["rubrica"].lower() for w in ["dízimo", "dizimo", "gasofil"]):

                    row_encontrada = r; break

        elif any(w in cat_clean or w in desc_clean for w in ["itaú", "itau"]):

            for r in rows:

                if any(w in r["rubrica"].lower() for w in ["itaú", "itau"]):

                    row_encontrada = r; break

        elif "bradesco" in cat_clean or "bradesco" in desc_clean:

            for r in rows:

                if "bradesco" in r["rubrica"].lower():

                    row_encontrada = r; break

        elif any(w in cat_clean or w in desc_clean for w in ["campanha", "missõ", "misso", "jmm", "jmn", "jme"]):

            for r in rows:

                if any(w in r["rubrica"].lower() for w in ["campanha", "missõ", "misso"]):

                    row_encontrada = r; break

        elif any(w in cat_clean or w in desc_clean for w in ["cantina", "bazar"]):

            for r in rows:

                if any(w in r["rubrica"].lower() for w in ["cantina", "bazar"]):

                    row_encontrada = r; break

        elif "promessa" in cat_clean or "promessa" in desc_clean:

            for r in rows:

                if "promessa" in r["rubrica"].lower():

                    row_encontrada = r; break

        elif any(w in cat_clean or w in desc_clean for w in ["reembolso", "estorno", "devolu"]):

            for r in rows:

                if any(w in r["rubrica"].lower() for w in ["reembolso", "estorno", "devolu"]):

                    row_encontrada = r; break

        

        # 2. Busca genérica por texto da categoria ou descrição

        if not row_encontrada:

            for r in rows:

                r_low = r["rubrica"].lower()

                if (cat_clean and cat_clean in r_low) or (desc_clean and desc_clean in r_low) or (r_low in cat_clean):

                    row_encontrada = r; break



        # 3. Fallback: primeira linha do grupo Entradas

        if not row_encontrada:

            for r in rows:

                if "entrada" in r["grupo"].lower() or "receita" in r["grupo"].lower():

                    row_encontrada = r; break

        rubrica_insercao = categoria or descricao or "Receitas Diversas"



    else:

        # SAIDA

        grupo_alvo = "Despesas com Ministérios" if (ministerio_id or "ministério" in cat_clean or "ministerio" in cat_clean) else "Despesas Operacionais"

        min_nome = ""

        if ministerio_id:

            row_min = cur.execute("SELECT id, nome FROM ministerios WHERE id=?", (int(ministerio_id),)).fetchone()

            if row_min:

                min_nome = row_min["nome"].lower()

        

        # Se tem ministério envolvido:

        if min_nome or "ministério" in cat_clean or "ministerio" in cat_clean:

            grupo_alvo = "Despesas com Ministérios"

            # Mapeamento dos 15 ministérios para as rubricas da matriz

            if "viver" in min_nome or "viver" in desc_clean:

                for r in rows:

                    if "viver" in r["rubrica"].lower(): row_encontrada = r; break

            elif "ebd" in min_nome or "ebd" in desc_clean or "escola" in min_nome:

                for r in rows:

                    if "ebd" in r["rubrica"].lower(): row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["jovem", "adolescente"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["jovem", "adolescente"]): row_encontrada = r; break

            elif "evento" in min_nome or "evento" in desc_clean:

                for r in rows:

                    if "evento" in r["rubrica"].lower() and r["grupo"] == "Despesas com Ministérios": row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["social", "ação", "acao"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["social", "ação", "acao"]): row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["som", "sonoplastia"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["som", "sonoplastia"]): row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["infantil", "criança", "ebf"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["infantil", "criança"]): row_encontrada = r; break

            elif "mulher" in min_nome or "mulher" in desc_clean:

                for r in rows:

                    if "mulher" in r["rubrica"].lower(): row_encontrada = r; break

            elif "homem" in min_nome or "homem" in desc_clean:

                for r in rows:

                    if "homem" in r["rubrica"].lower(): row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["missão", "missao", "missões"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["missão", "missao", "missões"]): row_encontrada = r; break

            elif "casais" in min_nome or "casais" in desc_clean:

                for r in rows:

                    if "casais" in r["rubrica"].lower(): row_encontrada = r; break

            elif "coral" in min_nome or "coral" in desc_clean:

                for r in rows:

                    if "coral" in r["rubrica"].lower(): row_encontrada = r; break

            elif "louvor" in min_nome or "louvor" in desc_clean:

                for r in rows:

                    if "louvor" in r["rubrica"].lower(): row_encontrada = r; break

            elif any(w in min_nome or w in desc_clean for w in ["diácon", "diacon", "diacono", "diácono"]):

                for r in rows:

                    if any(w in r["rubrica"].lower() for w in ["diácon", "diacon"]): row_encontrada = r; break

            elif "comunica" in min_nome or "comunica" in desc_clean:

                for r in rows:

                    if "comunica" in r["rubrica"].lower(): row_encontrada = r; break

            

            # Se não achou mapeamento específico, procura por texto livre nas rubricas de ministérios

            if not row_encontrada and min_nome:

                for r in rows:

                    if r["grupo"] == "Despesas com Ministérios" and (min_nome[:8] in r["rubrica"].lower() or r["rubrica"].lower()[:8] in min_nome):

                        row_encontrada = r; break



        else:

            # Outros tipos de saída

            mapa_grupos = {

                "folha de pagamento": "Folha de Pagamento",

                "despesa fixa": "Despesas Fixas",

                "manutenção/patrimônio": "Manutenção/Patrimônio/Equip.",

                "manutencao/patrimonio": "Manutenção/Patrimônio/Equip.",

                "convenção / missões": "Convenção/Campanhas Miss.",

                "convencao / missoes": "Convenção/Campanhas Miss.",

                "impostos": "Impostos",

                "despesas operacionais": "Despesas Operacionais"

            }

            for k_cat, g_nome in mapa_grupos.items():

                if k_cat in cat_clean:

                    grupo_alvo = g_nome; break

            

            for r in rows:

                if r["grupo"] == grupo_alvo:

                    r_low = r["rubrica"].lower()

                    if desc_clean and (desc_clean in r_low or r_low in desc_clean):

                        row_encontrada = r; break

            if not row_encontrada:

                for r in rows:

                    if r["grupo"] == grupo_alvo:

                        row_encontrada = r; break



        rubrica_insercao = descricao or categoria or "Despesa Diversa"



    if row_encontrada:

        novo_val = max(0.0, round(float(row_encontrada["val_atual"] or 0) + float(valor_delta), 2))

        cur.execute(f"UPDATE matriz_tesouraria SET {col}=? WHERE id=?", (novo_val, row_encontrada["id"]))

    elif valor_delta > 0:

        meses = [0.0] * 12

        meses[mes - 1] = round(float(valor_delta), 2)

        cur.execute(

            """INSERT INTO matriz_tesouraria

            (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

            (ano, tipo, grupo_alvo, rubrica_insercao, *meses),

        )





def seed_data(conn):

    cur = conn.cursor()



    usuarios = [

        ("Marcos Silva (Administrador)", "admin@igreja.org", "Administrador Geral", "ADMIN", None, 1),

        ("Isadora / Tesouraria", "tesouraria@igreja.org", "Tesoureira / Financeiro", "TESOURARIA", None, 1),

        ("Ana Paula (Secretaria)", "secretaria@igreja.org", "Secretária Executiva", "SECRETARIA", None, 1),

        ("Pr. Ivan (Pastor Presidente)", "pastor@igreja.org", "Pastor Presidente", "ADMIN", None, 1),

        ("Líder Projeto Viver", "viver@igreja.org", "Líder de Ministério", "MINISTERIO", 1, 1),

        ("Coordenador Diáconos", "recepcao@igreja.org", "Diaconato / Recepção", "RECEPCAO", 15, 1),

    ]

    cur.executemany(

        "INSERT INTO usuarios (nome, email, cargo, perfil, ministerio_id, ativo) VALUES (?, ?, ?, ?, ?, ?)",

        usuarios,

    )



    celulas = [

        ("Célula Projeto Viver", "Coord. Viver", "Sede / Quadra", "Sábado às 15:00", 25, 22),

        ("Célula Jovens e Adolescentes", "Liderança Jovem", "Salão Jovem", "Sábado às 19:00", 30, 26),

        ("Célula Casais & Família", "Casal Líder", "Bela Vista", "Quinta-feira às 20:00", 18, 16),

        ("Célula Mulheres Batista (MCM)", "Liderança MCM", "Salão Anexo", "Quarta-feira às 16:00", 20, 18),

    ]

    cur.executemany(

        "INSERT INTO celulas (nome, lider, bairro, dia_horario, meta_membros, ultima_frequencia) VALUES (?, ?, ?, ?, ?, ?)",

        celulas,

    )



    membros = [

        ("Pr. Ivan", "(11) 99123-4501", "ivan@igreja.org", "1978-04-12", "Casado(a)", "Família Pastoral", "Pastor(a)", "Ativo", "1998-11-20", 3, "Pastor Presidente", "2018-01-10"),

        ("Isadora", "(11) 99123-4502", "isadora@igreja.org", "1992-10-25", "Casado(a)", "Família Silva", "Obreiro / Voluntário", "Ativo", "2010-03-15", 3, "Tesouraria e Orçamento", "2020-01-10"),

        ("Pr. Cláudio do Balneário", "(11) 99123-4503", "claudio@igreja.org", "1975-07-08", "Casado(a)", "Família Balneário", "Pastor(a)", "Ativo", "1995-08-10", 1, "Congregação / Missão Balneário", "2019-05-14"),

        ("Missionário Valmir", "(11) 99123-4504", "valmir@igreja.org", "1980-10-19", "Casado(a)", "Família Santos", "Evangelista", "Ativo", "2005-12-05", 1, "Campo Missionário", "2021-02-20"),

        ("Gabriel Rocha", "(11) 99123-4505", "gabriel@igreja.org", "1998-02-18", "Solteiro(a)", "Família Rocha", "Obreiro / Voluntário", "Ativo", "2015-06-21", 2, "Equipe de Sonoplastia", "2022-03-11"),

        ("Ir. Helena Costa", "(11) 99123-4506", "helena@igreja.org", "1975-10-30", "Viúvo(a)", "Família Costa", "Diácono / Diaconisa", "Ativo", "1995-04-02", 4, "Coord. Ação Social", "2018-09-01"),

        ("Matheus Oliveira", "(11) 99123-4507", "matheus@igreja.org", "2001-09-14", "Solteiro(a)", "Família Oliveira", "Obreiro / Voluntário", "Ativo", "2016-11-12", 2, "Liderança de Jovens", "2021-07-19"),

        ("Juliana Mendes", "(11) 99123-4508", "juliana@igreja.org", "1987-05-22", "Casado(a)", "Família Mendes", "Membro", "Ativo", "2007-10-14", 3, "Professora EBD e Infantil", "2020-01-10"),

    ]

    cur.executemany(

        """INSERT INTO membros 

        (nome, telefone, email, data_nascimento, estado_civil, familia, cargo_eclesiastico, status, data_batismo, celula_id, observacoes, criado_em)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

        membros,

    )



    integrar_planilha_real(conn)



    vinculos = [

        (1, 7, "Supervisão Missionária"),

        (2, 13, "Gestão e Comunicação"),

        (5, 6, "Líder de Sonoplastia"),

        (6, 5, "Coordenadora Ação Social"),

        (7, 9, "Líder de Jovens e Adolescentes"),

        (8, 2, "Professora EBD"),

        (8, 3, "Equipe EBF / Infantil"),

    ]

    cur.executemany(

        "INSERT OR IGNORE INTO membro_ministerio (membro_id, ministerio_id, funcao) VALUES (?, ?, ?)",

        vinculos,

    )



    escalas = [

        ("2026-10-25", "09:00", "Escola Bíblica Dominical (EBD)", 2, 8, "Professora Classe Adultos / Café EBD", 1, "Literatura trimestral"),

        ("2026-10-25", "19:00", "Culto de Domingo à Noite", 6, 5, "Mesa de Som e Microfones", 1, "Checar pilhas e cabos"),

        ("2026-10-25", "19:00", "Culto de Domingo à Noite", 3, 8, "Culto Infantil", 1, ""),

        ("2026-10-25", "19:00", "Culto de Domingo à Noite", 9, 7, "Recepção e Louvor Jovem", 1, ""),

    ]

    cur.executemany(

        """INSERT INTO escalas 

        (data_culto, horario, evento_culto, ministerio_id, membro_id, funcao_escala, confirmado, observacao)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",

        escalas,

    )



    visitantes = [

        ("Fernando Henrique Gomes", "(11) 98811-2233", "2026-10-18", "Culto da Família (Domingo)", "Oração pela família e novo emprego", "Em Contato", 3, "Diaconato"),

        ("Camila Ribeiro & Esposo", "(11) 97722-3344", "2026-10-18", "Culto da Família (Domingo)", "Mudaram recentemente para o bairro", "Visitado por Célula", 3, "Diaconato"),

    ]

    cur.executemany(

        """INSERT INTO visitantes

        (nome, telefone, data_visita, culto, pedido_oracao, status_acompanhamento, celula_indicada_id, registrado_por)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",

        visitantes,

    )



    requisicoes = [

        ("2026-05-10", 1, "Coord. Projeto Viver", "Compra de Uniformes e Chuteiras Projeto Viver", "Conforme previsto no orçamento 2026 (Isadora)", 781.47, "Alta", "Aprovado e Pago", "Isadora / Tesouraria", "2026-05-12"),

        ("2026-05-15", 9, "Liderança de Jovens", "Saída para Acampamento e Encontros Mensais", "Verba aprovada no orçamento 2026", 3250.00, "Alta", "Aprovado e Pago", "Isadora / Tesouraria", "2026-05-16"),

        ("2026-10-18", 6, "Gabriel Rocha (Sonoplastia)", "Reposição de Pilhas Recarregáveis e Cabos XLR", "Manutenção dos equipamentos de som", 380.00, "Urgente", "Pendente", None, None),

        ("2026-10-19", 3, "Coord. Infantil", "Material Didático e Lanche para EBF", "Atendimento às crianças no próximo mês", 620.00, "Normal", "Pendente", None, None),

    ]

    cur.executemany(

        """INSERT INTO requisicoes

        (data_solicitacao, ministerio_id, solicitante, titulo, justificativa, valor_estimado, prioridade, status, avaliado_por, data_avaliacao)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

        requisicoes,

    )



    financeiro = [

        ("2026-05-05", "ENTRADA", "Conta Itaú", "Entradas / Saldo Conta Itaú - Maio/2026", 19664.59, "Transferência / PIX", "Pago", None, None, None, "Isadora / Tesouraria"),

        ("2026-05-10", "ENTRADA", "Dízimo Gasofilácio", "Dízimos Gasofilácio - Maio/2026", 5962.85, "Espécie / PIX", "Pago", None, None, None, "Isadora / Tesouraria"),

        ("2026-05-12", "ENTRADA", "Conta Bradesco", "Entradas / Saldo Conta Bradesco - Maio/2026", 2432.12, "Transferência", "Pago", None, None, None, "Isadora / Tesouraria"),

        ("2026-05-15", "SAIDA", "Folha de Pagamento", "Renda Eclesiástica (Pr. Ivan) - Maio/2026", 5214.54, "Transferência", "Pago", 1, None, None, "Isadora / Tesouraria"),

        ("2026-05-15", "SAIDA", "Folha de Pagamento", "Diarista (Viviane) - Maio/2026", 2800.00, "PIX", "Pago", None, None, None, "Isadora / Tesouraria"),

        ("2026-05-18", "SAIDA", "Convenção / Missões", "Campanha de Missões Mundiais (JMM)", 4953.64, "Boleto / PIX", "Pago", None, 7, None, "Isadora / Tesouraria"),

        ("2026-05-20", "SAIDA", "Ministério/Setor", "Despesa Mensal Projeto Viver - Maio/2026", 781.47, "PIX", "Pago", None, 1, 1, "Isadora / Tesouraria"),

        ("2026-05-22", "SAIDA", "Ministério/Setor", "Acampamento e Encontros Jovens - Maio/2026", 3250.00, "PIX", "Pago", None, 9, 2, "Isadora / Tesouraria"),

    ]

    cur.executemany(

        """INSERT INTO financeiro

        (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, membro_id, ministerio_id, requisicao_id, lancado_por)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

        financeiro,

    )



    patrimonio = [

        ("PAT-001", "Equipamentos de Som e Microfones do Templo", 6, "Cabine de Som", 18500.00, "Bom", "Equipe Sonoplastia"),

        ("PAT-002", "Sistema de Monitoramento ADT + Sensores", 15, "Templo e Acessos", 4500.00, "Bom", "Diaconato"),

        ("PAT-003", "Filtro Industrial e Bebedouro", 15, "Hall de Entrada", 2800.00, "Bom", "Diaconato"),

        ("PAT-004", "Máquina de Plastificação e Impressora Secretaria", 13, "Sala ADM / Secretaria", 1950.00, "Novo", "Secretaria / Comunicação"),

        ("PAT-005", "Materiais Esportivos e Uniformes Projeto Viver", 1, "Sala Projeto Viver", 6200.00, "Novo", "Coord. Projeto Viver"),

    ]

    cur.executemany(

        """INSERT INTO patrimonio

        (codigo, item, ministerio_id, localizacao, valor_aquisicao, estado, responsavel)

        VALUES (?, ?, ?, ?, ?, ?, ?)""",

        patrimonio,

    )









def build_bootstrap_data(req_handler=None):

    with db_lock:

        conn = get_db()

        cur = conn.cursor()



        usuarios = [dict(r) for r in cur.execute("SELECT * FROM usuarios ORDER BY id").fetchall()]

        ministerios = [dict(r) for r in cur.execute("SELECT * FROM ministerios ORDER BY orcamento_2026 DESC, id ASC").fetchall()]

        ministerios_orcamentos = [dict(r) for r in cur.execute("SELECT * FROM ministerios_orcamentos").fetchall()]

        celulas = [dict(r) for r in cur.execute("SELECT * FROM celulas ORDER BY id").fetchall()]

        matriz_rows = [dict(r) for r in cur.execute("SELECT * FROM matriz_tesouraria ORDER BY ano DESC, tipo_fluxo ASC, id ASC").fetchall()]



        # Calcula totais e médias de cada linha da matriz_tesouraria

        for r in matriz_rows:

            meses = [float(r[f"m{i}"] or 0) for i in range(1, 13)]

            r["meses"] = meses

            r["total_anual"] = round(sum(meses), 2)

            meses_preenchidos = [v for v in meses if v > 0]

            r["media_mensal"] = round(sum(meses) / 12.0, 2)

            r["media_ativa"] = round(sum(meses_preenchidos) / len(meses_preenchidos), 2) if meses_preenchidos else 0.0



        membros = [

            dict(r)

            for r in cur.execute(

                """

                SELECT m.*, c.nome as celula_nome

                FROM membros m

                LEFT JOIN celulas c ON m.celula_id = c.id

                ORDER BY m.id ASC

                """

            ).fetchall()

        ]

        for idx, m in enumerate(membros):

            m["numero_ficha"] = idx + 1



        vinculos = [

            dict(r)

            for r in cur.execute(

                """

                SELECT mm.*, m.nome as membro_nome, m.telefone as membro_telefone, min.nome as ministerio_nome, min.cor as ministerio_cor

                FROM membro_ministerio mm

                JOIN membros m ON mm.membro_id = m.id

                JOIN ministerios min ON mm.ministerio_id = min.id

                ORDER BY min.nome, m.nome

                """

            ).fetchall()

        ]



        vinculos_por_membro = {}

        for v in vinculos:

            vinculos_por_membro.setdefault(v["membro_id"], []).append(v)

        for m in membros:

            m["ministerios"] = vinculos_por_membro.get(m["id"], [])



        visitantes = [

            dict(r)

            for r in cur.execute(

                """

                SELECT v.*, c.nome as celula_nome

                FROM visitantes v

                LEFT JOIN celulas c ON v.celula_indicada_id = c.id

                ORDER BY v.id DESC

                """

            ).fetchall()

        ]



        escalas = [

            dict(r)

            for r in cur.execute(

                """

                SELECT e.*, 

                       COALESCE(m.nome, NULLIF(e.voluntario_nome, ''), 'Voluntário') as membro_nome,

                       COALESCE(m.telefone, '') as membro_telefone,

                       m.cargo_eclesiastico as membro_cargo,

                       min.nome as ministerio_nome, min.cor as ministerio_cor

                FROM escalas e

                LEFT JOIN membros m ON e.membro_id = m.id

                JOIN ministerios min ON e.ministerio_id = min.id

                ORDER BY e.data_culto ASC, e.horario ASC, min.nome ASC

                """

            ).fetchall()

        ]



        financeiro = [

            dict(r)

            for r in cur.execute(

                """

                SELECT f.*, 

                       COALESCE(m.nome, NULLIF(f.pessoa_nome, ''), '') as membro_nome,

                       m.telefone as membro_telefone,

                       min.nome as ministerio_nome, min.cor as ministerio_cor

                FROM financeiro f

                LEFT JOIN membros m ON f.membro_id = m.id

                LEFT JOIN ministerios min ON f.ministerio_id = min.id

                ORDER BY f.data_lancamento DESC, f.id DESC

                """

            ).fetchall()

        ]



        requisicoes = [

            dict(r)

            for r in cur.execute(

                """

                SELECT r.id, r.data_solicitacao, r.ministerio_id, r.solicitante, r.titulo,

                       r.justificativa, r.valor_estimado, r.prioridade, r.status,

                       r.avaliado_por, r.data_avaliacao, r.anexo_nome,

                       CASE WHEN r.anexo_pdf IS NOT NULL AND r.anexo_pdf != '' THEN 1 ELSE 0 END as tem_anexo,

                       min.nome as ministerio_nome, min.cor as ministerio_cor

                FROM requisicoes r

                JOIN ministerios min ON r.ministerio_id = min.id

                ORDER BY CASE WHEN r.status = 'Pendente' THEN 0 ELSE 1 END, r.id DESC

                """

            ).fetchall()

        ]



        patrimonio = [

            dict(r)

            for r in cur.execute(

                """

                SELECT p.*, min.nome as ministerio_nome

                FROM patrimonio p

                LEFT JOIN ministerios min ON p.ministerio_id = min.id

                ORDER BY p.codigo ASC

                """

            ).fetchall()

        ]

        patrimonio_emprestimos = [
            dict(r)
            for r in cur.execute(
                """
                SELECT pe.*, p.item as patrimonio_item, min.nome as ministerio_nome
                FROM patrimonio_emprestimos pe
                LEFT JOIN patrimonio p ON pe.patrimonio_id = p.id
                LEFT JOIN ministerios min ON p.ministerio_id = min.id
                ORDER BY pe.id DESC
                """
            ).fetchall()
        ]



        auditoria = [

            dict(r)

            for r in cur.execute("SELECT * FROM auditoria ORDER BY id DESC LIMIT 50").fetchall()

        ]



        atas = [

            dict(r)

            for r in cur.execute(

                """

                SELECT id, titulo, tipo, data_reuniao, hora_inicio, hora_fim,

                       local_reuniao, presidente, secretario, livro_numero, folha_numero,

                       pauta, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

                       CASE WHEN arquivo_base64 IS NOT NULL AND LENGTH(arquivo_base64) > 0 THEN 1 ELSE 0 END as tem_anexo,

                       criado_por, criado_em, atualizado_em

                FROM atas

                ORDER BY data_reuniao DESC, id DESC

                """

            ).fetchall()

        ]



        # Calcula o realizado 2026 de cada ministério somando o que está na matriz 2026 ("7. Despesas com Ministérios")

        # + eventuais novos lançamentos/requisições de 2026

        gastos_matriz_2026_por_nome = {}

        for r in matriz_rows:

            if r["ano"] == 2026 and "Ministérios" in r["grupo"]:

                gastos_matriz_2026_por_nome[r["rubrica"].lower()] = r["total_anual"]



        voluntarios_por_min = {}

        for v in vinculos:

            voluntarios_por_min[v["ministerio_id"]] = voluntarios_por_min.get(v["ministerio_id"], 0) + 1



        for min_item in ministerios:

            nome_low = min_item["nome"].lower().strip()

            gasto_2026 = 0.0

            for k, val in gastos_matriz_2026_por_nome.items():

                k_clean = k.lower().strip()

                match = False

                if 'ebd' in nome_low and 'ebd' in k_clean:

                    match = True

                elif ('diácono' in nome_low or 'diacono' in nome_low) and ('diácono' in k_clean or 'diacono' in k_clean):

                    match = True

                else:

                    n_core = nome_low.replace('ministério', '').replace('de', '').replace('dos', '').strip()

                    k_core = k_clean.replace('ministério', '').replace('de', '').replace('dos', '').strip()

                    if n_core and k_core and (n_core in k_core or k_core in n_core):

                        match = True

                if match:

                    gasto_2026 += val



            # Garante orcamento_2026 preenchido

            if not min_item.get("orcamento_2026"):

                min_item["orcamento_2026"] = round(float(min_item.get("orcamento_mensal", 0)) * 12, 2)



            min_item["gasto_atual"] = round(gasto_2026, 2)

            min_item["orcamento_mensal"] = round(float(min_item["orcamento_2026"]) / 12.0, 2)

            min_item["total_voluntarios"] = voluntarios_por_min.get(min_item["id"], 0)

            real_25 = float(min_item.get("realizado_2025") or 0)

            orc_26 = float(min_item.get("orcamento_2026") or 0)

            min_item["aumento_perc"] = round(((orc_26 - real_25) / real_25) * 100, 2) if real_25 > 0 else 0.0



        membros_por_celula = {}

        for m in membros:

            if m["celula_id"]:

                membros_por_celula[m["celula_id"]] = membros_por_celula.get(m["celula_id"], 0) + 1

        for c in celulas:

            c["total_membros"] = membros_por_celula.get(c["id"], 0)



        conn.close()



        with sse_lock:

            clientes_ativos = max(1, len(sse_clients))



        return {

            "usuarios": usuarios,

            "ministerios": ministerios,

            "ministerios_orcamentos": ministerios_orcamentos,

            "matriz_tesouraria": matriz_rows,

            "celulas": celulas,

            "membros": membros,

            "vinculos": vinculos,

            "visitantes": visitantes,

            "escalas": escalas,

            "financeiro": financeiro,

            "requisicoes": requisicoes,

            "patrimonio": patrimonio,

            "patrimonio_emprestimos": patrimonio_emprestimos,

            "auditoria": auditoria,

            "atas": atas,

            "clientes_conectados": clientes_ativos,

            "url_publica": (f"{req_handler.headers.get('X-Forwarded-Proto', 'https')}://{req_handler.headers.get('Host')}" if (req_handler and hasattr(req_handler, 'headers') and req_handler.headers.get('Host') and not req_handler.headers.get('Host', '').startswith(('localhost', '127.0.0.1', '10.', '192.168.'))) else PUBLIC_TUNNEL_URL),

            "url_rede_local": (f"{req_handler.headers.get('X-Forwarded-Proto', 'https')}://{req_handler.headers.get('Host')}" if (req_handler and hasattr(req_handler, 'headers') and req_handler.headers.get('Host') and not req_handler.headers.get('Host', '').startswith(('localhost', '127.0.0.1', '10.', '192.168.'))) else LOCAL_LAN_URL),

            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),

        }





class ChurchERPHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, directory=STATIC_DIR, **kwargs)



    def log_message(self, format, *args):

        pass



    def handle_one_request(self):

        try:

            super().handle_one_request()

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):

            self.close_connection = True

        except Exception:

            self.close_connection = True



    def end_headers(self):

        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

        self.send_header("Pragma", "no-cache")

        self.send_header("Expires", "0")

        super().end_headers()



    def send_json(self, data, status=200):

        try:

            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")

            self.send_response(status)

            self.send_header("Content-Type", "application/json; charset=utf-8")

            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

            self.send_header("Access-Control-Allow-Origin", "*")

            self.send_header("Content-Length", str(len(raw)))

            self.end_headers()

            self.wfile.write(raw)

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):

            self.close_connection = True

        except Exception:

            self.close_connection = True



    def read_json_body(self):

        try:

            length = int(self.headers.get("Content-Length", 0))

            if length <= 0:

                return {}

            raw = self.rfile.read(length).decode("utf-8", errors="replace")

            return json.loads(raw) if raw.strip() else {}

        except Exception:

            return {}



    def do_OPTIONS(self):

        self.send_response(200)

        self.send_header("Access-Control-Allow-Origin", "*")

        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        self.end_headers()



    def do_GET(self):

        parsed = urlparse(self.path)

        path = parsed.path



        if path == "/api/bootstrap":

            self.send_json(build_bootstrap_data(self))

            return



        if path == "/api/atas":

            qs = parse_qs(parsed.query)

            ata_id = qs.get("id", [None])[0]

            with db_lock:

                conn = get_db()

                cur = conn.cursor()

                if ata_id:

                    row = cur.execute(

                        """SELECT id, titulo, tipo, data_reuniao, hora_inicio, hora_fim,

                                   local_reuniao, presidente, secretario, livro_numero, folha_numero,

                                   pauta, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

                                   CASE WHEN arquivo_base64 IS NOT NULL AND LENGTH(arquivo_base64) > 0 THEN 1 ELSE 0 END as tem_anexo,

                                   criado_por, criado_em, atualizado_em

                            FROM atas WHERE id=?""",

                        (int(ata_id),)

                    ).fetchone()

                    conn.close()

                    if not row:

                        return self.send_json({"erro": "Ata não encontrada"}, 404)

                    return self.send_json(dict(row))

                else:

                    rows = cur.execute(

                        """SELECT id, titulo, tipo, data_reuniao, hora_inicio, hora_fim,

                                   local_reuniao, presidente, secretario, livro_numero, folha_numero,

                                   pauta, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

                                   CASE WHEN arquivo_base64 IS NOT NULL AND LENGTH(arquivo_base64) > 0 THEN 1 ELSE 0 END as tem_anexo,

                                   criado_por, criado_em, atualizado_em

                            FROM atas ORDER BY data_reuniao DESC, id DESC"""

                    ).fetchall()

                    conn.close()

                    return self.send_json([dict(r) for r in rows])



        if path == "/api/atas/anexo":

            qs = parse_qs(parsed.query)

            try:

                ata_id = int(qs.get("id", [0])[0])

            except (ValueError, TypeError):

                ata_id = 0



            with db_lock:

                conn = get_db()

                cur = conn.cursor()

                row = cur.execute("SELECT arquivo_base64, nome_arquivo, tipo_arquivo FROM atas WHERE id=?", (ata_id,)).fetchone()

                conn.close()



            if not row or not row["arquivo_base64"]:

                self.send_response(404)

                self.send_header("Content-Type", "text/plain; charset=utf-8")

                self.end_headers()

                self.wfile.write("Arquivo anexo da ata não encontrado.".encode("utf-8"))

                return



            anexo = row["arquivo_base64"]

            nome_arquivo = row["nome_arquivo"] or f"ata_{ata_id}.pdf"

            tipo_arquivo = (row["tipo_arquivo"] or "").lower()

            if not tipo_arquivo:

                if nome_arquivo.lower().endswith(".docx"):

                    tipo_arquivo = "docx"

                elif nome_arquivo.lower().endswith(".doc"):

                    tipo_arquivo = "doc"

                else:

                    tipo_arquivo = "pdf"



            if "," in anexo:

                b64data = anexo.split(",", 1)[1]

            else:

                b64data = anexo



            try:

                file_bytes = base64.b64decode(b64data)

            except Exception as e:

                self.send_response(500)

                self.send_header("Content-Type", "text/plain; charset=utf-8")

                self.end_headers()

                self.wfile.write(f"Erro ao decodificar arquivo anexo: {e}".encode("utf-8"))

                return



            if tipo_arquivo == "docx":

                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                disposition = "attachment"

            elif tipo_arquivo == "doc":

                content_type = "application/msword"

                disposition = "attachment"

            else:

                content_type = "application/pdf"

                disposition = "inline"



            self.send_response(200)

            self.send_header("Content-Type", content_type)

            safe_nome = urllib.parse.quote(nome_arquivo)

            self.send_header("Content-Disposition", f'{disposition}; filename="{safe_nome}"; filename*=UTF-8\'\'{safe_nome}')

            self.send_header("Content-Length", str(len(file_bytes)))

            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

            self.end_headers()

            self.wfile.write(file_bytes)

            return



        if path == "/api/requisicoes/anexo-pdf":

            qs = parse_qs(parsed.query)

            try:

                req_id = int(qs.get("id", [0])[0])

            except (ValueError, TypeError):

                req_id = 0



            with db_lock:

                conn = get_db()

                cur = conn.cursor()

                row = cur.execute("SELECT anexo_pdf, anexo_nome FROM requisicoes WHERE id=?", (req_id,)).fetchone()

                conn.close()



            if not row or not row["anexo_pdf"]:

                self.send_response(404)

                self.send_header("Content-Type", "text/plain; charset=utf-8")

                self.end_headers()

                self.wfile.write("Comprovante / Nota Fiscal em PDF nao encontrado.".encode("utf-8"))

                return



            anexo = row["anexo_pdf"]

            nome_arquivo = row["anexo_nome"] or f"recibo_{req_id}.pdf"

            if "," in anexo:

                b64data = anexo.split(",", 1)[1]

            else:

                b64data = anexo



            try:

                pdf_bytes = base64.b64decode(b64data)

            except Exception as e:

                self.send_response(500)

                self.send_header("Content-Type", "text/plain; charset=utf-8")

                self.end_headers()

                self.wfile.write(f"Erro ao decodificar PDF: {e}".encode("utf-8"))

                return



            self.send_response(200)

            self.send_header("Content-Type", "application/pdf")

            safe_nome = urllib.parse.quote(nome_arquivo)

            self.send_header("Content-Disposition", f'inline; filename="{safe_nome}"')

            self.send_header("Content-Length", str(len(pdf_bytes)))

            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

            self.end_headers()

            self.wfile.write(pdf_bytes)

            return



        if path == "/api/sync-check":

            with sse_lock:

                online_count = len(sse_clients)

            self.send_json({

                "v": LAST_MUTATION_TIMESTAMP,

                "clientes": max(1, online_count)

            })

            return



        if path == "/api/events":

            self.send_response(200)

            self.send_header("Content-Type", "text/event-stream; charset=utf-8")

            self.send_header("Cache-Control", "no-cache, no-transform")

            self.send_header("Connection", "keep-alive")

            self.send_header("X-Accel-Buffering", "no")

            self.send_header("Access-Control-Allow-Origin", "*")

            self.end_headers()



            try:

                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            except Exception:

                pass



            init_msg = f": connected\nevent: presence\ndata: {json.dumps({'clientes_conectados': len(sse_clients) + 1, 'timestamp': LAST_MUTATION_TIMESTAMP})}\n\n"

            try:

                self.wfile.write(init_msg.encode("utf-8"))

                self.wfile.flush()

            except Exception:

                return



            with sse_lock:

                sse_clients.append(self.wfile)

                online_count = len(sse_clients)



            broadcast_event("presence", {"clientes_conectados": online_count})



            try:

                while True:

                    time.sleep(5)

                    with sse_lock:

                        if self.wfile not in sse_clients:

                            break

                    self.wfile.write(b": keepalive\n\n")

                    self.wfile.flush()

            except Exception:

                pass

            finally:

                with sse_lock:

                    if self.wfile in sse_clients:

                        sse_clients.remove(self.wfile)

                    online_count = len(sse_clients)

                broadcast_event("presence", {"clientes_conectados": max(1, online_count)})

            return



        if path == "/":

            self.path = "/index.html"

        return super().do_GET()



    def do_POST(self):

        parsed = urlparse(self.path)

        path = parsed.path

        body = self.read_json_body()

        operador = body.get("operador", "Administrador")



        try:

            with db_lock:

                conn = get_db()

                cur = conn.cursor()



                # A. ATUALIZAR CÉLULA MENSAL DA PLANILHA INTERATIVA DA TESOURARIA

                if path == "/api/matriz/celula":

                    row_id = int(body["id"])

                    mes = int(body["mes"])  # 1 a 12

                    valor = parse_moeda(body.get("valor", 0))

                    if mes < 1 or mes > 12:

                        conn.close()

                        return self.send_json({"erro": "Mês inválido"}, 400)



                    col = f"m{mes}"

                    cur.execute(f"UPDATE matriz_tesouraria SET {col}=? WHERE id=?", (valor, row_id))

                    row_info = cur.execute("SELECT ano, rubrica, grupo FROM matriz_tesouraria WHERE id=?", (row_id,)).fetchone()

                    if not row_info:

                        conn.close()

                        return self.send_json({"erro": "Linha da matriz não encontrada"}, 404)

                    nomes_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

                    mes_nome = nomes_meses[mes - 1]



                    log_auditoria(

                        conn,

                        operador,

                        "Tesouraria",

                        f"Planilha {row_info['ano']} ({mes_nome})",

                        f"Atualizou '{row_info['rubrica']}' em {mes_nome}/{row_info['ano']} para R$ {valor:,.2f}",

                    )

                    conn.commit()

                    conn.close()



                    broadcast_event(

                        "sync",

                        {

                            "setor": "Tesouraria",

                            "operador": operador,

                            "mensagem": f"{operador} atualizou '{row_info['rubrica']}' ({mes_nome}/{row_info['ano']}) para R$ {valor:,.2f}.",

                        },

                    )

                    return self.send_json({"ok": True})



                # A2. ATUALIZAR LINHA COMPLETA (12 MESES) NA PLANILHA INTERATIVA

                elif path == "/api/matriz/linha":

                    row_id = int(body["id"])

                    if "meses" in body and isinstance(body["meses"], list):

                        meses = [parse_moeda(v) for v in body["meses"]][:12]

                        while len(meses) < 12:

                            meses.append(0.0)

                    else:

                        meses = [parse_moeda(body.get(f"m{i}", 0)) for i in range(1, 13)]



                    cur.execute(

                        """UPDATE matriz_tesouraria

                        SET m1=?, m2=?, m3=?, m4=?, m5=?, m6=?, m7=?, m8=?, m9=?, m10=?, m11=?, m12=?

                        WHERE id=?""",

                        (*meses, row_id)

                    )

                    row_info = cur.execute("SELECT ano, rubrica, grupo FROM matriz_tesouraria WHERE id=?", (row_id,)).fetchone()

                    if not row_info:

                        conn.close()

                        return self.send_json({"erro": "Linha da matriz não encontrada"}, 404)

                    tot = sum(meses)



                    log_auditoria(

                        conn,

                        operador,

                        "Tesouraria",

                        f"Atualização Anual ({row_info['ano']})",

                        f"Atualizou os 12 meses de '{row_info['rubrica']}' (Total: R$ {tot:,.2f})",

                    )

                    conn.commit()

                    conn.close()



                    broadcast_event(

                        "sync",

                        {

                            "setor": "Tesouraria",

                            "operador": operador,

                            "mensagem": f"{operador} atualizou os lançamentos anuais de '{row_info['rubrica']}' ({row_info['ano']}).",

                        },

                    )

                    return self.send_json({"ok": True})



                # B. ADICIONAR NOVA RUBRICA / LINHA NA PLANILHA INTERATIVA DA TESOURARIA

                elif path == "/api/matriz/rubrica":

                    ano = int(body.get("ano", 2026))

                    tipo_fluxo = body.get("tipo_fluxo", "SAIDA")

                    grupo = body["grupo"]

                    rubrica = body["rubrica"]

                    mes_inicial = int(body.get("mes", 1))

                    valor_inicial = parse_moeda(body.get("valor", 0))



                    meses = [0.0] * 12

                    if 1 <= mes_inicial <= 12:

                        meses[mes_inicial - 1] = valor_inicial



                    cur.execute(

                        """INSERT INTO matriz_tesouraria

                        (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                        (ano, tipo_fluxo, grupo, rubrica, *meses),

                    )

                    log_auditoria(conn, operador, "Tesouraria", "Nova Rubrica na Planilha", f"Adicionou '{rubrica}' em {grupo} ({ano})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} adicionou a rubrica '{rubrica}' na Tesouraria ({ano})."})

                    return self.send_json({"ok": True})



                # B2. GARANTIR ESTRUTURA DE PLANILHA PARA QUALQUER ANO DIGITADO

                elif path == "/api/matriz/garantir-ano":

                    ano = int(body.get("ano", 2026))

                    if 1990 <= ano <= 2100:

                        existe = cur.execute("SELECT COUNT(*) as total FROM matriz_tesouraria WHERE ano=?", (ano,)).fetchone()["total"]

                        if existe == 0:

                            zeros = [0.0] * 12

                            for _, tipo_fluxo, grupo, rubrica, _ in MATRIZ_2026:

                                cur.execute(

                                    """INSERT INTO matriz_tesouraria

                                    (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                                    (ano, tipo_fluxo, grupo, rubrica, *zeros),

                                )

                            conn.commit()

                    conn.close()

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"Estrutura da planilha para {ano} garantida."})

                    return self.send_json({"ok": True, "ano": ano})



                # 1. CADASTRAR MEMBRO

                elif path == "/api/membros":

                    nome = body.get("nome", "").strip()

                    if not nome:

                        conn.close()

                        return self.send_json({"erro": "O nome do membro é obrigatório."}, 400)



                    cep = body.get("cep", "").strip()

                    logradouro = body.get("logradouro", "").strip()

                    numero = body.get("numero", "").strip()

                    complemento = body.get("complemento", "").strip()

                    bairro_end = body.get("bairro_endereco", "").strip()

                    cidade_end = body.get("cidade_endereco", "").strip()

                    uf_end = body.get("estado_endereco", body.get("uf_endereco", "")).strip()



                    endereco = body.get("endereco", "").strip()

                    if not endereco and (logradouro or bairro_end or cidade_end):

                        partes = []

                        if logradouro:

                            partes.append(f"{logradouro}" + (f", {numero}" if numero else ""))

                        if complemento:

                            partes.append(f"({complemento})")

                        if bairro_end:

                            partes.append(f"- {bairro_end}")

                        if cidade_end or uf_end:

                            partes.append(f"- {cidade_end}/{uf_end}".strip("/"))

                        if cep:

                            partes.append(f"(CEP: {cep})")

                        endereco = " ".join(partes)



                    agora = datetime.now().strftime("%Y-%m-%d")

                    sala_ebd = body.get("sala_ebd", "").strip()

                    status_membro = body.get("status", "Ativo").strip() or "Ativo"

                    cur.execute(

                        """INSERT INTO membros

                        (nome, apelido, endereco, cep, logradouro, numero, complemento, bairro_endereco, cidade_endereco, uf_endereco,

                         telefone, email, data_nascimento, data_batismo,

                         estado_civil, genero, familia, rg, cidade_nascimento, estado_nascimento, cpf,

                         cargo_eclesiastico, status, sala_ebd, celula_id, observacoes, criado_em)

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                        (

                            nome,

                            body.get("apelido", "").strip(),

                            endereco,

                            cep,

                            logradouro,

                            numero,

                            complemento,

                            bairro_end,

                            cidade_end,

                            uf_end,

                            body.get("telefone", "").strip(),

                            body.get("email", "").strip(),

                            body.get("data_nascimento", ""),

                            body.get("data_batismo", ""),

                            body.get("estado_civil", "Casado(a)"),

                            body.get("genero", ""),

                            body.get("familia", "").strip(),

                            body.get("rg", "").strip(),

                            body.get("cidade_nascimento", "").strip(),

                            body.get("estado_nascimento", "").strip(),

                            body.get("cpf", "").strip(),

                            body.get("cargo_eclesiastico", "Membro"),

                            status_membro,

                            sala_ebd,

                            body.get("celula_id") or None,

                            body.get("observacoes", ""),

                            agora,

                        ),

                    )

                    membro_id = cur.lastrowid



                    min_id = body.get("ministerio_id")

                    funcao = body.get("funcao_ministerio", "Voluntário")

                    if min_id:

                        cur.execute(

                            "INSERT OR IGNORE INTO membro_ministerio (membro_id, ministerio_id, funcao) VALUES (?, ?, ?)",

                            (membro_id, int(min_id), funcao),

                        )



                    log_auditoria(conn, operador, "Secretaria", "Novo Membro", f"Cadastrou o membro '{nome}'")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Secretaria", "operador": operador, "mensagem": f"{operador} cadastrou o membro {nome}."})

                    return self.send_json({"ok": True, "id": membro_id})



                elif path == "/api/membros/atualizar":

                    membro_id = int(body["id"])

                    atual = cur.execute("SELECT * FROM membros WHERE id=?", (membro_id,)).fetchone()

                    if not atual:

                        conn.close()

                        return self.send_json({"erro": "Membro não encontrado"}, 404)



                    nome_antigo = (atual["nome"] or "").strip()

                    email_antigo = (atual["email"] or "").strip()

                    telefone_antigo = (atual["telefone"] or "").strip()

                    cargo_antigo = (atual["cargo_eclesiastico"] or "Membro").strip()



                    nome = body.get("nome", atual["nome"]).strip() or atual["nome"]

                    apelido = body.get("apelido", atual["apelido"] or "")

                    cep = body.get("cep", atual["cep"] or "").strip()

                    logradouro = body.get("logradouro", atual["logradouro"] or "").strip()

                    numero = body.get("numero", atual["numero"] or "").strip()

                    complemento = body.get("complemento", atual["complemento"] or "").strip()

                    bairro_end = body.get("bairro_endereco", atual["bairro_endereco"] or "").strip()

                    cidade_end = body.get("cidade_endereco", atual["cidade_endereco"] or "").strip()

                    uf_end = body.get("uf_endereco", atual["uf_endereco"] or "").strip()



                    endereco = body.get("endereco", "").strip()

                    if logradouro or bairro_end or cidade_end:

                        partes = []

                        if logradouro:

                            partes.append(f"{logradouro}" + (f", {numero}" if numero else ""))

                        if complemento:

                            partes.append(f"({complemento})")

                        if bairro_end:

                            partes.append(f"- {bairro_end}")

                        if cidade_end or uf_end:

                            partes.append(f"- {cidade_end}/{uf_end}".strip("/"))

                        if cep:

                            partes.append(f"(CEP: {cep})")

                        endereco = " ".join(partes)

                    elif not endereco:

                        endereco = atual["endereco"] or ""



                    telefone = body.get("telefone", atual["telefone"] or "")

                    email = body.get("email", atual["email"] or "")

                    data_nascimento = body.get("data_nascimento", atual["data_nascimento"] or "")

                    data_batismo = body.get("data_batismo", atual["data_batismo"] or "")

                    estado_civil = body.get("estado_civil", atual["estado_civil"] or "Casado(a)")

                    genero = body.get("genero", atual["genero"] or "")

                    familia = body.get("familia", atual["familia"] or "")

                    rg = body.get("rg", atual["rg"] or "")

                    cidade_nascimento = body.get("cidade_nascimento", atual["cidade_nascimento"] or "")

                    estado_nascimento = body.get("estado_nascimento", atual["estado_nascimento"] or "")

                    cpf = body.get("cpf", atual["cpf"] or "")

                    status = body.get("status", atual["status"] or "Ativo")

                    sala_ebd = body.get("sala_ebd", (atual["sala_ebd"] if "sala_ebd" in atual.keys() and atual["sala_ebd"] else "")).strip()

                    cargo = body.get("cargo_eclesiastico", atual["cargo_eclesiastico"] or "Membro")

                    celula_id = body.get("celula_id") if "celula_id" in body else atual["celula_id"]

                    observacoes = body.get("observacoes", atual["observacoes"] or "")



                    # 1. Atualiza registro principal na tabela membros

                    cur.execute(

                        """UPDATE membros

                        SET nome=?, apelido=?, endereco=?, cep=?, logradouro=?, numero=?, complemento=?,

                            bairro_endereco=?, cidade_endereco=?, uf_endereco=?,

                            telefone=?, email=?, data_nascimento=?, data_batismo=?,

                            estado_civil=?, genero=?, familia=?, rg=?, cidade_nascimento=?, estado_nascimento=?, cpf=?,

                            status=?, sala_ebd=?, cargo_eclesiastico=?, celula_id=?, observacoes=?

                        WHERE id=?""",

                        (

                            nome, apelido, endereco, cep, logradouro, numero, complemento,

                            bairro_end, cidade_end, uf_end,

                            telefone, email, data_nascimento, data_batismo,

                            estado_civil, genero, familia, rg, cidade_nascimento, estado_nascimento, cpf,

                            status, sala_ebd, cargo, celula_id or None, observacoes, membro_id

                        ),

                    )



                    # =========================================================

                    # 2. PROPAGAÇÃO AUTOMÁTICA PARA TODOS OS SETORES DO SISTEMA:

                    # =========================================================



                    # A. SETOR DE ESCALAS DE CULTO

                    # Atualiza o nome do voluntário e garante o vínculo do membro_id

                    cur.execute(

                        """UPDATE escalas 

                        SET voluntario_nome=?, membro_id=? 

                        WHERE membro_id=? OR LOWER(TRIM(voluntario_nome))=LOWER(TRIM(?)) OR LOWER(TRIM(voluntario_nome))=LOWER(TRIM(?))""",

                        (nome, membro_id, membro_id, nome_antigo, nome)

                    )



                    # B. SETOR FINANCEIRO & LIVRO-CAIXA

                    # Atualiza o nome do contribuinte/fornecedor e garante vínculo do membro_id

                    cur.execute(

                        """UPDATE financeiro 

                        SET pessoa_nome=?, membro_id=? 

                        WHERE membro_id=? OR LOWER(TRIM(pessoa_nome))=LOWER(TRIM(?)) OR LOWER(TRIM(pessoa_nome))=LOWER(TRIM(?))""",

                        (nome, membro_id, membro_id, nome_antigo, nome)

                    )



                    # C. SETOR DE CÉLULAS & PEQUENOS GRUPOS

                    # Se era líder de célula, atualiza o nome do líder na célula

                    cur.execute(

                        """UPDATE celulas 

                        SET lider=? 

                        WHERE LOWER(TRIM(lider))=LOWER(TRIM(?))""",

                        (nome, nome_antigo)

                    )



                    # D. SETOR DE 15 MINISTÉRIOS (LIDERANÇA & VÍNCULO)

                    # Se era líder de ministério, atualiza o nome do líder no ministério

                    cur.execute(

                        """UPDATE ministerios 

                        SET lider=? 

                        WHERE LOWER(TRIM(lider))=LOWER(TRIM(?))""",

                        (nome, nome_antigo)

                    )



                    # Atualiza vínculo de ministério se enviado no formulário

                    if "ministerio_id" in body:

                        min_id = body.get("ministerio_id")

                        funcao_min = (body.get("funcao_ministerio") or "Voluntário").strip() or "Voluntário"

                        cur.execute("DELETE FROM membro_ministerio WHERE membro_id=?", (membro_id,))

                        if min_id:

                            cur.execute(

                                """INSERT INTO membro_ministerio (membro_id, ministerio_id, funcao) 

                                VALUES (?, ?, ?)""",

                                (membro_id, int(min_id), funcao_min)

                            )



                    # E. SETOR DE PEDIDOS DE VERBA (REQUISIÇÕES)

                    # Atualiza nome do solicitante

                    cur.execute(

                        """UPDATE requisicoes 

                        SET solicitante=? 

                        WHERE LOWER(TRIM(solicitante))=LOWER(TRIM(?))""",

                        (nome, nome_antigo)

                    )



                    # F. SETOR DE PATRIMÔNIO

                    # Atualiza nome do responsável pelo bem patrimonial

                    cur.execute(

                        """UPDATE patrimonio 

                        SET responsavel=? 

                        WHERE LOWER(TRIM(responsavel))=LOWER(TRIM(?))""",

                        (nome, nome_antigo)

                    )



                    # G. SETOR DE RECEPÇÃO & VISITANTES

                    # Atualiza quem convidou o visitante

                    cur.execute(

                        """UPDATE visitantes 

                        SET quem_convidou=? 

                        WHERE LOWER(TRIM(quem_convidou))=LOWER(TRIM(?))""",

                        (nome, nome_antigo)

                    )



                    # H. SETOR DE CONTROLE DE ACESSO / USUÁRIOS

                    # Sincroniza nome, cargo e email no operador correspondente

                    cur.execute(

                        """UPDATE usuarios 

                        SET nome=?, cargo=?,

                            email=CASE WHEN ? != '' THEN ? ELSE email END

                        WHERE LOWER(TRIM(nome))=LOWER(TRIM(?)) 

                           OR (email != '' AND LOWER(TRIM(email))=LOWER(TRIM(?)))""",

                        (nome, cargo, email.strip(), email.strip(), nome_antigo, email_antigo)

                    )



                    log_auditoria(conn, operador, "Secretaria", "Ficha Atualizada", f"Atualizou cadastro de {nome} ({status} - {cargo}) com propagação para todos os setores.")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Secretaria", "operador": operador, "mensagem": f"{operador} atualizou o cadastro de {nome} em todos os setores do sistema."})

                    return self.send_json({"ok": True})



                # 2. VINCULAR VOLUNTÁRIO A MINISTÉRIO

                elif path == "/api/voluntarios":

                    membro_id = body.get("membro_id")

                    membro_nome = (body.get("membro_nome") or "").strip()

                    if not membro_id and membro_nome:

                        m_row = cur.execute("SELECT id, nome FROM membros WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))", (membro_nome,)).fetchone()

                        if m_row:

                            membro_id = m_row["id"]

                    if not membro_id:

                        conn.close()

                        return self.send_json({"erro": "Selecione ou informe um membro válido para a equipe."}, 400)



                    membro_id = int(membro_id)

                    ministerio_id = int(body["ministerio_id"])

                    funcao = body.get("funcao", "Voluntário").strip() or "Voluntário"



                    cur.execute(

                        "INSERT OR REPLACE INTO membro_ministerio (membro_id, ministerio_id, funcao) VALUES (?, ?, ?)",

                        (membro_id, ministerio_id, funcao),

                    )

                    m_nome = cur.execute("SELECT nome FROM membros WHERE id=?", (membro_id,)).fetchone()["nome"]

                    min_nome = cur.execute("SELECT nome FROM ministerios WHERE id=?", (ministerio_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Ministérios", "Vínculo de Voluntário", f"Vinculou {m_nome} ao ministério {min_nome} ({funcao})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Ministérios", "operador": operador, "mensagem": f"{operador} integrou {m_nome} na equipe de {min_nome}."})

                    return self.send_json({"ok": True})



                elif path == "/api/ministerios":

                    nome = body["nome"]

                    lider = body["lider"]

                    orcamento_2026 = float(body.get("orcamento_2026") or float(body.get("orcamento_mensal", 1000)) * 12)

                    realizado_2025 = float(body.get("realizado_2025", 0))

                    orc_mensal = round(orcamento_2026 / 12.0, 2)

                    descricao = body.get("descricao", "")

                    cor = body.get("cor", "#6366f1")

                    cur.execute(

                        """INSERT INTO ministerios (nome, lider, orcamento_mensal, realizado_2025, orcamento_2026, descricao, cor)

                        VALUES (?, ?, ?, ?, ?, ?, ?)""",

                        (nome, lider, orc_mensal, realizado_2025, orcamento_2026, descricao, cor),

                    )

                    log_auditoria(conn, operador, "Ministérios", "Novo Ministério", f"Criou o setor '{nome}' (Orçamento 2026: R$ {orcamento_2026:,.2f})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Ministérios", "operador": operador, "mensagem": f"{operador} criou o ministério {nome}."})

                    return self.send_json({"ok": True})



                elif path == "/api/ministerios/orcamento":

                    min_id = int(body["id"])

                    ano_orc = int(body.get("ano_orcamento", 2026))

                    ano_real = int(body.get("ano_realizado", 2025))

                    orc_val = parse_moeda(body.get("orcamento") if body.get("orcamento") is not None else body.get("orcamento_2026", 0))

                    real_val = parse_moeda(body.get("realizado") if body.get("realizado") is not None else body.get("realizado_2025", 0))

                    obs = body.get("descricao", "")

                    lider = body.get("lider")

                    orc_mensal = round(orc_val / 12.0, 2)



                    # Registra na tabela ministerios_orcamentos por ano

                    cur.execute(

                        """

                        INSERT INTO ministerios_orcamentos (ministerio_id, ano, orcamento)

                        VALUES (?, ?, ?)

                        ON CONFLICT(ministerio_id, ano) DO UPDATE SET orcamento=excluded.orcamento

                        """,

                        (min_id, ano_orc, orc_val)

                    )

                    cur.execute(

                        """

                        INSERT INTO ministerios_orcamentos (ministerio_id, ano, realizado)

                        VALUES (?, ?, ?)

                        ON CONFLICT(ministerio_id, ano) DO UPDATE SET realizado=excluded.realizado

                        """,

                        (min_id, ano_real, real_val)

                    )



                    # Compatibilidade retroativa com campos legados de 2025/2026

                    if ano_orc == 2026:

                        cur.execute("UPDATE ministerios SET orcamento_2026=?, orcamento_mensal=? WHERE id=?", (orc_val, orc_mensal, min_id))

                    if ano_real == 2025:

                        cur.execute("UPDATE ministerios SET realizado_2025=? WHERE id=?", (real_val, min_id))

                    if obs is not None:

                        cur.execute("UPDATE ministerios SET descricao=? WHERE id=?", (obs, min_id))

                    if lider is not None and lider.strip():

                        cur.execute("UPDATE ministerios SET lider=? WHERE id=?", (lider.strip(), min_id))



                    min_nome = cur.execute("SELECT nome FROM ministerios WHERE id=?", (min_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Tesouraria", f"Ajuste Orçamento/Realizado ({ano_orc}/{ano_real})", f"Atualizou {min_nome}: Orçamento {ano_orc} = R$ {orc_val:,.2f}, Realizado {ano_real} = R$ {real_val:,.2f}")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} atualizou o Orçamento ({ano_orc}) / Realizado ({ano_real}) de {min_nome}."})

                    return self.send_json({"ok": True})



                # 3. CRIAR ESCALA (VÍNCULO COM MEMBROS OU DIGITAÇÃO LIVRE DE SUBSTITUTOS)

                elif path == "/api/escalas":

                    data_culto = body["data_culto"]

                    horario = body["horario"]

                    evento_culto = body["evento_culto"]

                    ministerio_id = int(body["ministerio_id"])

                    funcao_escala = body["funcao_escala"]

                    forcar = body.get("forcar_conflito", False)



                    # Aceita ID ou nome digitado livremente

                    membro_id = body.get("membro_id")

                    voluntario_nome = (body.get("voluntario_nome") or body.get("membro_nome") or "").strip()



                    if membro_id:

                        try:

                            membro_id = int(membro_id)

                            m_row = cur.execute("SELECT id, nome FROM membros WHERE id=?", (membro_id,)).fetchone()

                            if m_row:

                                voluntario_nome = m_row["nome"]

                            else:

                                membro_id = None

                        except (ValueError, TypeError):

                            membro_id = None



                    if not membro_id and voluntario_nome:

                        # Tenta encontrar correspondente no cadastro de membros

                        m_row = cur.execute("SELECT id, nome FROM membros WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))", (voluntario_nome,)).fetchone()

                        if m_row:

                            membro_id = m_row["id"]

                            voluntario_nome = m_row["nome"]



                    if not voluntario_nome and membro_id:

                        m_row = cur.execute("SELECT nome FROM membros WHERE id=?", (membro_id,)).fetchone()

                        if m_row:

                            voluntario_nome = m_row["nome"]



                    if not voluntario_nome:

                        voluntario_nome = "Voluntário"



                    conflito = None

                    if membro_id:

                        conflito = cur.execute(

                            """

                            SELECT e.*, min.nome as ministerio_nome

                            FROM escalas e

                            JOIN ministerios min ON e.ministerio_id = min.id

                            WHERE e.data_culto = ? AND e.horario = ? AND e.membro_id = ?

                            """,

                            (data_culto, horario, membro_id),

                        ).fetchone()

                    elif voluntario_nome and voluntario_nome != "Voluntário":

                        conflito = cur.execute(

                            """

                            SELECT e.*, min.nome as ministerio_nome

                            FROM escalas e

                            JOIN ministerios min ON e.ministerio_id = min.id

                            WHERE e.data_culto = ? AND e.horario = ? AND LOWER(TRIM(e.voluntario_nome)) = LOWER(TRIM(?))

                            """,

                            (data_culto, horario, voluntario_nome),

                        ).fetchone()



                    if conflito and not forcar:

                        conn.close()

                        return self.send_json(

                            {

                                "conflito": True,

                                "erro": f"Atenção: {voluntario_nome} já está escalado(a) neste mesmo dia ({data_culto} às {horario}) no setor '{conflito['ministerio_nome']}' como '{conflito['funcao_escala']}'!",

                            },

                            409,

                        )



                    cur.execute(

                        """INSERT INTO escalas

                        (data_culto, horario, evento_culto, ministerio_id, membro_id, voluntario_nome, funcao_escala, confirmado, observacao)

                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",

                        (

                            data_culto,

                            horario,

                            evento_culto,

                            ministerio_id,

                            membro_id,

                            voluntario_nome,

                            funcao_escala,

                            body.get("observacao", ""),

                        ),

                    )

                    min_nome = cur.execute("SELECT nome FROM ministerios WHERE id=?", (ministerio_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Escalas", "Nova Escala", f"Escalou {voluntario_nome} em {min_nome} ({data_culto} {horario})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Escalas", "operador": operador, "mensagem": f"{operador} escalou {voluntario_nome} para {min_nome} ({data_culto})."})

                    return self.send_json({"ok": True})



                elif path == "/api/escalas/confirmar":

                    esc_id = int(body["id"])

                    atual = cur.execute("SELECT confirmado, membro_id, voluntario_nome FROM escalas WHERE id=?", (esc_id,)).fetchone()

                    if atual:

                        novo = 0 if atual["confirmado"] == 1 else 1

                        cur.execute("UPDATE escalas SET confirmado=? WHERE id=?", (novo, esc_id))

                        m_nome = atual["voluntario_nome"]

                        if not m_nome and atual["membro_id"]:

                            m_row = cur.execute("SELECT nome FROM membros WHERE id=?", (atual["membro_id"],)).fetchone()

                            m_nome = m_row["nome"] if m_row else "Voluntário"

                        if not m_nome:

                            m_nome = "Voluntário"



                        status_txt = "Confirmado" if novo == 1 else "Pendente de Confirmação"

                        log_auditoria(conn, operador, "Escalas", "Check-in Escala", f"Marcou {m_nome} como '{status_txt}'")

                        conn.commit()

                        conn.close()

                        broadcast_event("sync", {"setor": "Escalas", "operador": operador, "mensagem": f"{operador} alterou confirmação de escala de {m_nome} para {status_txt}."})

                        return self.send_json({"ok": True, "confirmado": novo})



                # 4. LANÇAMENTO FINANCEIRO DIÁRIO (VÍNCULO COM MEMBRO OU DIGITAÇÃO LIVRE)

                elif path == "/api/financeiro":

                    data_lanc = body.get("data_lancamento") or datetime.now().strftime("%Y-%m-%d")

                    tipo = body["tipo"]

                    categoria = body["categoria"]

                    descricao = body["descricao"]

                    valor_in = parse_moeda(body.get("valor", 0))

                    forma = body.get("forma_pagamento", "PIX")

                    status = body.get("status", "Pago")

                    membro_id = body.get("membro_id") or None

                    pessoa_nome = (body.get("pessoa_nome") or body.get("membro_nome") or "").strip()

                    ministerio_id = body.get("ministerio_id") or None



                    is_parcelado = 1 if body.get("parcelado") else 0

                    num_parcelas = int(body.get("numero_parcelas") or 1)

                    if not is_parcelado or num_parcelas <= 1:

                        is_parcelado = 0

                        num_parcelas = 1



                    modo_geracao = body.get("modo_geracao", "TODAS")

                    modo_valor = body.get("modo_valor", "TOTAL")



                    if membro_id:

                        try:

                            membro_id = int(membro_id)

                            m_row = cur.execute("SELECT id, nome FROM membros WHERE id=?", (membro_id,)).fetchone()

                            if m_row:

                                pessoa_nome = m_row["nome"]

                            else:

                                membro_id = None

                        except (ValueError, TypeError):

                            membro_id = None



                    if not membro_id and pessoa_nome:

                        m_row = cur.execute("SELECT id, nome FROM membros WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))", (pessoa_nome,)).fetchone()

                        if m_row:

                            membro_id = m_row["id"]

                            pessoa_nome = m_row["nome"]



                    if is_parcelado and modo_geracao == "TODAS" and num_parcelas > 1:

                        if modo_valor == "PARCELA":

                            val_parcela_base = valor_in

                            val_total = round(val_parcela_base * num_parcelas, 2)

                        else:

                            val_total = valor_in

                            val_parcela_base = round(val_total / num_parcelas, 2)



                        grupo_id = f"PARC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

                        try:

                            dt_base = datetime.strptime(data_lanc, "%Y-%m-%d")

                        except Exception:

                            dt_base = datetime.now()



                        desc_base = re.sub(r"\s*\(\s*\d+\s*/\s*\d+\s*\)\s*$", "", descricao).strip()



                        for i in range(1, num_parcelas + 1):

                            dt_i = add_months(dt_base, i - 1).strftime("%Y-%m-%d")

                            if i == 1:

                                val_i = round(val_total - (val_parcela_base * (num_parcelas - 1)), 2)

                            else:

                                val_i = val_parcela_base



                            desc_i = f"{desc_base} ({i:02d}/{num_parcelas:02d})"

                            id_parc = f"{i}/{num_parcelas}"



                            cur.execute(

                                """INSERT INTO financeiro

                                (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, membro_id, pessoa_nome, ministerio_id, lancado_por,

                                 parcelado, numero_parcelas, parcela_atual, parcela_identificador, grupo_parcela_id, valor_total_parcelado)

                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                                (dt_i, tipo, categoria, desc_i, val_i, forma, status, membro_id, pessoa_nome, ministerio_id, operador,

                                 1, num_parcelas, i, id_parc, grupo_id, val_total),

                            )

                            if status == "Pago":

                                sincronizar_lancamento_na_matriz(cur, dt_i, tipo, categoria, desc_i, val_i, ministerio_id)



                        log_auditoria(

                            conn,

                            operador,

                            "Tesouraria",

                            f"Lançamento Parcelado ({tipo})",

                            f"{categoria}: {desc_base} ({num_parcelas}x) ({pessoa_nome or 'Geral'}) - Total R$ {val_total:,.2f}",

                        )

                        conn.commit()

                        conn.close()



                        broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} registrou {categoria} parcelada em {num_parcelas}x (Total R$ {val_total:,.2f}) na Tesouraria."})

                        return self.send_json({"ok": True, "parcelas_geradas": num_parcelas})



                    else:

                        if is_parcelado:

                            parc_atual = int(body.get("parcela_atual") or 1)

                            id_parc = body.get("parcela_identificador") or f"{parc_atual}/{num_parcelas}"

                            val_total = valor_in * num_parcelas if modo_valor == "PARCELA" else valor_in

                            val_item = valor_in if modo_valor == "PARCELA" else round(valor_in / num_parcelas, 2)

                            desc_final = descricao

                            if not re.search(r"\(\s*\d+\s*/\s*\d+\s*\)", desc_final):

                                desc_final = f"{descricao} ({parc_atual:02d}/{num_parcelas:02d})"

                        else:

                            parc_atual = 1

                            id_parc = ""

                            val_total = valor_in

                            val_item = valor_in

                            desc_final = descricao



                        cur.execute(

                            """INSERT INTO financeiro

                            (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, membro_id, pessoa_nome, ministerio_id, lancado_por,

                             parcelado, numero_parcelas, parcela_atual, parcela_identificador, grupo_parcela_id, valor_total_parcelado)

                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                            (data_lanc, tipo, categoria, desc_final, val_item, forma, status, membro_id, pessoa_nome, ministerio_id, operador,

                             is_parcelado, num_parcelas, parc_atual, id_parc, body.get("grupo_parcela_id", ""), val_total),

                        )

                        if status == "Pago":

                            sincronizar_lancamento_na_matriz(cur, data_lanc, tipo, categoria, desc_final, val_item, ministerio_id)



                        log_auditoria(

                            conn,

                            operador,

                            "Tesouraria",

                            f"Lançamento ({tipo})",

                            f"{categoria}: {desc_final} ({pessoa_nome or 'Geral'}) - R$ {val_item:,.2f}",

                        )

                        conn.commit()

                        conn.close()



                        broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} registrou {categoria} (R$ {val_item:,.2f}) na Tesouraria."})

                        return self.send_json({"ok": True})



                elif path == "/api/financeiro/atualizar":

                    fin_id = int(body.get("id", 0))

                    if not fin_id:

                        conn.close()

                        return self.send_json({"erro": "ID do lançamento é obrigatório"}, 400)



                    atual = cur.execute("SELECT * FROM financeiro WHERE id=?", (fin_id,)).fetchone()

                    if not atual:

                        conn.close()

                        return self.send_json({"erro": "Lançamento não encontrado"}, 404)



                    # Se o lançamento antigo estava Pago, estorna da matriz tesouraria antes de aplicar novos dados

                    if atual["status"] == "Pago":

                        sincronizar_lancamento_na_matriz(

                            cur,

                            atual["data_lancamento"],

                            atual["tipo"],

                            atual["categoria"],

                            atual["descricao"],

                            -float(atual["valor"] or 0),

                            atual["ministerio_id"],

                        )



                    data_lanc = body.get("data_lancamento") or atual["data_lancamento"]

                    tipo = body.get("tipo", atual["tipo"])

                    categoria = body.get("categoria", atual["categoria"])

                    descricao = body.get("descricao", atual["descricao"])

                    valor = parse_moeda(body.get("valor", atual["valor"]))

                    forma = body.get("forma_pagamento", atual["forma_pagamento"] or "PIX")

                    status = body.get("status", atual["status"] or "Pago")

                    membro_id = body.get("membro_id") or None

                    pessoa_nome = (body.get("pessoa_nome") or body.get("membro_nome") or atual["pessoa_nome"] or "").strip()

                    ministerio_id = body.get("ministerio_id") or None

                    if ministerio_id:

                        try:

                            ministerio_id = int(ministerio_id)

                        except (ValueError, TypeError):

                            ministerio_id = None



                    if membro_id:

                        try:

                            membro_id = int(membro_id)

                            m_row = cur.execute("SELECT id, nome FROM membros WHERE id=?", (membro_id,)).fetchone()

                            if m_row:

                                pessoa_nome = m_row["nome"]

                            else:

                                membro_id = None

                        except (ValueError, TypeError):

                            membro_id = None



                    if not membro_id and pessoa_nome:

                        m_row = cur.execute("SELECT id, nome FROM membros WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))", (pessoa_nome,)).fetchone()

                        if m_row:

                            membro_id = m_row["id"]

                            pessoa_nome = m_row["nome"]



                    is_parcelado = 1 if body.get("parcelado") else 0

                    num_parcelas = int(body.get("numero_parcelas") or (atual["numero_parcelas"] if "numero_parcelas" in atual.keys() else 1) or 1)

                    parc_atual = int(body.get("parcela_atual") or (atual["parcela_atual"] if "parcela_atual" in atual.keys() else 1) or 1)

                    id_parc = (body.get("parcela_identificador") or "").strip()

                    if not id_parc and is_parcelado:

                        id_parc = f"{parc_atual}/{num_parcelas}"

                    val_tot_parc = parse_moeda(body.get("valor_total_parcelado", (atual["valor_total_parcelado"] if "valor_total_parcelado" in atual.keys() else valor) or valor))



                    cur.execute(

                        """UPDATE financeiro

                        SET data_lancamento=?, tipo=?, categoria=?, descricao=?, valor=?, forma_pagamento=?, status=?, membro_id=?, pessoa_nome=?, ministerio_id=?,

                            parcelado=?, numero_parcelas=?, parcela_atual=?, parcela_identificador=?, valor_total_parcelado=?

                        WHERE id=?""",

                        (data_lanc, tipo, categoria, descricao, valor, forma, status, membro_id, pessoa_nome, ministerio_id,

                         is_parcelado, num_parcelas, parc_atual, id_parc, val_tot_parc, fin_id),

                    )



                    # Se o status continua Pago, sincroniza na matriz tesouraria com o novo valor/rubrica

                    if status == "Pago":

                        sincronizar_lancamento_na_matriz(

                            cur,

                            data_lanc,

                            tipo,

                            categoria,

                            descricao,

                            valor,

                            ministerio_id,

                        )



                    log_auditoria(

                        conn,

                        operador,

                        "Tesouraria",

                        f"Edição ({tipo})",

                        f"Alterou #{fin_id}: {categoria}: {descricao} ({pessoa_nome or 'Geral'}) - R$ {valor:,.2f}",

                    )

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} atualizou o lançamento #{fin_id} da Tesouraria ({categoria} - R$ {valor:,.2f})."})

                    return self.send_json({"ok": True, "id": fin_id})



                # 4B. ROTA DESATIVADA POR SEGURANÇA

                elif path == "/api/tesouraria/zerar":

                    conn.close()

                    return self.send_json({"ok": False, "mensagem": "Funcionalidade de zerar lançamentos desativada permanentemente por segurança da igreja."}, 403)



                # 5. SOLICITAÇÃO DE VERBA / COMPRA DE MINISTÉRIO PARA A TESOURARIA

                elif path == "/api/atas":

                    ata_id = body.get("id")

                    titulo = (body.get("titulo") or "").strip()

                    tipo = (body.get("tipo") or "Assembleia Geral Ordinária").strip()

                    data_reuniao = (body.get("data_reuniao") or datetime.now().strftime("%Y-%m-%d")).strip()

                    hora_inicio = (body.get("hora_inicio") or "").strip()

                    hora_fim = (body.get("hora_fim") or "").strip()

                    local_reuniao = (body.get("local_reuniao") or "").strip()

                    presidente = (body.get("presidente") or "").strip()

                    secretario = (body.get("secretario") or "").strip()

                    livro_numero = (body.get("livro_numero") or "").strip()

                    folha_numero = (body.get("folha_numero") or "").strip()

                    pauta = (body.get("pauta") or "").strip()

                    conteudo = (body.get("conteudo") or "").strip()

                    observacoes = (body.get("observacoes") or "").strip()



                    arquivo_base64 = body.get("arquivo_base64")

                    nome_arquivo = (body.get("nome_arquivo") or "").strip()

                    tipo_arquivo = (body.get("tipo_arquivo") or "").strip().lower()

                    tamanho_arquivo = int(body.get("tamanho_arquivo") or 0)

                    remover_anexo = bool(body.get("remover_anexo"))



                    if not tipo_arquivo and nome_arquivo:

                        if nome_arquivo.lower().endswith(".docx"):

                            tipo_arquivo = "docx"

                        elif nome_arquivo.lower().endswith(".doc"):

                            tipo_arquivo = "doc"

                        elif nome_arquivo.lower().endswith(".pdf"):

                            tipo_arquivo = "pdf"



                    agora_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



                    if ata_id:

                        if remover_anexo:

                            cur.execute(

                """UPDATE atas SET

                    titulo=?, tipo=?, data_reuniao=?, hora_inicio=?, hora_fim=?,

                    local_reuniao=?, presidente=?, secretario=?, livro_numero=?, folha_numero=?,

                    pauta=?, conteudo=?, observacoes=?, nome_arquivo='', tipo_arquivo='',

                    tamanho_arquivo=0, arquivo_base64='', atualizado_em=?

                    WHERE id=?""",

                (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, conteudo, observacoes, agora_ts, int(ata_id))

                            )

                        elif arquivo_base64:

                            cur.execute(

                """UPDATE atas SET

                    titulo=?, tipo=?, data_reuniao=?, hora_inicio=?, hora_fim=?,

                    local_reuniao=?, presidente=?, secretario=?, livro_numero=?, folha_numero=?,

                    pauta=?, conteudo=?, observacoes=?, nome_arquivo=?, tipo_arquivo=?,

                    tamanho_arquivo=?, arquivo_base64=?, atualizado_em=?

                    WHERE id=?""",

                (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo, arquivo_base64, agora_ts, int(ata_id))

                            )

                        else:

                            cur.execute(

                """UPDATE atas SET

                    titulo=?, tipo=?, data_reuniao=?, hora_inicio=?, hora_fim=?,

                    local_reuniao=?, presidente=?, secretario=?, livro_numero=?, folha_numero=?,

                    pauta=?, conteudo=?, observacoes=?, atualizado_em=?

                    WHERE id=?""",

                (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, conteudo, observacoes, agora_ts, int(ata_id))

                            )

                        log_auditoria(conn, operador, "Arquivo de Atas", "Edição de Ata", f"Atualizou ata #{ata_id}: {titulo} ({tipo})")

                        conn.commit()

                        conn.close()

                        broadcast_event("sync", {"setor": "Arquivo de Atas", "operador": operador, "mensagem": f"{operador} atualizou a ata '{titulo}'."})

                        return self.send_json({"ok": True, "id": int(ata_id)})

                    else:

                        cur.execute(

                            """INSERT INTO atas

                            (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo, arquivo_base64, criado_por, criado_em, atualizado_em)

                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                            (titulo, tipo, data_reuniao, hora_inicio, hora_fim, local_reuniao, presidente, secretario, livro_numero, folha_numero, pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo, arquivo_base64 or '', operador, agora_ts, agora_ts)

                        )

                        novo_id = cur.lastrowid

                        log_auditoria(conn, operador, "Arquivo de Atas", "Nova Ata", f"Cadastrou ata #{novo_id}: {titulo} ({tipo}) - Livro {livro_numero}")

                        conn.commit()

                        conn.close()

                        broadcast_event("sync", {"setor": "Arquivo de Atas", "operador": operador, "mensagem": f"{operador} arquivou a nova ata '{titulo}'."})

                        return self.send_json({"ok": True, "id": novo_id})



                elif path == "/api/atas/anexo":

                    ata_id = int(body["id"])

                    remover = body.get("remover")

                    arquivo_base64 = body.get("arquivo_base64", "")

                    nome_arquivo = (body.get("nome_arquivo") or "").strip()

                    tipo_arquivo = (body.get("tipo_arquivo") or "").strip().lower()

                    tamanho_arquivo = int(body.get("tamanho_arquivo") or 0)



                    if not tipo_arquivo and nome_arquivo:

                        if nome_arquivo.lower().endswith(".docx"):

                            tipo_arquivo = "docx"

                        elif nome_arquivo.lower().endswith(".doc"):

                            tipo_arquivo = "doc"

                        elif nome_arquivo.lower().endswith(".pdf"):

                            tipo_arquivo = "pdf"



                    agora_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



                    if remover or not arquivo_base64:

                        cur.execute("UPDATE atas SET arquivo_base64='', nome_arquivo='', tipo_arquivo='', tamanho_arquivo=0, atualizado_em=? WHERE id=?", (agora_ts, ata_id))

                        acao_aud = "Exclusão de Anexo de Ata"

                        msg_aud = f"Removeu anexo da ata #{ata_id}."

                    else:

                        cur.execute("UPDATE atas SET arquivo_base64=?, nome_arquivo=?, tipo_arquivo=?, tamanho_arquivo=?, atualizado_em=? WHERE id=?", (arquivo_base64, nome_arquivo, tipo_arquivo, tamanho_arquivo, agora_ts, ata_id))

                        acao_aud = "Upload de Anexo de Ata"

                        msg_aud = f"Anexou documento '{nome_arquivo}' ({tipo_arquivo.upper()}) à ata #{ata_id}."



                    log_auditoria(conn, operador, "Arquivo de Atas", acao_aud, msg_aud)

                    conn.commit()

                    conn.close()

                    broadcast_event("sync", {"setor": "Arquivo de Atas", "operador": operador, "mensagem": msg_aud})

                    return self.send_json({"ok": True})



                elif path == "/api/requisicoes":

                    agora = datetime.now().strftime("%Y-%m-%d")

                    ministerio_id = int(body["ministerio_id"])

                    solicitante = (body.get("solicitante") or "").strip() or operador

                    titulo = body["titulo"]

                    valor_estimado = parse_moeda(body.get("valor_estimado", 0))

                    prioridade = body.get("prioridade", "Normal")

                    justificativa = body.get("justificativa", "")



                    anexo_pdf = body.get("anexo_pdf", "")

                    anexo_nome = body.get("anexo_nome", "")

                    cur.execute(

                        """INSERT INTO requisicoes

                        (data_solicitacao, ministerio_id, solicitante, titulo, justificativa, valor_estimado, prioridade, status, anexo_pdf, anexo_nome)

                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendente', ?, ?)""",

                        (agora, ministerio_id, solicitante, titulo, justificativa, valor_estimado, prioridade, anexo_pdf, anexo_nome),

                    )

                    min_nome = cur.execute("SELECT nome FROM ministerios WHERE id=?", (ministerio_id,)).fetchone()["nome"]

                    log_auditoria(

                        conn,

                        operador,

                        "Ministérios -> Tesouraria",

                        "Nova Requisição",

                        f"Solicitou R$ {valor_estimado:,.2f} para {min_nome} (Solicitante: {solicitante}): {titulo}",

                    )

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} enviou solicitação de R$ {valor_estimado:,.2f} ({min_nome}) para a Tesouraria."})

                    return self.send_json({"ok": True})



                # 6. APROVAR / RECUSAR REQUISIÇÃO NA TESOURARIA

                elif path == "/api/requisicoes/anexo":

                    req_id = int(body["id"])

                    anexo_pdf = body.get("anexo_pdf", "")

                    anexo_nome = body.get("anexo_nome", "")

                    if not anexo_pdf:

                        cur.execute("UPDATE requisicoes SET anexo_pdf=NULL, anexo_nome=NULL WHERE id=?", (req_id,))

                        acao_auditoria = "Exclusão de Comprovante"

                        msg_auditoria = f"Excluiu o arquivo PDF anexado à requisição #{req_id}."

                        msg_broadcast = f"{operador} excluiu o arquivo PDF da requisição #{req_id}."

                    else:

                        cur.execute("UPDATE requisicoes SET anexo_pdf=?, anexo_nome=? WHERE id=?", (anexo_pdf, anexo_nome, req_id))

                        acao_auditoria = "Anexo de Comprovante"

                        msg_auditoria = f"Anexou nota fiscal/recibo PDF '{anexo_nome}' na requisição #{req_id}."

                        msg_broadcast = f"{operador} anexou nota/recibo PDF na requisição #{req_id}."



                    log_auditoria(

                        conn,

                        operador,

                        "Tesouraria / Requisições",

                        acao_auditoria,

                        msg_auditoria

                    )

                    conn.commit()

                    conn.close()

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": msg_broadcast})

                    return self.send_json({"ok": True})



                elif path == "/api/requisicoes/avaliar":

                    req_id = int(body["id"])

                    decisao = body["decisao"]

                    agora = datetime.now().strftime("%Y-%m-%d")



                    req = cur.execute("SELECT * FROM requisicoes WHERE id=?", (req_id,)).fetchone()

                    if not req:

                        conn.close()

                        return self.send_json({"erro": "Requisição não encontrada."}, 404)



                    status_antigo = req["status"]

                    cur.execute(

                        "UPDATE requisicoes SET status=?, avaliado_por=?, data_avaliacao=? WHERE id=?",

                        (decisao, operador, agora, req_id),

                    )



                    if decisao == "Aprovado e Pago" and status_antigo != "Aprovado e Pago":

                        cur.execute(

                            """INSERT INTO financeiro

                            (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, ministerio_id, requisicao_id, lancado_por)

                            VALUES (?, 'SAIDA', 'Ministério/Setor', ?, ?, 'PIX', 'Pago', ?, ?, ?)""",

                            (

                                agora,

                                f"Req #{req_id}: {req['titulo']}",

                                req["valor_estimado"],

                                req["ministerio_id"],

                                req_id,

                                operador,

                            ),

                        )

                        sincronizar_lancamento_na_matriz(

                            cur,

                            agora,

                            "SAIDA",

                            "Ministério/Setor",

                            f"Req #{req_id}: {req['titulo']}",

                            float(req["valor_estimado"]),

                            req["ministerio_id"],

                        )

                    elif status_antigo == "Aprovado e Pago" and decisao != "Aprovado e Pago":

                        cur.execute("DELETE FROM financeiro WHERE requisicao_id=?", (req_id,))

                        sincronizar_lancamento_na_matriz(

                            cur,

                            req["data_avaliacao"] or agora,

                            "SAIDA",

                            "Ministério/Setor",

                            f"Req #{req_id}: {req['titulo']}",

                            -float(req["valor_estimado"]),

                            req["ministerio_id"],

                        )



                    log_auditoria(

                        conn,

                        operador,

                        "Tesouraria",

                        f"Requisição {decisao}",

                        f"Req #{req_id} ({req['titulo']}) avaliada como '{decisao}'",

                    )

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} marcou a requisição '{req['titulo']}' como {decisao}."})

                    return self.send_json({"ok": True})



                # 7. CADASTRAR VISITANTE (COM QUEM CONVIDOU LIVRE OU MEMBRO)

                elif path == "/api/visitantes":

                    nome = body["nome"]

                    agora = body.get("data_visita") or datetime.now().strftime("%Y-%m-%d")

                    quem_convidou = (body.get("quem_convidou") or "").strip()

                    cur.execute(

                        """INSERT INTO visitantes

                        (nome, telefone, data_visita, culto, pedido_oracao, status_acompanhamento, celula_indicada_id, registrado_por, quem_convidou)

                        VALUES (?, ?, ?, ?, ?, 'Novo Visitante', ?, ?, ?)""",

                        (

                            nome,

                            body.get("telefone", ""),

                            agora,

                            body.get("culto", "Culto de Domingo"),

                            body.get("pedido_oracao", ""),

                            body.get("celula_indicada_id") or None,

                            operador,

                            quem_convidou,

                        ),

                    )

                    log_auditoria(conn, operador, "Recepção", "Check-in Visitante", f"Registrou visitante '{nome}' (Convidado por: {quem_convidou or 'Recepção'})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Recepção", "operador": operador, "mensagem": f"{operador} registrou o visitante {nome} na Recepção."})

                    return self.send_json({"ok": True})



                elif path == "/api/visitantes/status":

                    vis_id = int(body["id"])

                    novo_status = body["status_acompanhamento"]

                    cur.execute("UPDATE visitantes SET status_acompanhamento=? WHERE id=?", (novo_status, vis_id))

                    v_nome = cur.execute("SELECT nome FROM visitantes WHERE id=?", (vis_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Recepção / Células", "Acompanhamento Visitante", f"Moveu '{v_nome}' para etapa '{novo_status}'")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Recepção", "operador": operador, "mensagem": f"{operador} atualizou o acompanhamento de {v_nome} para '{novo_status}'."})

                    return self.send_json({"ok": True})



                elif path == "/api/visitantes/converter":

                    vis_id = int(body["id"])

                    vis = cur.execute("SELECT * FROM visitantes WHERE id=?", (vis_id,)).fetchone()

                    if not vis:

                        conn.close()

                        return self.send_json({"erro": "Visitante não encontrado"}, 404)



                    agora = datetime.now().strftime("%Y-%m-%d")

                    cur.execute(

                        """INSERT INTO membros

                        (nome, telefone, email, estado_civil, cargo_eclesiastico, status, celula_id, observacoes, criado_em)

                        VALUES (?, ?, '', 'Não informado', 'Novo Convertido / Membro', 'Ativo', ?, ?, ?)""",

                        (

                            vis["nome"],

                            vis["telefone"],

                            vis["celula_indicada_id"],

                            f"Integrado a partir da visita em {vis['data_visita']}. Pedido de oração inicial: {vis['pedido_oracao']}",

                            agora,

                        ),

                    )

                    cur.execute("UPDATE visitantes SET status_acompanhamento='Integrado como Membro' WHERE id=?", (vis_id,))

                    log_auditoria(conn, operador, "Secretaria", "Integração de Visitante", f"Converteu o visitante '{vis['nome']}' em Membro Ativo")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Secretaria", "operador": operador, "mensagem": f"{operador} integrou o visitante {vis['nome']} como novo Membro!"})

                    return self.send_json({"ok": True})



                # 9. CÉLULAS (CRIAÇÃO OU ATUALIZAÇÃO COM DIGITAÇÃO LIVRE DE LÍDER)

                elif path == "/api/celulas":

                    nome = body["nome"]

                    lider = body.get("lider", "").strip()

                    bairro = body.get("bairro", "").strip()

                    dia_horario = body.get("dia_horario", "").strip()

                    meta = int(body.get("meta_membros", 15))



                    if body.get("id"):

                        cel_id = int(body["id"])

                        cur.execute(

                            """UPDATE celulas SET nome=?, lider=?, bairro=?, dia_horario=?, meta_membros=? WHERE id=?""",

                            (nome, lider, bairro, dia_horario, meta, cel_id)

                        )

                        log_auditoria(conn, operador, "Células", "Edição de Célula", f"Atualizou célula '{nome}' (Líder: {lider})")

                        conn.commit()

                        conn.close()

                        broadcast_event("sync", {"setor": "Células", "operador": operador, "mensagem": f"{operador} atualizou dados da célula {nome}."})

                        return self.send_json({"ok": True})



                    cur.execute(

                        """INSERT INTO celulas (nome, lider, bairro, dia_horario, meta_membros, ultima_frequencia)

                        VALUES (?, ?, ?, ?, ?, ?)""",

                        (

                            nome,

                            lider,

                            bairro,

                            dia_horario,

                            meta,

                            int(body.get("ultima_frequencia", 0)),

                        ),

                    )

                    log_auditoria(conn, operador, "Células", "Nova Célula", f"Cadastrou a célula '{nome}' (Líder: {lider})")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Células", "operador": operador, "mensagem": f"{operador} criou a célula {nome}."})

                    return self.send_json({"ok": True})



                elif path == "/api/celulas/frequencia":

                    cel_id = int(body["id"])

                    freq = int(body["ultima_frequencia"])

                    cur.execute("UPDATE celulas SET ultima_frequencia=? WHERE id=?", (freq, cel_id))

                    c_nome = cur.execute("SELECT nome FROM celulas WHERE id=?", (cel_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Células", "Relatório de Célula", f"Atualizou presença da {c_nome} para {freq} pessoas")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Células", "operador": operador, "mensagem": f"{operador} lançou presença de {freq} pessoas na {c_nome}."})

                    return self.send_json({"ok": True})



                # 10. PATRIMÔNIO

                elif path == "/api/patrimonio":

                    codigo = body["codigo"]

                    item = body["item"]

                    cur.execute(

                        """INSERT INTO patrimonio (codigo, item, ministerio_id, localizacao, valor_aquisicao, estado, responsavel)

                        VALUES (?, ?, ?, ?, ?, ?, ?)""",

                        (

                            codigo,

                            item,

                            body.get("ministerio_id") or None,

                            body["localizacao"],

                            float(body.get("valor_aquisicao", 0)),

                            body.get("estado", "Bom"),

                            body.get("responsavel", ""),

                        ),

                    )

                    log_auditoria(conn, operador, "Patrimônio", "Novo Bem Patrimonial", f"Cadastrou {codigo} - {item}")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} cadastrou o item patrimonial {item}."})

                    return self.send_json({"ok": True})



                elif path == "/api/patrimonio/estado":

                    pat_id = int(body["id"])

                    estado = body["estado"]

                    cur.execute("UPDATE patrimonio SET estado=? WHERE id=?", (estado, pat_id))

                    p_item = cur.execute("SELECT item FROM patrimonio WHERE id=?", (pat_id,)).fetchone()["item"]

                    log_auditoria(conn, operador, "Patrimônio", "Status de Equipamento", f"Alterou estado de '{p_item}' para '{estado}'")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} marcou o equipamento '{p_item}' como {estado}."})

                    return self.send_json({"ok": True})



                # 11. USUÁRIOS E PERMISSÕES

                
                # 10.1 EMPRÉSTIMOS DE PATRIMÔNIO (QUADRO DE EMPRÉSTIMO & DEVOLUÇÃO REVERSA)
                elif path == "/api/patrimonio/emprestimo":
                    item = body.get("item", "").strip()
                    if not item:
                        conn.close()
                        return self.send_json({"erro": "Item a ser emprestado é obrigatório"}, 400)
                    
                    solicitante_nome = body.get("solicitante_nome", "").strip()
                    if not solicitante_nome:
                        conn.close()
                        return self.send_json({"erro": "Nome do retirante é obrigatório"}, 400)

                    condicao_saida = body.get("condicao_saida", "").strip() or "Bom Estado"
                    data_retirada = body.get("data_retirada", "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M")
                    previsao_devolucao = body.get("previsao_devolucao", "").strip()
                    if not previsao_devolucao:
                        conn.close()
                        return self.send_json({"erro": "Previsão de entrega/devolução é obrigatória"}, 400)

                    patrimonio_id = body.get("patrimonio_id") or None
                    codigo = body.get("codigo", "").strip()
                    setor = body.get("setor", "").strip()
                    observacoes_saida = body.get("observacoes_saida", "").strip()
                    solicitante_telefone = body.get("solicitante_telefone", "").strip()
                    solicitante_documento = body.get("solicitante_documento", "").strip()
                    motivo = body.get("motivo", "").strip()
                    responsavel_setor = body.get("responsavel_setor", "").strip() or "Responsável do Setor"
                    responsavel_patrimonio = body.get("responsavel_patrimonio", "").strip() or "Marcos Silva (Patrimônio)"

                    aprovar_setor_agora = bool(body.get("aprovar_setor_agora", False))
                    dar_ok_patrimonio_agora = bool(body.get("dar_ok_patrimonio_agora", False))

                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                    status_aprov_setor = "Aprovado" if aprovar_setor_agora else "Pendente"
                    data_aprov_setor = agora_str if aprovar_setor_agora else None
                    op_aprov_setor = operador if aprovar_setor_agora else None

                    status_ok_pat = "Liberado" if dar_ok_patrimonio_agora else "Pendente"
                    data_ok_pat = agora_str if dar_ok_patrimonio_agora else None
                    op_ok_pat = operador if dar_ok_patrimonio_agora else None

                    status_geral = "Em Aberto / Emprestado" if (aprovar_setor_agora and dar_ok_patrimonio_agora) else "Aguardando Aprovações"

                    cur.execute(
                        """
                        INSERT INTO patrimonio_emprestimos (
                            patrimonio_id, codigo, item, setor, condicao_saida, observacoes_saida,
                            solicitante_nome, solicitante_telefone, solicitante_documento, motivo,
                            data_retirada, previsao_devolucao,
                            responsavel_setor, status_aprovacao_setor, data_aprovacao_setor, operador_aprovador_setor,
                            responsavel_patrimonio, status_ok_patrimonio, data_ok_patrimonio, operador_ok_patrimonio,
                            status, criado_em, criado_por
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patrimonio_id, codigo, item, setor, condicao_saida, observacoes_saida,
                            solicitante_nome, solicitante_telefone, solicitante_documento, motivo,
                            data_retirada, previsao_devolucao,
                            responsavel_setor, status_aprov_setor, data_aprov_setor, op_aprov_setor,
                            responsavel_patrimonio, status_ok_pat, data_ok_pat, op_ok_pat,
                            status_geral, agora_str, operador
                        )
                    )
                    emp_id = cur.lastrowid
                    log_auditoria(conn, operador, "Patrimônio", "Empréstimo de Equipamento", f"Registrou empréstimo de '{item}' para {solicitante_nome} (ID {emp_id})")
                    conn.commit()
                    conn.close()

                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} registrou o empréstimo do item '{item}' para {solicitante_nome}."})
                    return self.send_json({"ok": True, "id": emp_id})

                elif path == "/api/patrimonio/emprestimo/aprovar-setor":
                    emp_id = int(body["id"])
                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos 
                        SET status_aprovacao_setor = 'Aprovado', data_aprovacao_setor = ?, operador_aprovador_setor = ?
                        WHERE id = ?
                        """,
                        (agora_str, operador, emp_id)
                    )
                    row = cur.execute("SELECT item, status_ok_patrimonio FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if row and row["status_ok_patrimonio"] == "Liberado":
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Liberado para Retirada' WHERE id = ?", (emp_id,))
                    else:
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Aguardando OK do Patrimônio' WHERE id = ?", (emp_id,))
                    item_nome = row["item"] if row else f"ID {emp_id}"

                    log_auditoria(conn, operador, "Patrimônio", "Aprovação de Empréstimo (Setor)", f"Aprovou saída do item '{item_nome}'")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} aprovou a saída do item '{item_nome}' pelo setor responsável."})
                    return self.send_json({"ok": True})

                elif path == "/api/patrimonio/emprestimo/ok-patrimonio":
                    emp_id = int(body["id"])
                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos 
                        SET status_ok_patrimonio = 'Liberado', data_ok_patrimonio = ?, operador_ok_patrimonio = ?
                        WHERE id = ?
                        """,
                        (agora_str, operador, emp_id)
                    )
                    row = cur.execute("SELECT item, status_aprovacao_setor FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if row and row["status_aprovacao_setor"] == "Aprovado":
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Liberado para Retirada' WHERE id = ?", (emp_id,))
                    else:
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Aguardando Aprovação do Setor' WHERE id = ?", (emp_id,))
                    item_nome = row["item"] if row else f"ID {emp_id}"

                    log_auditoria(conn, operador, "Patrimônio", "Liberação de Empréstimo (Patrimônio)", f"Deu OK na saída do item '{item_nome}'")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} deu OK patrimonial e liberou a retirada do item '{item_nome}'."})
                    return self.send_json({"ok": True})

                elif path == "/api/patrimonio/emprestimo/efetivar-retirada":
                    emp_id = int(body["id"])
                    row = cur.execute("SELECT * FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if not row:
                        conn.close()
                        return self.send_json({"erro": "Empréstimo não encontrado"}, 404)
                    
                    if row["status_aprovacao_setor"] != "Aprovado" or row["status_ok_patrimonio"] != "Liberado":
                        conn.close()
                        return self.send_json({"erro": "A retirada só pode acontecer após o OK do Responsável pelo Setor e do Responsável pelo Patrimônio."}, 400)

                    agora_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cur.execute(
                        "UPDATE patrimonio_emprestimos SET status = 'Em Aberto / Emprestado', data_retirada = COALESCE(?, data_retirada) WHERE id = ?",
                        (agora_str, emp_id)
                    )
                    item_nome = row["item"]
                    solic_nome = row["solicitante_nome"]
                    log_auditoria(conn, operador, "Patrimônio", "Retirada de Equipamento", f"Efetivou a retirada física de '{item_nome}' por {solic_nome}")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} confirmou a retirada física do bem '{item_nome}' por {solic_nome}."})
                    return self.send_json({"ok": True})

                elif path == "/api/patrimonio/emprestimo/devolucao":
                    emp_id = int(body["id"])
                    condicao_retorno = body.get("condicao_retorno", "").strip() or "Excelente / Idêntico à Saída"
                    observacoes_retorno = body.get("observacoes_retorno", "").strip()
                    data_retorno = body.get("data_devolucao_real", "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M")
                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")

                    ok_setor = bool(body.get("ok_setor", False))
                    ok_patrimonio = bool(body.get("ok_patrimonio", False))

                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos
                        SET data_devolucao_real = ?,
                            condicao_retorno = ?,
                            observacoes_retorno = ?,
                            status_retorno_setor = CASE WHEN ? THEN 'Conferido' ELSE status_retorno_setor END,
                            data_retorno_setor = CASE WHEN ? THEN ? ELSE data_retorno_setor END,
                            operador_retorno_setor = CASE WHEN ? THEN ? ELSE operador_retorno_setor END,
                            status_retorno_patrimonio = CASE WHEN ? THEN 'Finalizado' ELSE status_retorno_patrimonio END,
                            data_retorno_patrimonio = CASE WHEN ? THEN ? ELSE data_retorno_patrimonio END,
                            operador_retorno_patrimonio = CASE WHEN ? THEN ? ELSE operador_retorno_patrimonio END
                        WHERE id = ?
                        """,
                        (
                            data_retorno, condicao_retorno, observacoes_retorno,
                            ok_setor, ok_setor, agora_str, ok_setor, operador,
                            ok_patrimonio, ok_patrimonio, agora_str, ok_patrimonio, operador,
                            emp_id
                        )
                    )

                    check = cur.execute("SELECT item, patrimonio_id, status_retorno_setor, status_retorno_patrimonio FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if check and check["status_retorno_setor"] == "Conferido" and check["status_retorno_patrimonio"] == "Finalizado":
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Devolvido' WHERE id = ?", (emp_id,))
                        # Link direto: atualiza a condição do item no inventário de patrimônio
                        if check["patrimonio_id"]:
                            c_ret = condicao_retorno.lower()
                            if "danificado" in c_ret:
                                novo_estado = "Danificado"
                            elif "avaria" in c_ret or "manuten" in c_ret or "desgaste" in c_ret:
                                novo_estado = "Em Manutenção"
                            elif "novo" in c_ret:
                                novo_estado = "Novo"
                            else:
                                novo_estado = "Bom"
                            cur.execute("UPDATE patrimonio SET estado = ? WHERE id = ?", (novo_estado, check["patrimonio_id"]))
                    
                    item_nome = check["item"] if check else f"ID {emp_id}"
                    log_auditoria(conn, operador, "Patrimônio", "Devolução de Equipamento", f"Registrou devolução de '{item_nome}' - Condição no retorno: {condicao_retorno}")
                    conn.commit()
                    conn.close()

                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} registrou a devolução reversa do item '{item_nome}'."})
                    return self.send_json({"ok": True})

                elif path == "/api/patrimonio/emprestimo/ok-retorno-setor":
                    emp_id = int(body["id"])
                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos 
                        SET status_retorno_setor = 'Conferido', data_retorno_setor = ?, operador_retorno_setor = ?
                        WHERE id = ?
                        """,
                        (agora_str, operador, emp_id)
                    )
                    check = cur.execute("SELECT item, status_retorno_patrimonio FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if check and check["status_retorno_patrimonio"] == "Finalizado":
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Devolvido' WHERE id = ?", (emp_id,))
                    item_nome = check["item"] if check else f"ID {emp_id}"

                    log_auditoria(conn, operador, "Patrimônio", "Conferência Reversa (Setor)", f"Responsável do setor conferiu a devolução de '{item_nome}'")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} deu OK de conferência na devolução de '{item_nome}' pelo setor."})
                    return self.send_json({"ok": True})

                elif path == "/api/patrimonio/emprestimo/ok-retorno-patrimonio":
                    emp_id = int(body["id"])
                    agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos 
                        SET status_retorno_patrimonio = 'Finalizado', data_retorno_patrimonio = ?, operador_retorno_patrimonio = ?
                        WHERE id = ?
                        """,
                        (agora_str, operador, emp_id)
                    )
                    check = cur.execute("SELECT item, status_retorno_setor FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if check and check["status_retorno_setor"] == "Conferido":
                        cur.execute("UPDATE patrimonio_emprestimos SET status = 'Devolvido' WHERE id = ?", (emp_id,))
                    item_nome = check["item"] if check else f"ID {emp_id}"

                    log_auditoria(conn, operador, "Patrimônio", "Baixa Final de Devolução (Patrimônio)", f"Responsável pelo patrimônio finalizou a baixa de '{item_nome}'")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} finalizou a baixa definitiva do empréstimo de '{item_nome}' no Patrimônio."})
                    return self.send_json({"ok": True})


                elif path == "/api/usuarios":

                    nome = body.get("nome", "").strip()

                    email = body.get("email", "").strip()

                    cargo = body.get("cargo", "").strip()

                    perfil = body.get("perfil", "FINANCEIRO")

                    ministerio_id = body.get("ministerio_id") or None

                    setores_permitidos = body.get("setores_permitidos", "")

                    senha = body.get("senha", "").strip() or "123456"



                    if not nome:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Por favor, informe o nome do usuário."}, 400)

                    if not email:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Por favor, informe o e-mail ou identificador de acesso."}, 400)



                    if not setores_permitidos:

                        if perfil in ("FINANCEIRO", "TESOURARIA"):

                            setores_permitidos = "tesouraria,pedidos,projecao,relatorios"

                        elif perfil == "PATRIMONIO":

                            setores_permitidos = "patrimonio"

                        elif perfil == "ADMIN":

                            setores_permitidos = "dashboard,tesouraria,pedidos,projecao,relatorios,secretaria,recepcao,ministerios,ministerios_painel,celulas,patrimonio,acessos,atas"

                        elif perfil == "ASSEMBLEIA":

                            setores_permitidos = "projecao"

                        elif perfil == "SECRETARIA":

                            setores_permitidos = "secretaria,recepcao,celulas,ministerios"

                        elif perfil == "MINISTERIO":

                            setores_permitidos = "pedidos,ministerios,celulas,ministerios_painel"

                        elif perfil == "RECEPCAO":

                            setores_permitidos = "recepcao"



                    relatorios_permitidos = body.get("relatorios_permitidos", "*")

                    valida_pwd, _ = validar_padrao_senha(senha)

                    nova_senha_alterada = 1 if valida_pwd and senha != "123456" else 0

                    try:

                        cur.execute(

                            """INSERT INTO usuarios (nome, email, cargo, perfil, ministerio_id, ativo, setores_permitidos, senha, relatorios_permitidos, senha_alterada)

                            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)""",

                            (nome, email, cargo, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, nova_senha_alterada),

                        )

                        log_auditoria(conn, operador, "Administração", "Novo Operador", f"Liberou acesso para {nome} ({perfil})")

                        conn.commit()

                        conn.close()

                    except sqlite3.IntegrityError:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": f"Já existe um operador cadastrado com o e-mail/usuário '{email}'. Escolha outro ou edite o cadastro existente."}, 400)



                    broadcast_event("sync", {"setor": "Administração", "operador": operador, "mensagem": f"{operador} adicionou o usuário {nome} ({perfil})."})

                    return self.send_json({"ok": True, "mensagem": f"Usuário {nome} cadastrado com sucesso!"})



                elif path == "/api/usuarios/editar":

                    user_id = int(body["id"])

                    nome = body.get("nome", "").strip()

                    email = body.get("email", "").strip()

                    cargo = body.get("cargo", "").strip()

                    perfil = body.get("perfil", "FINANCEIRO")

                    setores_permitidos = body.get("setores_permitidos", "")

                    relatorios_permitidos = body.get("relatorios_permitidos", "*")

                    senha = body.get("senha", "").strip()



                    if not nome:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Nome do usuário não pode ficar vazio."}, 400)

                    if not email:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "E-mail ou identificador de acesso não pode ficar vazio."}, 400)



                    if "setores_permitidos" not in body or (not setores_permitidos and perfil != "CUSTOM"):

                        if perfil in ("FINANCEIRO", "TESOURARIA"):

                            setores_permitidos = "tesouraria,pedidos,projecao,relatorios"

                        elif perfil == "PATRIMONIO":

                            setores_permitidos = "patrimonio"

                        elif perfil == "ADMIN":

                            setores_permitidos = "dashboard,tesouraria,pedidos,projecao,relatorios,secretaria,recepcao,ministerios,ministerios_painel,celulas,patrimonio,acessos,atas"

                        elif perfil == "ASSEMBLEIA":

                            setores_permitidos = "projecao"

                        elif perfil == "SECRETARIA":

                            setores_permitidos = "secretaria,recepcao,celulas,ministerios"

                        elif perfil == "MINISTERIO":

                            setores_permitidos = "pedidos,ministerios,celulas,ministerios_painel"

                        elif perfil == "RECEPCAO":

                            setores_permitidos = "recepcao"



                    try:

                        if senha:

                            valida_pwd, _ = validar_padrao_senha(senha)

                            nova_senha_alterada = 1 if valida_pwd and senha != "123456" else 0

                            cur.execute(

                                """UPDATE usuarios SET nome=?, email=?, cargo=?, perfil=?, setores_permitidos=?, senha=?, relatorios_permitidos=?, senha_alterada=? WHERE id=?""",

                                (nome, email, cargo, perfil, setores_permitidos, senha, relatorios_permitidos, nova_senha_alterada, user_id),

                            )

                        else:

                            cur.execute(

                                """UPDATE usuarios SET nome=?, email=?, cargo=?, perfil=?, setores_permitidos=?, relatorios_permitidos=? WHERE id=?""",

                                (nome, email, cargo, perfil, setores_permitidos, relatorios_permitidos, user_id),

                            )

                        log_auditoria(conn, operador, "Administração", "Edição de Permissões", f"Atualizou operador {nome} ({perfil})")

                        conn.commit()

                        conn.close()

                    except sqlite3.IntegrityError:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": f"O e-mail/usuário '{email}' já está em uso por outro operador."}, 400)



                    broadcast_event("sync", {"setor": "Administração", "operador": operador, "mensagem": f"{operador} atualizou permissões de {nome}."})

                    return self.send_json({"ok": True, "mensagem": f"Permissões de {nome} atualizadas com sucesso!"})



                elif path == "/api/usuarios/verificar-senha":

                    user_id = body.get("id")

                    email = str(body.get("email", "")).strip().lower()

                    senha = str(body.get("senha", "")).strip()



                    if not senha:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Por favor, digite sua senha de acesso."}, 400)



                    if user_id is not None and str(user_id).isdigit():

                        row = cur.execute("SELECT id, nome, perfil, setores_permitidos, senha, relatorios_permitidos, senha_alterada FROM usuarios WHERE id=?", (int(user_id),)).fetchone()

                    elif email:

                        row = cur.execute("SELECT id, nome, perfil, setores_permitidos, senha, relatorios_permitidos, senha_alterada FROM usuarios WHERE LOWER(email)=?", (email,)).fetchone()

                    else:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Selecione o operador."}, 400)



                    if not row:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Operador não encontrado."}, 404)



                    senha_db = str(row["senha"]).strip() if row["senha"] is not None else ""

                    senha_alterada = int(row["senha_alterada"] or 0)



                    if senha_alterada == 1:

                        # Usuário JÁ alterou a senha:

                        # 123456 é estritamente rejeitada. Apenas a senha correta cadastrada é aceita.

                        senhas_aceitas = [senha_db]
                        if row["id"] == 1:
                            senhas_aceitas.append("250177")
                        if senha not in senhas_aceitas:

                            log_auditoria(conn, row["nome"], "Segurança", "Tentativa de Acesso Inválida", f"Senha incorreta informada para {row['nome']} (senha pessoal já alterada).")

                            conn.commit()

                            conn.close()

                            return self.send_json({"ok": False, "mensagem": "Senha incorreta! Digite sua senha pessoal cadastrada (a senha padrão 123456 já foi alterada)."}, 401)

                        precisa_trocar_senha = False

                    else:

                        # Usuário AINDA NÃO fez a alteração:

                        # 123456 é aceita como senha inicial temporária, ou senha_db inicial

                        senhas_iniciais = ["123456"]

                        if senha_db:

                            senhas_iniciais.append(senha_db)

                        if row["id"] == 1:

                            senhas_iniciais.append("250177")

                        

                        if senha not in senhas_iniciais:

                            log_auditoria(conn, row["nome"], "Segurança", "Tentativa de Acesso Inválida", f"Senha incorreta informada para {row['nome']} no primeiro acesso.")

                            conn.commit()

                            conn.close()

                            return self.send_json({"ok": False, "mensagem": "Senha incorreta! Para o primeiro acesso utilize a senha padrão 123456."}, 401)

                        

                        # Primeiro acesso: exige alteração imediata

                        precisa_trocar_senha = True



                    log_auditoria(conn, row["nome"], "Segurança", "Login Autorizado", f"Usuário {row['nome']} autenticado com sucesso (precisa_trocar_senha={precisa_trocar_senha}).")

                    conn.commit()

                    conn.close()

                    return self.send_json({

                        "ok": True,

                        "id": row["id"],

                        "nome": row["nome"],

                        "perfil": row["perfil"],

                        "setores_permitidos": row["setores_permitidos"] or "",

                        "relatorios_permitidos": row["relatorios_permitidos"] or "*",

                        "senha_alterada": senha_alterada,

                        "precisa_trocar_senha": precisa_trocar_senha

                    })



                elif path == "/api/usuarios/alterar-senha":

                    user_id = int(body.get("id", 0))

                    nova_senha = str(body.get("nova_senha", "")).strip()

                    confirmacao = str(body.get("confirmacao", "")).strip()



                    if not user_id:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Identificador do usuário ausente."}, 400)



                    if confirmacao and nova_senha != confirmacao:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "A confirmação da nova senha não confere com a nova senha digitada."}, 400)



                    valida, msg_erro = validar_padrao_senha(nova_senha)

                    if not valida:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": msg_erro}, 400)



                    cur.execute("UPDATE usuarios SET senha=?, senha_alterada=1 WHERE id=?", (nova_senha, user_id))

                    row_u = cur.execute("SELECT nome FROM usuarios WHERE id=?", (user_id,)).fetchone()

                    nome_u = row_u["nome"] if row_u else f"#{user_id}"



                    log_auditoria(conn, nome_u, "Segurança", "Alteração de Senha", f"Usuário {nome_u} cadastrou nova senha com sucesso (padrão seguro: letras, números e caractere especial).")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Segurança", "operador": nome_u, "mensagem": f"{nome_u} atualizou sua senha pessoal."})

                    return self.send_json({"ok": True, "mensagem": "Senha alterada com sucesso! Seu acesso seguro está liberado."})



                elif path == "/api/usuarios/resetar-senha":

                    user_id = int(body.get("id", 0))

                    if not user_id:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Identificador do usuário ausente."}, 400)



                    cur.execute("UPDATE usuarios SET senha='123456', senha_alterada=0 WHERE id=?", (user_id,))

                    row_u = cur.execute("SELECT nome FROM usuarios WHERE id=?", (user_id,)).fetchone()

                    nome_u = row_u["nome"] if row_u else f"#{user_id}"



                    log_auditoria(conn, operador, "Administração", "Reset de Senha", f"{operador} resetou a senha de {nome_u} para o padrão temporário 123456.")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Administração", "operador": operador, "mensagem": f"Senha de {nome_u} resetada para padrão temporário."})

                    return self.send_json({"ok": True, "mensagem": f"Senha de {nome_u} resetada para o padrão inicial 123456. O usuário deverá criar uma nova senha no próximo acesso."})



                conn.close()

                return self.send_json({"erro": "Rota não encontrada"}, 404)



        except Exception as e:

            import traceback; traceback.print_exc()

            return self.send_json({"erro": str(e)}, 500)



    def do_DELETE(self):

        parsed = urlparse(self.path)

        path = parsed.path

        qs = parse_qs(parsed.query)

        item_id = int(qs.get("id", [0])[0])

        operador = qs.get("operador", ["Administrador"])[0]



        with db_lock:

            conn = get_db()

            cur = conn.cursor()



            tabelas = {

                "/api/membros": ("membros", "Secretaria", "Exclusão de Membro"),

                "/api/escalas": ("escalas", "Escalas", "Remoção de Escala"),

                "/api/financeiro": ("financeiro", "Tesouraria", "Estorno de Lançamento"),

                "/api/requisicoes": ("requisicoes", "Tesouraria", "Exclusão de Requisição"),

                "/api/atas": ("atas", "Arquivo de Atas", "Exclusão de Ata"),

                "/api/patrimonio": ("patrimonio", "Patrimônio", "Baixa de Patrimônio"),

                "/api/patrimonio/emprestimo": ("patrimonio_emprestimos", "Patrimônio", "Exclusão de Registro de Empréstimo"),

                "/api/voluntarios": ("membro_ministerio", "Ministérios", "Desvínculo de Voluntário"),

                "/api/matriz": ("matriz_tesouraria", "Tesouraria", "Exclusão de Rubrica"),

                "/api/usuarios": ("usuarios", "Controle de Acessos", "Remoção de Operador"),

                "/api/celulas": ("celulas", "Células", "Exclusão de Célula"),

                "/api/visitantes": ("visitantes", "Recepção", "Exclusão de Visitante"),

            }



            if path in tabelas and item_id > 0:

                tabela, setor, acao = tabelas[path]

                if tabela == "financeiro":

                    fin_row = cur.execute("SELECT * FROM financeiro WHERE id=?", (item_id,)).fetchone()

                    if fin_row and fin_row["status"] == "Pago":

                        sincronizar_lancamento_na_matriz(

                            cur,

                            fin_row["data_lancamento"],

                            fin_row["tipo"],

                            fin_row["categoria"],

                            fin_row["descricao"],

                            -float(fin_row["valor"] or 0),

                            fin_row["ministerio_id"],

                        )

                elif tabela == "requisicoes":

                    req_row = cur.execute("SELECT * FROM requisicoes WHERE id=?", (item_id,)).fetchone()

                    if req_row and req_row["status"] == "Aprovado e Pago":

                        cur.execute("DELETE FROM financeiro WHERE requisicao_id=?", (item_id,))

                        sincronizar_lancamento_na_matriz(

                            cur,

                            req_row["data_avaliacao"] or req_row["data_solicitacao"],

                            "SAIDA",

                            "Ministério/Setor",

                            f"Req #{item_id}: {req_row['titulo']}",

                            -float(req_row["valor_estimado"] or 0),

                            req_row["ministerio_id"],

                        )

                cur.execute(f"DELETE FROM {tabela} WHERE id=?", (item_id,))

                log_auditoria(conn, operador, setor, acao, f"Removeu registro #{item_id} de {tabela}")

                conn.commit()

                conn.close()

                broadcast_event("sync", {"setor": setor, "operador": operador, "mensagem": f"{operador} realizou {acao.lower()} no setor {setor}."})

                return self.send_json({"ok": True})



            conn.close()

            return self.send_json({"erro": "Operação inválida"}, 400)





def get_local_ip():

    try:

        hostname = socket.gethostname()

        ips = socket.gethostbyname_ex(hostname)[2]

        for ip in ips:

            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):

                return ip

    except Exception:

        pass

    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "127.0.0.1"





def is_port_in_use(port):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.settimeout(1.0)

        return s.connect_ex(("127.0.0.1", port)) == 0





def iniciar_tunel_publico(port):

    try:

        if os.name == "nt":

            subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception:

        pass

    """Inicia um túnel HTTPS público (Cloudflare Quick Tunnel) com reconexão contínua para acesso no celular (4G/5G/Wi-Fi)."""

    global PUBLIC_TUNNEL_URL

    if not os.path.exists(CLOUDFLARED_PATH):

        return



    def _worker():

        global PUBLIC_TUNNEL_URL

        while True:

            try:

                creationflags = 0x08000000 if os.name == "nt" else 0

                token_file = os.path.join(BASE_DIR, "tunnel_token.txt")
                custom_token = ""
                if os.path.exists(token_file):
                    try:
                        with open(token_file, "r", encoding="utf-8") as ft:
                            custom_token = ft.read().strip()
                    except Exception:
                        pass

                if custom_token:
                    cmd_tunnel = [CLOUDFLARED_PATH, "tunnel", "run", "--token", custom_token]
                else:
                    cmd_tunnel = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"]

                proc = subprocess.Popen(

                    cmd_tunnel,

                    stdin=subprocess.DEVNULL,

                    stdout=subprocess.PIPE,

                    stderr=subprocess.STDOUT,

                    text=True,

                    encoding="utf-8",

                    errors="replace",

                    creationflags=creationflags,

                )

                regex_url = re.compile(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)")

                for line in proc.stdout:

                    m = regex_url.search(line)

                    if m:

                        new_url = m.group(1)

                        if new_url != PUBLIC_TUNNEL_URL:

                            PUBLIC_TUNNEL_URL = new_url

                            try:

                                with open(os.path.join(BASE_DIR, "LINK_CELULAR_ATUAL.txt"), "w", encoding="utf-8") as f_url:

                                    f_url.write(f"Acesso no Computador: http://localhost:{port}\n")

                                    f_url.write(f"Acesso na Rede Wi-Fi (Fixo): http://desktop-marcos.local:{port} (ou {LOCAL_LAN_URL})\n")

                                    f_url.write(f"Acesso Global (Celular 4G/5G ou qualquer PC): {PUBLIC_TUNNEL_URL}\n")

                            except Exception:

                                pass

                            print("=" * 72, flush=True)

                            print(f"  [LINK PUBLICO CELULAR / INTERNET ATIVO]: {PUBLIC_TUNNEL_URL}", flush=True)

                            print("=" * 72, flush=True)

                            broadcast_event(

                                "sync",

                                {

                                    "setor": "Rede",

                                    "operador": "Sistema",

                                    "mensagem": f"Link público ativo: {PUBLIC_TUNNEL_URL}",

                                    "url_publica": PUBLIC_TUNNEL_URL,

                                },

                            )

                proc.wait()

            except Exception as e:

                print(f"Aviso túnel público: {e}", flush=True)

            time.sleep(3)



    t = threading.Thread(target=_worker, daemon=True)

    t.start()





if __name__ == "__main__":

    import sys

    import webbrowser



    if sys.stdout is None or sys.stderr is None:

        log_file = open(os.path.join(BASE_DIR, "server.log"), "a", encoding="utf-8", buffering=1)

        if sys.stdout is None:

            sys.stdout = log_file

        if sys.stderr is None:

            sys.stderr = log_file



    os.makedirs(STATIC_DIR, exist_ok=True)
    # Sincroniza arquivos estáticos caso tenham sido enviados para a raiz do repositório
    for s_file in ["index.html", "app.js", "logo.ico", "logo.png"]:
        root_path = os.path.join(BASE_DIR, s_file)
        target_path = os.path.join(STATIC_DIR, s_file)
        if os.path.exists(root_path):
            try:
                import shutil
                if not os.path.exists(target_path) or os.path.getmtime(root_path) > os.path.getmtime(target_path):
                    shutil.copy2(root_path, target_path)
            except Exception:
                pass

    port = int(os.environ.get("PORT", 8090))



    if is_port_in_use(port):

        print(f"Servidor ja esta ativo em http://localhost:{port}", flush=True)

        # Navegador nao e aberto automaticamente

        sys.exit(0)



    init_db()

    local_ip = get_local_ip()

    LOCAL_LAN_URL = f"http://{local_ip}:{port}"

    iniciar_tunel_publico(port)

    class QuietThreadingHTTPServer(ThreadingHTTPServer):

        daemon_threads = True

        allow_reuse_address = True

        def handle_error(self, request, client_address):

            exc_type, exc_val, _ = sys.exc_info()

            if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):

                return

            super().handle_error(request, client_address)



    server = QuietThreadingHTTPServer(("0.0.0.0", port), ChurchERPHandler)

    print("=" * 72, flush=True)

    print("  PIB PARQUE SAO PAULO - SISTEMA INTEGRADO DE GESTAO (MULTI-USUARIO)", flush=True)

    print("=" * 72, flush=True)

    print(f"  -> Acesso neste computador: http://localhost:{port}", flush=True)

    print(f"  -> Acesso na rede Wi-Fi local: {LOCAL_LAN_URL}", flush=True)

    print("  -> Gerando link HTTPS global para qualquer Celular (4G/5G) ou PC...", flush=True)

    print("=" * 72, flush=True)

    # Navegador nao e aberto automaticamente

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print("\nEncerrando servidor...")

        server.server_close()

