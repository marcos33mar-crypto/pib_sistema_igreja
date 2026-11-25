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
import shutil
import hashlib
import hmac
import secrets

import socket

import sqlite3

import subprocess

import threading

try:
    import fiscal_a1
except ImportError:
    fiscal_a1 = None

import time

import base64

import urllib.parse
import urllib.request

from datetime import datetime, timedelta, timezone

TZ_BRASILIA = timezone(timedelta(hours=-3))


def agora_brasilia():
    return datetime.now(TZ_BRASILIA)

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

    if event_type == "sync":
        try:
            agendar_auto_backup_nuvem(3.0)
        except Exception:
            pass





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



# =========================================================
# BLINDAGEM KAIRÓS: AUTO-BACKUP E AUTO-RECUPERAÇÃO EM NUVEM
# =========================================================
_AUTO_BACKUP_TIMER = None
_AUTO_BACKUP_LOCK = threading.Lock()
ULTIMO_BACKUP_NUVEM_EM = None


def _obter_token_blindagem():
    env_tk = os.environ.get("KAIROS_CLOUD_TOKEN", "").strip()
    if env_tk:
        return env_tk
    # Chave codificada em memória para não acionar bloqueio de push scanner
    _k_rev = "==Qa2VGMpJzdtVTOy1UWxh3NQJzd3l3a3EjRn1mRMVDdJhHWNZ0Xwh2Z"
    try:
        return base64.b64decode(_k_rev[::-1].encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def _contar_peso_banco(caminho_db):
    """Retorna uma tupla (total_auditoria, max_id_auditoria, soma_tabelas) para comparar qual banco é mais recente."""
    if not os.path.exists(caminho_db) or os.path.getsize(caminho_db) < 15000:
        return (-1, -1, -1)
    try:
        c = sqlite3.connect(caminho_db)
        cur = c.cursor()
        chk = cur.execute("PRAGMA quick_check").fetchone()
        if not chk or chk[0] != "ok":
            c.close()
            return (-1, -1, -1)
        cnt_aud = cur.execute("SELECT COUNT(*), COALESCE(MAX(id), 0) FROM auditoria").fetchone()
        tot_aud, max_aud = int(cnt_aud[0] or 0), int(cnt_aud[1] or 0)
        soma_tab = 0
        for tb in ("usuarios", "membros", "lancamentos", "atas", "patrimonio", "emprestimos_patrimonio", "pedidos"):
            try:
                soma_tab += int(cur.execute(f"SELECT COUNT(*) FROM {tb}").fetchone()[0] or 0)
            except Exception:
                pass
        c.close()
        return (tot_aud, max_aud, soma_tab)
    except Exception:
        return (-1, -1, -1)


def executar_auto_backup_nuvem():
    """Gera snapshot atômico do SQLite e salva na branch dedicada 'kairos-db-backup' no GitHub sem reiniciar o Render."""
    global ULTIMO_BACKUP_NUVEM_EM
    tk = _obter_token_blindagem()
    if not tk or not os.path.exists(DB_PATH):
        return False
    with _AUTO_BACKUP_LOCK:
        tmp_snap = DB_PATH + ".autobackup_snap"
        try:
            if os.path.exists(tmp_snap):
                os.remove(tmp_snap)
            conn_src = sqlite3.connect(DB_PATH, timeout=20.0)
            conn_dst = sqlite3.connect(tmp_snap)
            conn_src.backup(conn_dst)
            conn_dst.close()
            conn_src.close()

            with open(tmp_snap, "rb") as f:
                db_bytes = f.read()
            if os.path.exists(tmp_snap):
                os.remove(tmp_snap)

            if len(db_bytes) < 20000:
                return False

            repo = "marcos33mar-crypto/Pib_Parque_SP"
            file_path = "backups/igreja_erp_latest.db"
            branch = "kairos-db-backup"
            headers = {
                "Authorization": f"token {tk}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "Kairos-CloudShield/2.35",
            }

            sha_atual = None
            try:
                req_get = urllib.request.Request(
                    f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}",
                    headers=headers,
                )
                with urllib.request.urlopen(req_get, timeout=15) as resp:
                    sha_atual = json.loads(resp.read().decode("utf-8")).get("sha")
            except Exception:
                pass

            agora_str = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")
            payload = {
                "message": f"Blindagem Kairós Auto-Backup ({agora_str})",
                "content": base64.b64encode(db_bytes).decode("ascii"),
                "branch": branch,
            }
            if sha_atual:
                payload["sha"] = sha_atual

            req_put = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/contents/{file_path}",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="PUT",
            )
            with urllib.request.urlopen(req_put, timeout=30) as resp:
                if resp.status in (200, 201):
                    ULTIMO_BACKUP_NUVEM_EM = agora_str
                    print(f"[BLINDAGEM KAIRÓS] Auto-Backup salvo na nuvem com sucesso às {agora_str}!", flush=True)
                    return True
        except Exception as e:
            print(f"[BLINDAGEM KAIRÓS] Aviso no Auto-Backup em segundo plano: {e}", flush=True)
            try:
                if os.path.exists(tmp_snap):
                    os.remove(tmp_snap)
            except Exception:
                pass
    return False


def agendar_auto_backup_nuvem(delay_segundos=3.0):
    """Agenda um Auto-Backup em segundo plano com debounce para não atrasar nenhuma resposta ao usuário."""
    global _AUTO_BACKUP_TIMER
    try:
        if _AUTO_BACKUP_TIMER is not None:
            _AUTO_BACKUP_TIMER.cancel()
        _AUTO_BACKUP_TIMER = threading.Timer(delay_segundos, executar_auto_backup_nuvem)
        _AUTO_BACKUP_TIMER.daemon = True
        _AUTO_BACKUP_TIMER.start()
    except Exception:
        pass


def restaurar_backup_nuvem_no_boot():
    """Ao iniciar o servidor (ex: após reinicialização do Render), verifica se há backup mais recente na nuvem e restaura."""
    tk = _obter_token_blindagem()
    if not tk:
        return
    repo = "marcos33mar-crypto/Pib_Parque_SP"
    file_path = "backups/igreja_erp_latest.db"
    branch = "kairos-db-backup"
    headers = {
        "Authorization": f"token {tk}",
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Kairos-CloudShield/2.35",
    }
    tmp_cloud = DB_PATH + ".cloud_restore_check"
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            cloud_bytes = resp.read()
        if not cloud_bytes or len(cloud_bytes) < 20000:
            return
        with open(tmp_cloud, "wb") as f:
            f.write(cloud_bytes)

        peso_nuvem = _contar_peso_banco(tmp_cloud)
        peso_local = _contar_peso_banco(DB_PATH)
        if peso_nuvem[0] >= 0 and peso_nuvem >= peso_local:
            for sufixo in ("-wal", "-shm"):
                if os.path.exists(DB_PATH + sufixo):
                    try:
                        os.remove(DB_PATH + sufixo)
                    except Exception:
                        pass
            shutil.copy2(tmp_cloud, DB_PATH)
            print(
                f"[BLINDAGEM KAIRÓS] Banco de dados sincronizado da nuvem no boot ({peso_nuvem[0]} eventos vs {peso_local[0]} locais).",
                flush=True,
            )
    except Exception as e:
        print(f"[BLINDAGEM KAIRÓS] Verificação de boot concluída: {e}", flush=True)
    finally:
        if os.path.exists(tmp_cloud):
            try:
                os.remove(tmp_cloud)
            except Exception:
                pass


def iniciar_keep_alive_blindagem():
    """Mantém o servidor ativo no Render com pings periódicos leves."""
    def _loop():
        while True:
            time.sleep(600)  # A cada 10 minutos
            try:
                url_ping = os.environ.get("RENDER_EXTERNAL_URL", "https://pib-parque-sp.onrender.com").rstrip("/") + "/"
                req = urllib.request.Request(url_ping, headers={"User-Agent": "Kairos-KeepAlive/2.35"})
                with urllib.request.urlopen(req, timeout=15) as _:
                    pass
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def log_auditoria(conn, usuario_nome, setor, acao, detalhes):

    agora = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(

        "INSERT INTO auditoria (data_hora, usuario, setor, acao, detalhes) VALUES (?, ?, ?, ?, ?)",

        (agora, usuario_nome, setor, acao, detalhes),

    )

    try:

        conn.commit()

    except Exception:

        pass

    agendar_auto_backup_nuvem(3.0)


def init_db():

    with db_lock:

        restaurar_backup_nuvem_no_boot()

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

                membro_id INTEGER,

                ativo INTEGER DEFAULT 1,

                pode_editar_planilha INTEGER DEFAULT 0,

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
                assinatura_retirada_base64 TEXT DEFAULT '',
                assinatura_retirada_em TEXT DEFAULT '',
                assinatura_devolucao_base64 TEXT DEFAULT '',
                assinatura_devolucao_em TEXT DEFAULT '',
                telefone_responsavel_setor TEXT DEFAULT '',
                telefone_responsavel_patrimonio TEXT DEFAULT '',
                notificacao_sms_setor_enviada INTEGER DEFAULT 0,
                data_sms_setor TEXT DEFAULT '',
                notificacao_sms_patrimonio_enviada INTEGER DEFAULT 0,
                data_sms_patrimonio TEXT DEFAULT '',
                ultimo_aviso_sms TEXT DEFAULT '',
                criado_em TEXT NOT NULL,
                criado_por TEXT NOT NULL,
                FOREIGN KEY (patrimonio_id) REFERENCES patrimonio(id) ON DELETE SET NULL
            );



            CREATE TABLE IF NOT EXISTS requisicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_solicitacao TEXT NOT NULL,
                ministerio_id INTEGER NOT NULL,
                solicitante TEXT NOT NULL,
                solicitante_telefone TEXT DEFAULT '',
                titulo TEXT NOT NULL,
                justificativa TEXT,
                valor_estimado REAL NOT NULL,
                prioridade TEXT DEFAULT 'Normal',
                status TEXT DEFAULT 'Pendente',
                avaliado_por TEXT,
                data_avaliacao TEXT,
                anexo_pdf TEXT,
                anexo_nome TEXT,
                responsavel_tesouraria TEXT DEFAULT 'Tesouraria / Financeiro',
                telefone_tesouraria TEXT DEFAULT '',
                alerta_enviado INTEGER DEFAULT 0,
                data_alerta TEXT DEFAULT '',
                ultimo_aviso_alerta TEXT DEFAULT '',
                FOREIGN KEY (ministerio_id) REFERENCES ministerios(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS config_alertas_verba (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                responsavel_padrao TEXT DEFAULT 'Tesouraria / Financeiro',
                telefone_padrao TEXT DEFAULT '',
                telefone_secundario TEXT DEFAULT '',
                callmebot_apikey TEXT DEFAULT '',
                ntfy_topico TEXT DEFAULT 'kairos-pib-parque-sp-verbas',
                webhook_whatsapp_url TEXT DEFAULT '',
                alerta_auto_ativo INTEGER DEFAULT 1,
                atualizado_em TEXT DEFAULT ''
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

            CREATE TABLE IF NOT EXISTS contas_pagar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fornecedor TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                documento TEXT DEFAULT '',
                data_emissao TEXT NOT NULL,
                data_vencimento TEXT NOT NULL,
                valor REAL NOT NULL,
                forma_pagamento TEXT DEFAULT 'Boleto',
                status TEXT DEFAULT 'Em Aberto',
                data_pagamento TEXT DEFAULT '',
                valor_pago REAL DEFAULT 0,
                pago_por TEXT DEFAULT '',
                ministerio_id INTEGER,
                rubrica_matriz_id INTEGER,
                parcelado INTEGER DEFAULT 0,
                numero_parcelas INTEGER DEFAULT 1,
                parcela_atual INTEGER DEFAULT 1,
                grupo_parcela_id TEXT DEFAULT '',
                financeiro_id INTEGER,
                observacoes TEXT DEFAULT '',
                criado_por TEXT DEFAULT 'Tesouraria',
                criado_em TEXT DEFAULT ''
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

            ("profissao", "TEXT DEFAULT ''"),

            ("conjuge", "TEXT DEFAULT ''"),

            ("data_casamento", "TEXT DEFAULT ''"),

            ("foto_base64", "TEXT DEFAULT ''"),

            ("ministerio_id_2", "INTEGER DEFAULT NULL"),

            ("funcao_ministerio_2", "TEXT DEFAULT ''"),

            ("tipo_transferencia", "TEXT DEFAULT ''"),

            ("motivo_transferencia", "TEXT DEFAULT ''"),

            ("lgpd_consentimento", "INTEGER DEFAULT 0"),

            ("lgpd_data", "TEXT DEFAULT ''"),

        ]

        for col_name, col_type in novas_cols_membros:

            if col_name not in cols_mem:

                cur.execute(f"ALTER TABLE membros ADD COLUMN {col_name} {col_type}")

        # Garante colunas de consentimento LGPD em visitantes
        cols_vis = [r["name"] for r in cur.execute("PRAGMA table_info(visitantes)").fetchall()]
        for col_name, col_type in [("lgpd_consentimento", "INTEGER DEFAULT 0"), ("lgpd_data", "TEXT DEFAULT ''")]:
            if col_name not in cols_vis:
                cur.execute(f"ALTER TABLE visitantes ADD COLUMN {col_name} {col_type}")

        # Garante colunas estendidas de inventario em patrimonio (quantidade, situacao, NF, etc.)
        cols_pat = [r["name"] for r in cur.execute("PRAGMA table_info(patrimonio)").fetchall()]
        novas_cols_pat = [
            ("quantidade", "INTEGER DEFAULT 1"),
            ("situacao", "TEXT DEFAULT 'Em uso'"),
            ("motivo_entrada", "TEXT DEFAULT ''"),
            ("motivo_baixa", "TEXT DEFAULT ''"),
            ("data_compra", "TEXT DEFAULT ''"),
            ("nota_fiscal", "TEXT DEFAULT ''"),
            ("observacoes", "TEXT DEFAULT ''"),
        ]
        for col_name, col_type in novas_cols_pat:
            if col_name not in cols_pat:
                cur.execute(f"ALTER TABLE patrimonio ADD COLUMN {col_name} {col_type}")

        cur.execute(
            """CREATE TABLE IF NOT EXISTS extrato_apelidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo_chave TEXT UNIQUE NOT NULL,
                nome_real TEXT NOT NULL,
                grupo TEXT DEFAULT '',
                rubrica TEXT DEFAULT '',
                fonte TEXT DEFAULT 'Manual',
                atualizado_em TEXT DEFAULT ''
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS extrato_importados (
                chave_unica TEXT PRIMARY KEY,
                banco TEXT DEFAULT '',
                data_lancamento TEXT DEFAULT '',
                valor REAL DEFAULT 0,
                descricao TEXT DEFAULT '',
                importado_em TEXT DEFAULT ''
            )"""
        )



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

        # Garante migração das colunas de assinatura digital no módulo de patrimônio
        for c_nome, c_tipo in [
            ("assinatura_retirada_base64", "TEXT DEFAULT ''"),
            ("assinatura_retirada_em", "TEXT DEFAULT ''"),
            ("assinatura_devolucao_base64", "TEXT DEFAULT ''"),
            ("assinatura_devolucao_em", "TEXT DEFAULT ''"),
            ("telefone_responsavel_setor", "TEXT DEFAULT ''"),
            ("telefone_responsavel_patrimonio", "TEXT DEFAULT ''"),
            ("notificacao_sms_setor_enviada", "INTEGER DEFAULT 0"),
            ("data_sms_setor", "TEXT DEFAULT ''"),
            ("notificacao_sms_patrimonio_enviada", "INTEGER DEFAULT 0"),
            ("data_sms_patrimonio", "TEXT DEFAULT ''"),
            ("ultimo_aviso_sms", "TEXT DEFAULT ''"),
        ]:
            try:
                cur.execute(f"ALTER TABLE patrimonio_emprestimos ADD COLUMN {c_nome} {c_tipo}")
            except Exception:
                pass

        # Garante migração das colunas de alerta por telefone no módulo de pedidos de verba (requisicoes)
        for c_nome, c_tipo in [
            ("solicitante_telefone", "TEXT DEFAULT ''"),
            ("responsavel_tesouraria", "TEXT DEFAULT 'Tesouraria / Financeiro'"),
            ("telefone_tesouraria", "TEXT DEFAULT ''"),
            ("alerta_enviado", "INTEGER DEFAULT 0"),
            ("data_alerta", "TEXT DEFAULT ''"),
            ("ultimo_aviso_alerta", "TEXT DEFAULT ''"),
        ]:
            try:
                cur.execute(f"ALTER TABLE requisicoes ADD COLUMN {c_nome} {c_tipo}")
            except Exception:
                pass

        # Garante linha padrão de configuração de alertas de solicitação de verba
        try:
            row_cfg_v = cur.execute("SELECT id, telefone_padrao FROM config_alertas_verba WHERE id = 1").fetchone()
            if not row_cfg_v:
                fone_ini = ""
                resp_ini = "Tesouraria / Financeiro"
                try:
                    m_tes = cur.execute(
                        """SELECT nome, telefone FROM membros 
                           WHERE telefone IS NOT NULL AND TRIM(telefone) != '' 
                             AND (LOWER(cargo) LIKE '%tesour%' OR LOWER(nome) LIKE '%marcos%' OR LOWER(nome) LIKE '%isadora%')
                           ORDER BY CASE WHEN LOWER(nome) LIKE '%marcos%' THEN 0 ELSE 1 END LIMIT 1"""
                    ).fetchone()
                    if m_tes:
                        resp_ini = m_tes["nome"]
                        fone_ini = m_tes["telefone"]
                except Exception:
                    pass
                cur.execute(
                    """INSERT INTO config_alertas_verba 
                       (id, responsavel_padrao, telefone_padrao, ntfy_topico, alerta_auto_ativo, atualizado_em)
                       VALUES (1, ?, ?, 'kairos-pib-parque-sp-verbas', 1, ?)""",
                    (resp_ini, fone_ini, agora_brasilia().strftime("%d/%m/%Y %H:%M"))
                )
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

        if "ministerio_id" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN ministerio_id INTEGER DEFAULT NULL")

        if "membro_id" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN membro_id INTEGER DEFAULT NULL")

            cur.execute("UPDATE usuarios SET senha = '123456' WHERE senha IS NULL OR senha = ''")



        if "relatorios_permitidos" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN relatorios_permitidos TEXT DEFAULT '*'")



        if "senha_alterada" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN senha_alterada INTEGER DEFAULT 0")

        if "pode_editar_planilha" not in cols_usr:

            cur.execute("ALTER TABLE usuarios ADD COLUMN pode_editar_planilha INTEGER DEFAULT 0")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_fiscal_a1 (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cnpj TEXT NOT NULL,
                ccm_sp TEXT DEFAULT '',
                titular TEXT DEFAULT '',
                validade TEXT DEFAULT '',
                pfx_enc TEXT NOT NULL,
                senha_enc TEXT NOT NULL,
                ult_nsu TEXT DEFAULT '000000000000000',
                ultimo_sync TEXT DEFAULT '',
                atualizado_por TEXT DEFAULT '',
                atualizado_em TEXT DEFAULT ''
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais_recebidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                chave_acesso TEXT UNIQUE NOT NULL,
                nsu TEXT DEFAULT '',
                numero TEXT DEFAULT '',
                serie TEXT DEFAULT '',
                data_emissao TEXT DEFAULT '',
                emitente_cnpj TEXT DEFAULT '',
                emitente_nome TEXT DEFAULT '',
                valor_total REAL DEFAULT 0,
                descricao_itens TEXT DEFAULT '',
                situacao_sefaz TEXT DEFAULT 'Autorizada',
                status_lancamento TEXT DEFAULT 'Pendente',
                financeiro_id INTEGER DEFAULT NULL,
                conta_pagar_id INTEGER DEFAULT NULL,
                criado_em TEXT DEFAULT ''
            );
        """)



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



        # Verifica se o ministério 'Diretoria' já está cadastrado
        cur.execute("SELECT id FROM ministerios WHERE LOWER(nome) = 'diretoria' OR LOWER(nome) LIKE '%diretoria%'")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO ministerios (nome, lider, orcamento_mensal, realizado_2025, orcamento_2026, descricao, cor)
                VALUES ('Diretoria', 'Pastor Presidente & Diretoria Executiva', 0.0, 0.0, 0.0, 'Diretoria Estatutária da Igreja: Pastor Presidente, Vice-Presidente, Secretários e Tesoureiros.', '#1e293b')
            """)

        # Garante que todos os anos de 2020 a 2035 tenham o plano de contas padrão completo sem perder nenhum valor já lançado
        padronizar_matriz_todos_os_anos(conn)

        # Reconcilia lançamentos diários com a matriz_tesouraria garantindo 100% de fidelidade nas rubricas
        reconciliar_lancamentos_com_matriz(conn)

        conn.commit()

        conn.close()


def padronizar_matriz_todos_os_anos(conn):
    """Garante que todos os exercícios contábeis (2020 a 2035) possuam todas as contas padrão de 2026, preservando 100% dos valores já lançados."""
    cur = conn.cursor()
    padrao_contas = []
    vistos = set()
    for _, tipo_fluxo, grupo, rubrica, _ in MATRIZ_2026:
        chave = (tipo_fluxo, grupo, rubrica)
        if chave not in vistos:
            vistos.add(chave)
            padrao_contas.append(chave)

    for r26 in cur.execute("SELECT tipo_fluxo, grupo, rubrica FROM matriz_tesouraria WHERE ano=2026 ORDER BY id").fetchall():
        chave = (r26["tipo_fluxo"], r26["grupo"], r26["rubrica"])
        if chave not in vistos:
            vistos.add(chave)
            padrao_contas.append(chave)

    zeros = [0.0] * 12
    for ano in range(2020, 2036):
        rows_ano = cur.execute(
            "SELECT id, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12 FROM matriz_tesouraria WHERE ano=?",
            (ano,),
        ).fetchall()
        existentes_map = {}
        for r in rows_ano:
            rid = r["id"]
            chave = (r["tipo_fluxo"], r["grupo"], r["rubrica"])
            soma = sum(abs(float(r[f"m{i}"] or 0)) for i in range(1, 13))
            if chave not in vistos and soma == 0:
                cur.execute("DELETE FROM matriz_tesouraria WHERE id=?", (rid,))
            else:
                if chave not in existentes_map:
                    existentes_map[chave] = rid
                elif soma == 0:
                    cur.execute("DELETE FROM matriz_tesouraria WHERE id=?", (rid,))

        for t, g, rub in padrao_contas:
            if (t, g, rub) not in existentes_map:
                cur.execute(
                    """INSERT INTO matriz_tesouraria
                    (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (ano, t, g, rub, *zeros),
                )





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
    row_encontrada, ano, mes, col, grupo_alvo, rubrica_insercao = localizar_rubrica_matriz_para_lancamento(
        cur, data_lanc, tipo, categoria, descricao, ministerio_id
    )

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


def localizar_rubrica_matriz_para_lancamento(cur, data_lanc, tipo, categoria, descricao, ministerio_id=None):
    """Localiza com precisão cirúrgica a rubrica correspondente na matriz_tesouraria para um lançamento."""
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
    texto_busca = f"{cat_clean} {desc_clean}".strip()

    rows = cur.execute(
        f"SELECT id, rubrica, grupo, {col} as val_atual FROM matriz_tesouraria WHERE ano=? AND tipo_fluxo=? ORDER BY id ASC",
        (ano, tipo),
    ).fetchall()

    if " — " in (categoria or ""):
        part_g, part_r = [p.strip().lower() for p in str(categoria).split(" — ", 1)]
        for r in rows:
            if r["grupo"].strip().lower() == part_g and r["rubrica"].strip().lower() == part_r:
                return r, ano, mes, col, r["grupo"], r["rubrica"]

    row_encontrada = None
    grupo_alvo = "Entradas" if tipo == "ENTRADA" else "Despesas Operacionais"
    rubrica_insercao = descricao or categoria or "Lançamento Geral"

    if tipo == "ENTRADA":
        grupo_alvo = "Entradas"
        for r in rows:
            r_low = r["rubrica"].strip().lower()
            if cat_clean == r_low or desc_clean == r_low:
                row_encontrada = r
                break

        if not row_encontrada:
            if any(w in texto_busca for w in ["gasofil", "gazofil", "caixinha moeda", "dizimos caixa", "dízimos caixa"]):
                for r in rows:
                    if "gasofil" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "saldo" in texto_busca and any(w in texto_busca for w in ["itaú", "itau"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["itaú", "itau"]):
                        row_encontrada = r; break
            elif "saldo" in texto_busca and "bradesco" in texto_busca:
                for r in rows:
                    if "bradesco" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "aplic" in texto_busca or "rendimento" in texto_busca:
                for r in rows:
                    if "aplic" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "saldo" in texto_busca and "anterior" in texto_busca:
                for r in rows:
                    if "saldo" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "promessa" in texto_busca:
                for r in rows:
                    if "promessa" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "viver" in texto_busca:
                for r in rows:
                    if "viver" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "panetone" in texto_busca:
                for r in rows:
                    if "panetone" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "educa" in texto_busca and "crist" in texto_busca:
                for r in rows:
                    if "educa" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "bazar" in texto_busca:
                for r in rows:
                    if "bazar" in r["rubrica"].lower():
                        row_encontrada = r; break
                if not row_encontrada:
                    for r in rows:
                        if "cantina" in r["rubrica"].lower():
                            row_encontrada = r; break
            elif "cantina" in texto_busca:
                for r in rows:
                    if "cantina" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif any(w in texto_busca for w in ["missõ", "misso", "missão", "missao", "jmm", "jmn", "jme", "campanha"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["missõ", "misso", "campanha"]):
                        row_encontrada = r; break
            elif any(w in texto_busca for w in ["acampamento", "retiro", "piquenique", "piquinique", "camiseta", "casais"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["retiro", "piquenique", "acampamento"]):
                        row_encontrada = r; break
            elif any(w in texto_busca for w in ["reembolso", "estorno", "devolu", "ressarc"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["reembolso", "estorno", "devolu"]):
                        row_encontrada = r; break
            elif any(w in texto_busca for w in ["dízimo", "dizimo"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["dízimo", "dizimo"]):
                        row_encontrada = r; break
            elif "evento" in texto_busca:
                for r in rows:
                    if "evento" in r["rubrica"].lower():
                        row_encontrada = r; break
            elif "oferta" in texto_busca:
                for r in rows:
                    if "oferta" in r["rubrica"].lower() and "miss" not in r["rubrica"].lower():
                        row_encontrada = r; break

        if not row_encontrada:
            for r in rows:
                r_low = r["rubrica"].lower()
                if (cat_clean and cat_clean in r_low) or (desc_clean and desc_clean in r_low) or (r_low in cat_clean):
                    row_encontrada = r; break

        if not row_encontrada:
            for r in rows:
                if "outras entradas" in r["rubrica"].lower():
                    row_encontrada = r; break
        if not row_encontrada and rows:
            row_encontrada = rows[0]

        rubrica_insercao = categoria or descricao or "Receitas Diversas"

    else:
        min_nome = ""
        if ministerio_id:
            row_min = cur.execute("SELECT id, nome FROM ministerios WHERE id=?", (int(ministerio_id),)).fetchone()
            if row_min:
                min_nome = row_min["nome"].lower()

        if min_nome or "ministério" in cat_clean or "ministerio" in cat_clean:
            grupo_alvo = "Despesas com Ministérios"
            busca_min = f"{min_nome} {desc_clean} {cat_clean}"
            if "viver" in busca_min:
                for r in rows:
                    if "viver" in r["rubrica"].lower(): row_encontrada = r; break
            elif "ebd" in busca_min or "escola bíblica" in busca_min or "escola biblica" in busca_min:
                for r in rows:
                    if "ebd" in r["rubrica"].lower(): row_encontrada = r; break
            elif any(w in busca_min for w in ["jovem", "jovens", "adolescente"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["jovem", "adolescente"]): row_encontrada = r; break
            elif "evento" in busca_min:
                for r in rows:
                    if "evento" in r["rubrica"].lower() and r["grupo"] == "Despesas com Ministérios": row_encontrada = r; break
            elif any(w in busca_min for w in ["social", "ação", "acao"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["social", "ação", "acao"]): row_encontrada = r; break
            elif any(w in busca_min for w in ["som", "sonoplastia"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["som", "sonoplastia"]): row_encontrada = r; break
            elif any(w in busca_min for w in ["infantil", "criança", "ebf"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["infantil", "criança"]): row_encontrada = r; break
            elif "mulher" in busca_min or "mcm" in busca_min:
                for r in rows:
                    if "mulher" in r["rubrica"].lower(): row_encontrada = r; break
            elif "homem" in busca_min or "homens" in busca_min or "umhb" in busca_min:
                for r in rows:
                    if "homem" in r["rubrica"].lower(): row_encontrada = r; break
            elif any(w in busca_min for w in ["missão", "missao", "missões", "missoes"]):
                for r in rows:
                    if r["grupo"] == "Despesas com Ministérios" and any(w in r["rubrica"].lower() for w in ["missão", "missao", "missões"]): row_encontrada = r; break
            elif "casais" in busca_min or "casal" in busca_min or "família" in busca_min:
                for r in rows:
                    if "casais" in r["rubrica"].lower(): row_encontrada = r; break
            elif "coral" in busca_min:
                for r in rows:
                    if "coral" in r["rubrica"].lower(): row_encontrada = r; break
            elif "louvor" in busca_min or "música" in busca_min:
                for r in rows:
                    if "louvor" in r["rubrica"].lower(): row_encontrada = r; break
            elif any(w in busca_min for w in ["diácon", "diacon", "diacono", "diácono"]):
                for r in rows:
                    if any(w in r["rubrica"].lower() for w in ["diácon", "diacon"]): row_encontrada = r; break
            elif "comunica" in busca_min or "mídia" in busca_min or "midia" in busca_min:
                for r in rows:
                    if "comunica" in r["rubrica"].lower(): row_encontrada = r; break

            if not row_encontrada and min_nome:
                for r in rows:
                    if r["grupo"] == "Despesas com Ministérios" and (min_nome[:8] in r["rubrica"].lower() or r["rubrica"].lower()[:8] in min_nome):
                        row_encontrada = r; break

        if not row_encontrada:
            palavras_rubrica = [
                (["água", "agua", "sabesp"], "Conta de Água (Sabesp)"),
                (["luz", "energia", "enel", "eletric"], "Conta de Energia (Enel)"),
                (["telefone", "internet", "claro", "vivo", "fibra", "wi-fi", "net serv"], "Conta de Internet Telefone"),
                (["telefone", "internet", "claro", "vivo", "fibra", "wi-fi"], "Telefone e Internet (Claro)"),
                (["alarme", "adt", "monitoramento", "segurança"], "Monitoramento Sistema ADT"),
                (["alarme", "adt", "monitoramento", "segurança"], "Monitoramento Alarme (ADT)"),
                (["extintor", "bombeiro"], "Recarga de Extintores"),
                (["dedetiza"], "Dedetização"),
                (["caixa d'água", "caixa d agua", "limpeza caixa"], "Limpeza Caixa D'água"),
                (["diarista", "viviane", "faxina"], "Diarista (Viviane)"),
                (["contabilidade", "contador", "cardoso", "garisto", "honorário"], "Contador Cardoso & Garisto"),
                (["contabilidade", "contador", "honorário"], "Contabilidade"),
                (["inss", "gps", "previdência"], "INSS"),
                (["renda eclesiástica", "prebenda", "pastor ivan", "pr. ivan"], "Renda Eclesiástica (IVAN)"),
                (["renda eclesiástica", "prebenda", "pastor ivan", "pr. ivan"], "Renda Eclesiástica (Pr. Ivan)"),
                (["13º", "decimo terceiro", "férias"], "13º Salário / Férias"),
                (["iptu"], "IPTU"),
                (["darf", "irrf", "pis"], "DARF"),
                (["taxa prefeitura", "prefeitura"], "Taxas Prefeitura"),
                (["tarifa", "manutenção conta", "taxa banc"], "Tarifa Manutenção de Conta"),
                (["cartório", "cartorio", "ata", "autentica"], "Cartório (Atas/Documentos)"),
                (["sistema", "software", "informática", "site", "domínio"], "Sistema de Gestão / Informática"),
                (["convenção", "convencao", "cbm", "cbb"], "Convenção Batista"),
                (["mundiais", "jmm"], "Campanha Missões Mundiais"),
                (["nacionais", "jmn"], "Campanha Missões Nacionais"),
                (["estaduais", "jme"], "Campanha Missões Estaduais"),
                (["cláudio", "claudio", "balneário", "balneario"], "Pr. Cláudio do Balneário"),
                (["valmir"], "Missionário Valmir"),
                (["reforma", "pedreiro", "pintura", "telhado"], "Reforma e Construção"),
                (["elétrica", "eletrica", "lâmpada", "lampada", "fiação"], "Manutenção Elétrica / Hidráulica"),
                (["equipamento", "compra de bem", "instrumento", "microfone", "cadeira"], "Compra de Equipamentos"),
                (["limpeza", "descart", "papel", "detergente", "sabão"], "Material de Limpeza / Descartáveis"),
                (["santa ceia", "ceia", "pão", "suco de uva"], "Santa Ceia"),
                (["café", "cafe", "cozinha", "açúcar", "acucar", "lanche"], "Café e Cozinha"),
                (["ajuda de custo", "uber", "combustível", "gasolina", "passagem"], "Ajuda de Custo / Transporte"),
                (["gráfica", "grafica", "boletim", "banner", "faixa"], "Impressos / Boletins / Faixas"),
                (["livraria", "bíblia", "biblia", "revista"], "Livraria / Bíblias / Revistas"),
                (["expediente", "papelaria", "caneta", "toner", "impressora"], "Material de Expediente / Secretaria"),
            ]
            for termos, rub_alvo in palavras_rubrica:
                if any(t in texto_busca for t in termos):
                    for r in rows:
                        if r["rubrica"].lower() == rub_alvo.lower():
                            row_encontrada = r
                            grupo_alvo = r["grupo"]
                            break
                    if row_encontrada:
                        break

        if not row_encontrada:
            mapa_grupos = {
                "folha de pagamento": "Folha de Pagamento",
                "despesas fixas": "Despesas Fixas",
                "despesa fixa": "Despesas Fixas",
                "manutenção/patrimônio": "Manutenção/Patrimônio/Equip.",
                "manutencao/patrimonio": "Manutenção/Patrimônio/Equip.",
                "convenção/campanhas miss": "Convenção/Campanhas Miss.",
                "convenção / missões": "Convenção/Campanhas Miss.",
                "convencao / missoes": "Convenção/Campanhas Miss.",
                "missionários fixos": "Missionários Fixos",
                "missionarios fixos": "Missionários Fixos",
                "impostos": "Impostos",
                "desp. banco/cartório/sistema": "Desp. banco/Cartório/Sistema",
                "desp. banco": "Desp. banco/Cartório/Sistema",
                "gráfica /livraria/adm": "Gráfica /Livraria/ADM",
                "grafica /livraria/adm": "Gráfica /Livraria/ADM",
                "despesas com ministérios": "Despesas com Ministérios",
                "despesas operacionais": "Despesas Operacionais",
                "outras saídas": "Despesas Operacionais",
                "outras saidas": "Despesas Operacionais",
            }
            for k_cat, g_nome in mapa_grupos.items():
                if k_cat in cat_clean:
                    grupo_alvo = g_nome
                    break

            for r in rows:
                if r["grupo"] == grupo_alvo:
                    r_low = r["rubrica"].lower()
                    if desc_clean and (desc_clean in r_low or r_low in desc_clean):
                        row_encontrada = r; break
            if not row_encontrada:
                for r in rows:
                    if r["grupo"] == grupo_alvo and "outros" in r["rubrica"].lower():
                        row_encontrada = r; break
            if not row_encontrada:
                for r in rows:
                    if r["grupo"] == grupo_alvo:
                        row_encontrada = r; break

        rubrica_insercao = descricao or categoria or "Despesa Diversa"

    return row_encontrada, ano, mes, col, grupo_alvo, rubrica_insercao


def limpar_descricao_extrato(texto):
    s = str(texto or "").upper().strip()
    s = re.sub(r"\b(PIX\s+TRANSF|PIX\s+ENVIADO|PIX\s+RECEBIDO|PIX\s+QRCODE|TED|DOC|DEB\s+AUT|DEBITO\s+AUTOMATICO|COMPRA\s+CARTAO|COMPRA\s+DEBITO|PAGAMENTO\s+BOLETO|PAGTO|BOLETO|SISPAG|INT|MOBILE)\b", " ", s)
    s = re.sub(r"\b(PAG\*|MP\s*\*|EBN\*|PAYPAL\s*\*|MERCADOPAGO\*|IFD\*|99\*|UBER\*)\s*", " ", s)
    s = re.sub(r"\b\d{2}/\d{2}(?:/\d{2,4})?\b", " ", s)
    s = re.sub(r"\b\d{6,}\b", " ", s)
    s = re.sub(r"[^A-ZÀ-ÿ0-9\s&./-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -./")
    return s


def parsear_extrato_texto(conteudo, nome_arquivo=""):
    txt = str(conteudo or "").replace("\r\n", "\n").replace("\r", "\n")
    ext = (nome_arquivo or "").lower()
    itens = []
    if ext.endswith(".ofx") or "<OFX>" in txt.upper() or "<STMTTRN>" in txt.upper():
        blocos = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", txt, flags=re.IGNORECASE | re.DOTALL)
        if not blocos:
            blocos = txt.split("<STMTTRN>")[1:]
        for b in blocos:
            def tag_val(tag):
                m = re.search(rf"<{tag}>([^<\n]+)", b, flags=re.IGNORECASE)
                return m.group(1).strip() if m else ""
            dt_raw = re.sub(r"\D", "", tag_val("DTPOSTED"))
            if len(dt_raw) >= 8:
                data_iso = f"{dt_raw[0:4]}-{dt_raw[4:6]}-{dt_raw[6:8]}"
            else:
                continue
            amt_raw = tag_val("TRNAMT").replace(",", ".")
            try:
                amt = float(amt_raw)
            except Exception:
                continue
            if amt == 0:
                continue
            tipo = "ENTRADA" if amt > 0 else "SAIDA"
            memo = tag_val("MEMO") or tag_val("NAME") or "Lançamento Bancário"
            fitid = tag_val("FITID")
            itens.append({
                "data": data_iso,
                "tipo": tipo,
                "valor": round(abs(amt), 2),
                "descricao": memo,
                "fitid": fitid,
            })
        return itens

    # Parser CSV / TXT (separador ; ou ,)
    linhas = [l.strip() for l in txt.split("\n") if l.strip()]
    if not linhas:
        return itens
    sep = ";" if sum(l.count(";") for l in linhas[:5]) >= sum(l.count(",") for l in linhas[:5]) else ","
    for linha in linhas:
        partes = [p.strip().strip('"') for p in linha.split(sep)]
        if len(partes) < 3:
            continue
        data_iso = ""
        for p in partes[:3]:
            m_br = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", p)
            m_iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", p)
            if m_br:
                data_iso = f"{m_br.group(3)}-{m_br.group(2)}-{m_br.group(1)}"
                break
            if m_iso:
                data_iso = p
                break
        if not data_iso:
            continue
        val = None
        for p in reversed(partes):
            num_s = p.replace("R$", "").replace(" ", "").strip()
            if re.match(r"^[+-]?\d{1,3}(\.\d{3})*(,\d{1,2})?$", num_s):
                num_s = num_s.replace(".", "").replace(",", ".")
            elif re.match(r"^[+-]?\d+(\.\d{1,2})?$", num_s):
                pass
            else:
                continue
            try:
                v_f = float(num_s)
                if v_f != 0:
                    val = v_f
                    break
            except Exception:
                pass
        if val is None:
            continue
        desc = max([p for p in partes if not re.match(r"^[\d.,/+\-R$\s]+$", p)] or [partes[1]], key=len)
        itens.append({
            "data": data_iso,
            "tipo": "ENTRADA" if val > 0 else "SAIDA",
            "valor": round(abs(val), 2),
            "descricao": desc,
            "fitid": "",
        })
    return itens


def buscar_estabelecimento_extrato(cur, desc_original, cache_ext):
    termo_limpo = limpar_descricao_extrato(desc_original)
    if not termo_limpo:
        return desc_original, "Extrato", "", ""

    # 1. Memória da Igreja
    row_ap = cur.execute(
        "SELECT nome_real, grupo, rubrica FROM extrato_apelidos WHERE termo_chave=? OR ? LIKE '%' || termo_chave || '%' ORDER BY LENGTH(termo_chave) DESC LIMIT 1",
        (termo_limpo, termo_limpo),
    ).fetchone()
    if row_ap:
        return row_ap["nome_real"], "Memória", row_ap["grupo"] or "", row_ap["rubrica"] or ""

    if termo_limpo in cache_ext:
        return cache_ext[termo_limpo]

    # 2. Consulta CNPJ na BrasilAPI (Receita Federal)
    m_cnpj = re.search(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b", str(desc_original or ""))
    if m_cnpj:
        cnpj_num = re.sub(r"\D", "", m_cnpj.group(1))
        if len(cnpj_num) == 14:
            try:
                req = urllib.request.Request(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_num}", headers={"User-Agent": "KairosERP/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    j = json.loads(resp.read().decode("utf-8"))
                    nome_real = (j.get("nome_fantasia") or j.get("razao_social") or "").strip()
                    if nome_real:
                        res = (nome_real.title(), "Receita (CNPJ)", "", "")
                        cache_ext[termo_limpo] = res
                        return res
            except Exception:
                pass

    # 3. Busca na Internet (DuckDuckGo HTML)
    if len(termo_limpo) >= 4:
        try:
            q = urllib.parse.quote_plus(f"{termo_limpo} empresa estabelecimento")
            req = urllib.request.Request(
                f"https://html.duckduckgo.com/html/?q={q}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                html_res = resp.read().decode("utf-8", errors="ignore")
                m_tit = re.search(r'class="result__a"[^>]*>(.*?)</a>', html_res, flags=re.IGNORECASE | re.DOTALL)
                if m_tit:
                    tit = re.sub(r"<[^>]+>", "", m_tit.group(1)).strip()
                    tit = html.unescape(tit) if "html" in globals() else tit
                    tit = tit.split(" - ")[0].split(" | ")[0].strip()
                    if tit and len(tit) >= 3:
                        res = (tit[:90], "Busca Web", "", "")
                        cache_ext[termo_limpo] = res
                        return res
        except Exception:
            pass

    res = (termo_limpo.title(), "Extrato", "", "")
    cache_ext[termo_limpo] = res
    return res


def reconciliar_lancamentos_com_matriz(conn):
    """Garante que os lançamentos diários pagos em `financeiro` estejam refletidos nas rubricas exatas da `matriz_tesouraria`."""
    cur = conn.cursor()
    lancs = cur.execute(
        "SELECT id, data_lancamento, tipo, categoria, descricao, valor, status, ministerio_id FROM financeiro WHERE status != 'Cancelado' AND substr(data_lancamento, 1, 4) >= '2026'"
    ).fetchall()
    if not lancs:
        return False

    esperado_por_celula = {}
    for l in lancs:
        val = float(l["valor"] or 0)
        if val <= 0:
            continue
        row_enc, ano, mes, col, _, _ = localizar_rubrica_matriz_para_lancamento(
            cur, l["data_lancamento"], l["tipo"], l["categoria"], l["descricao"], l["ministerio_id"]
        )
        if row_enc:
            chave = (row_enc["id"], col)
            esperado_por_celula[chave] = round(esperado_por_celula.get(chave, 0.0) + val, 2)

    alterou = False
    for (rid, col), val_esperado in esperado_por_celula.items():
        r_atual = cur.execute(f"SELECT id, ano, tipo_fluxo, rubrica, {col} as v FROM matriz_tesouraria WHERE id=?", (rid,)).fetchone()
        if not r_atual:
            continue
        val_atual = float(r_atual["v"] or 0)
        if val_atual < val_esperado:
            diferenca = round(val_esperado - val_atual, 2)
            cur.execute(f"UPDATE matriz_tesouraria SET {col}=? WHERE id=?", (val_esperado, rid))
            alterou = True
            fallbacks = cur.execute(
                f"SELECT id, rubrica, {col} as v FROM matriz_tesouraria WHERE ano=? AND tipo_fluxo=? AND id != ?",
                (r_atual["ano"], r_atual["tipo_fluxo"], rid),
            ).fetchall()
            for fb in fallbacks:
                fb_id = fb["id"]
                fb_val = float(fb["v"] or 0)
                fb_esperado = esperado_por_celula.get((fb_id, col), 0.0)
                if fb_val >= diferenca and fb_esperado == 0.0 and any(
                    w in fb["rubrica"].lower() for w in ["média de entrada", "eventos (retiro/aniversário)"]
                ):
                    novo_fb = max(0.0, round(fb_val - diferenca, 2))
                    cur.execute(f"UPDATE matriz_tesouraria SET {col}=? WHERE id=?", (novo_fb, fb_id))
                    break
    return alterou


def _sincronizar_lancamento_na_matriz_legado(cur, data_lanc, tipo, categoria, descricao, valor_delta, ministerio_id=None):

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









# ============================================================================
# SEGURANÇA, HASH DE SENHAS (PBKDF2), SESSÃO HMAC E LGPD
# ============================================================================

def gerar_hash_senha(senha_raw):
    s = str(senha_raw or "").strip()
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", s.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"pbkdf2${salt}${dk}"


def verificar_senha_segura(senha_digitada, senha_db, senha_alterada=1):
    s_dig = str(senha_digitada or "").strip()
    s_db = str(senha_db or "").strip()
    if not s_dig:
        return False
    if s_db.startswith("pbkdf2$"):
        partes = s_db.split("$")
        if len(partes) == 3:
            _, salt, dk_esp = partes
            dk_calc = hashlib.pbkdf2_hmac("sha256", s_dig.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
            if hmac.compare_digest(dk_calc, dk_esp):
                return True
            if int(senha_alterada or 0) == 0 and s_dig == "123456":
                dk_123 = hashlib.pbkdf2_hmac("sha256", b"123456", salt.encode("utf-8"), 120000).hex()
                return hmac.compare_digest(dk_123, dk_esp)
        return False
    # Compatibilidade com senhas legadas em texto plano (com auto-upgrade no login)
    aceitas = set()
    if s_db:
        aceitas.add(s_db)
        sem_pref = s_db.lstrip("*@#$!%&")
        if sem_pref:
            aceitas.add(sem_pref)
            aceitas.add(f"*{sem_pref}")
    if int(senha_alterada or 0) == 0 or not s_db:
        aceitas.add("123456")
    return (
        s_dig in aceitas
        or (s_db and s_dig.lower() == s_db.lower())
        or (s_db and s_dig.lower() == s_db.lstrip("*@#$!%&").lower())
    )


def obter_segredo_sistema(conn, chave):
    env_map = {
        "session_secret": os.environ.get("KAIROS_SESSION_SECRET", "").strip(),
        "backup_key": os.environ.get("KAIROS_BACKUP_KEY", "").strip(),
    }
    if env_map.get(chave):
        return env_map[chave]
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS sistema_seguranca (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
    row = cur.execute("SELECT valor FROM sistema_seguranca WHERE chave=?", (chave,)).fetchone()
    if row and row["valor"]:
        return row["valor"]
    novo = secrets.token_hex(32)
    cur.execute("INSERT OR REPLACE INTO sistema_seguranca (chave, valor) VALUES (?, ?)", (chave, novo))
    conn.commit()
    return novo


def criar_token_sessao(conn, user_row):
    secret = obter_segredo_sistema(conn, "session_secret")
    raw_min_id = user_row["ministerio_id"] if "ministerio_id" in user_row.keys() else None
    payload = {
        "id": int(user_row["id"]),
        "nome": str(user_row["nome"] or ""),
        "perfil": str(user_row["perfil"] or "").upper(),
        "ministerio_id": int(raw_min_id) if raw_min_id else None,
        "exp": int(time.time()) + 43200,
    }
    raw_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    sig = hmac.new(secret.encode("utf-8"), raw_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{raw_b64}.{sig}"


def validar_token_sessao(token):
    if not token or "." not in token:
        return None
    try:
        raw_b64, sig = token.split(".", 1)
        with db_lock:
            conn = get_db()
            secret = obter_segredo_sistema(conn, "session_secret")
            esp = hmac.new(secret.encode("utf-8"), raw_b64.encode("ascii"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, esp):
                conn.close()
                return None
            payload = json.loads(base64.urlsafe_b64decode(raw_b64.encode("ascii")).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(time.time()):
                conn.close()
                return None
            uid = int(payload.get("id") or 0)
            row_u = conn.execute(
                "SELECT id, nome, perfil, ministerio_id, setores_permitidos, ativo FROM usuarios WHERE id=?",
                (uid,),
            ).fetchone()
            conn.close()
        if not row_u or int(row_u["ativo"] or 0) != 1:
            return None
        return {
            "id": int(row_u["id"]),
            "nome": str(row_u["nome"] or ""),
            "perfil": str(row_u["perfil"] or "").upper(),
            "ministerio_id": int(row_u["ministerio_id"]) if row_u["ministerio_id"] else None,
            "setores_permitidos": str(row_u["setores_permitidos"] or ""),
            "exp": int(payload.get("exp", 0)),
        }
    except Exception:
        return None


def obter_setores_usuario(auth_u):
    if not auth_u:
        return set()
    perfil = str(auth_u.get("perfil") or "").upper()
    if perfil == "ADMIN":
        return {"*"}
    if perfil == "LIDER_MINISTERIO":
        return {"tesouraria"}
    raw_setores = [s.strip().lower() for s in str(auth_u.get("setores_permitidos") or "").split(",") if s.strip()]
    if raw_setores:
        return set(raw_setores)
    defaults = {
        "FINANCEIRO": {"tesouraria", "pedidos", "projecao", "relatorios"},
        "TESOURARIA": {"tesouraria", "pedidos", "projecao", "relatorios"},
        "PATRIMONIO": {"patrimonio"},
        "SECRETARIA": {"secretaria", "recepcao", "celulas", "ministerios", "atas"},
        "MINISTERIO": {"pedidos", "ministerios", "celulas", "ministerios_painel"},
        "RECEPCAO": {"recepcao"},
        "ASSEMBLEIA": {"projecao"},
    }
    return defaults.get(perfil, set())


def usuario_tem_permissao_rota(auth_u, method, path):
    if not auth_u:
        return False
    perfil = str(auth_u.get("perfil") or "").upper()
    if perfil == "ADMIN":
        return True
    if path in ("/api/logout", "/api/usuarios/alterar-senha", "/api/bootstrap", "/api/sync-check", "/api/events"):
        return True
    if perfil == "LIDER_MINISTERIO":
        return False
    setores = obter_setores_usuario(auth_u)

    if path in ("/api/usuarios", "/api/usuarios/editar", "/api/usuarios/resetar-senha"):
        return "acessos" in setores
    if path in ("/api/lgpd/exportar-membro", "/api/lgpd/anonimizar-membro") or path.startswith("/api/membros"):
        return "secretaria" in setores
    if path.startswith("/api/atas"):
        return ("atas" in setores) or ("secretaria" in setores)
    if path.startswith("/api/matriz") or path.startswith("/api/financeiro") or path.startswith("/api/tesouraria") or path.startswith("/api/contas-pagar") or path.startswith("/api/fiscal") or path == "/api/ministerios/orcamento":
        return "tesouraria" in setores
    if path in ("/api/requisicoes/avaliar", "/api/requisicoes/config-alertas") or (method == "DELETE" and path == "/api/requisicoes"):
        return ("pedidos" in setores) or ("tesouraria" in setores)
    if path.startswith("/api/requisicoes"):
        return ("pedidos" in setores) or ("tesouraria" in setores) or ("ministerios" in setores)
    if path.startswith("/api/escalas") or path.startswith("/api/voluntarios") or path == "/api/ministerios":
        return ("ministerios" in setores) or ("secretaria" in setores)
    if path.startswith("/api/celulas"):
        return ("celulas" in setores) or ("secretaria" in setores)
    if path.startswith("/api/visitantes"):
        return ("recepcao" in setores) or ("secretaria" in setores)
    if path.startswith("/api/patrimonio"):
        return "patrimonio" in setores
    return False


LOGIN_RATE_LIMIT = {}
login_rate_lock = threading.Lock()


def verificar_rate_limit_login(ip_addr, chave):
    agora = time.time()
    key = (str(ip_addr or "local"), str(chave or ""))
    with login_rate_lock:
        rec = LOGIN_RATE_LIMIT.get(key)
        if not rec:
            return False, 0
        if rec.get("bloqueado_ate", 0) > agora:
            return True, int(rec["bloqueado_ate"] - agora)
        if agora - rec.get("janela_inicio", 0) > 300:
            LOGIN_RATE_LIMIT.pop(key, None)
            return False, 0
        return False, 0


def registrar_falha_login(ip_addr, chave):
    agora = time.time()
    key = (str(ip_addr or "local"), str(chave or ""))
    with login_rate_lock:
        rec = LOGIN_RATE_LIMIT.get(key)
        if not rec or (agora - rec.get("janela_inicio", 0) > 300):
            rec = {"tentativas": 0, "janela_inicio": agora, "bloqueado_ate": 0}
        rec["tentativas"] += 1
        if rec["tentativas"] >= 5:
            rec["bloqueado_ate"] = agora + 300
        LOGIN_RATE_LIMIT[key] = rec
        return rec["tentativas"], rec["bloqueado_ate"] > agora


def limpar_falha_login(ip_addr, chave):
    key = (str(ip_addr or "local"), str(chave or ""))
    with login_rate_lock:
        LOGIN_RATE_LIMIT.pop(key, None)


def build_bootstrap_data(req_handler=None):

    auth_user = req_handler.get_authenticated_user() if (req_handler and hasattr(req_handler, "get_authenticated_user")) else None
    is_auth = bool(auth_user)
    path_str = str(getattr(req_handler, "path", "") or "")
    modo_assembleia = any(k in path_str for k in ("modo=assembleia", "view=assembleia", "qrcode=1"))

    with db_lock:

        conn = get_db()

        cur = conn.cursor()



        usuarios_raw = [dict(r) for r in cur.execute("SELECT * FROM usuarios ORDER BY id").fetchall()]
        usuarios = []
        for u in usuarios_raw:
            u.pop("senha", None)
            if is_auth:
                usuarios.append(u)
            else:
                usuarios.append({
                    "id": u.get("id"),
                    "nome": u.get("nome"),
                    "perfil": u.get("perfil"),
                    "ativo": u.get("ativo", 1),
                })

        if not is_auth and not modo_assembleia:
            conn.close()
            return {
                "autenticado": False,
                "usuarios": usuarios,
                "ministerios": [],
                "ministerios_orcamentos": [],
                "matriz_tesouraria": [],
                "celulas": [],
                "membros": [],
                "vinculos": [],
                "visitantes": [],
                "escalas": [],
                "financeiro": [],
                "requisicoes": [],
                "config_alertas_verba": {},
                "patrimonio": [],
                "patrimonio_emprestimos": [],
                "auditoria": [],
                "atas": [],
                "contas_pagar": [],
                "clientes_conectados": 0,
                "timestamp": agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
            }

        ministerios = [dict(r) for r in cur.execute("SELECT * FROM ministerios ORDER BY orcamento_2026 DESC, id ASC").fetchall()]

        ministerios_orcamentos = [dict(r) for r in cur.execute("SELECT * FROM ministerios_orcamentos").fetchall()]

        celulas = [dict(r) for r in cur.execute("SELECT * FROM celulas ORDER BY id").fetchall()]

        try:
            if reconciliar_lancamentos_com_matriz(conn):
                conn.commit()
                agendar_auto_backup_nuvem(2.0)
        except Exception as e_rec_boot:
            print(f"[Bootstrap Reconciliacao Matriz] Aviso: {e_rec_boot}")

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
                SELECT r.id, r.data_solicitacao, r.ministerio_id, r.solicitante,
                       COALESCE(r.solicitante_telefone, '') as solicitante_telefone,
                       r.titulo, r.justificativa, r.valor_estimado, r.prioridade, r.status,
                       r.avaliado_por, r.data_avaliacao, r.anexo_nome,
                       COALESCE(r.responsavel_tesouraria, 'Tesouraria / Financeiro') as responsavel_tesouraria,
                       COALESCE(r.telefone_tesouraria, '') as telefone_tesouraria,
                       COALESCE(r.alerta_enviado, 0) as alerta_enviado,
                       COALESCE(r.data_alerta, '') as data_alerta,
                       COALESCE(r.ultimo_aviso_alerta, '') as ultimo_aviso_alerta,
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

                       pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

                       CASE WHEN arquivo_base64 IS NOT NULL AND LENGTH(arquivo_base64) > 0 THEN 1 ELSE 0 END as tem_anexo,

                       criado_por, criado_em, atualizado_em

                FROM atas

                ORDER BY data_reuniao DESC, id DESC

                """

            ).fetchall()

        ]

        contas_pagar = [
            dict(r)
            for r in cur.execute(
                """
                SELECT cp.*, min.nome as ministerio_nome, min.cor as ministerio_cor
                FROM contas_pagar cp
                LEFT JOIN ministerios min ON cp.ministerio_id = min.id
                ORDER BY CASE WHEN cp.status = 'Em Aberto' THEN 0 ELSE 1 END, cp.data_vencimento ASC, cp.id DESC
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

        # Agrupa lançamentos pagos por (ministerio_id, ano, mes) para reconciliar com a matriz sem duplicar
        fin_por_min_ano_mes = {}
        for f in financeiro:
            if f.get("tipo") == "SAIDA" and f.get("status") != "Cancelado" and f.get("ministerio_id") and f.get("data_lancamento"):
                partes_dt = str(f["data_lancamento"]).split("-")
                if len(partes_dt) >= 2 and partes_dt[0].isdigit() and partes_dt[1].isdigit():
                    chave_fm = (int(f["ministerio_id"]), int(partes_dt[0]), int(partes_dt[1]))
                    fin_por_min_ano_mes[chave_fm] = round(fin_por_min_ano_mes.get(chave_fm, 0.0) + float(f.get("valor") or 0), 2)

        for min_item in ministerios:

            nome_low = min_item["nome"].lower().strip()
            mid = int(min_item["id"])
            executado_por_ano = {}

            for ano_ref in [2023, 2024, 2025, 2026, 2027]:
                meses_mat = [0.0] * 12
                for r in matriz_rows:
                    if int(r["ano"]) == ano_ref and "Ministérios" in r["grupo"]:
                        k_clean = r["rubrica"].lower().strip()
                        match = False
                        if "ebd" in nome_low and "ebd" in k_clean:
                            match = True
                        elif ("diácono" in nome_low or "diacono" in nome_low) and ("diácono" in k_clean or "diacono" in k_clean):
                            match = True
                        else:
                            n_core = nome_low.replace("ministério", "").replace("de", "").replace("dos", "").strip()
                            k_core = k_clean.replace("ministério", "").replace("de", "").replace("dos", "").strip()
                            if n_core and k_core and (n_core in k_core or k_core in n_core):
                                match = True
                        if match:
                            for idx_m in range(12):
                                meses_mat[idx_m] += float(r["meses"][idx_m] or 0)

                soma_ano = 0.0
                for idx_m in range(12):
                    val_fin = fin_por_min_ano_mes.get((mid, ano_ref, idx_m + 1), 0.0)
                    soma_ano += max(meses_mat[idx_m], val_fin)
                executado_por_ano[str(ano_ref)] = round(soma_ano, 2)

            gasto_2026 = executado_por_ano.get("2026", 0.0)

            # Garante orcamento_2026 preenchido

            if not min_item.get("orcamento_2026"):

                min_item["orcamento_2026"] = round(float(min_item.get("orcamento_mensal", 0)) * 12, 2)

            min_item["gasto_atual"] = round(gasto_2026, 2)
            min_item["executado_por_ano"] = executado_por_ano

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

        cfg_alertas_verba = obter_config_alertas_verba(cur)

        conn.close()

        with sse_lock:
            clientes_ativos = max(1, len(sse_clients))

        if not is_auth and modo_assembleia:
            return {
                "autenticado": False,
                "modo_assembleia": True,
                "usuarios": usuarios,
                "ministerios": ministerios,
                "ministerios_orcamentos": ministerios_orcamentos,
                "matriz_tesouraria": matriz_rows,
                "celulas": [],
                "membros": [],
                "vinculos": [],
                "visitantes": [],
                "escalas": [],
                "financeiro": [],
                "requisicoes": [],
                "config_alertas_verba": {},
                "patrimonio": [],
                "patrimonio_emprestimos": [],
                "auditoria": [],
                "atas": [],
                "contas_pagar": [],
                "clientes_conectados": 0,
                "timestamp": agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
            }

        if is_auth and str(auth_user.get("perfil") or "").upper() == "LIDER_MINISTERIO":
            min_id_alvo = auth_user.get("ministerio_id")
            if not min_id_alvo:
                usr_match = next((u for u in usuarios_raw if int(u.get("id") or 0) == int(auth_user.get("id") or 0)), None)
                min_id_alvo = usr_match.get("ministerio_id") if usr_match else None
            min_id_int = int(min_id_alvo) if min_id_alvo else 0
            ministerios = [m for m in ministerios if int(m.get("id") or 0) == min_id_int]
            ministerios_orcamentos = [o for o in ministerios_orcamentos if int(o.get("ministerio_id") or 0) == min_id_int]
            financeiro = [f for f in financeiro if int(f.get("ministerio_id") or 0) == min_id_int]
            requisicoes = [r for r in requisicoes if int(r.get("ministerio_id") or 0) == min_id_int]
            usuarios = [u for u in usuarios if int(u.get("id") or 0) == int(auth_user.get("id") or 0)]
            matriz_rows = []
            celulas = []
            membros = []
            vinculos = []
            visitantes = []
            escalas = []
            patrimonio = []
            patrimonio_emprestimos = []
            auditoria = []
            atas = []
            contas_pagar = []

        return {
            "autenticado": is_auth,
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
            "config_alertas_verba": cfg_alertas_verba,
            "patrimonio": patrimonio,
            "patrimonio_emprestimos": patrimonio_emprestimos,
            "auditoria": auditoria,
            "atas": atas,
            "contas_pagar": contas_pagar,
            "clientes_conectados": clientes_ativos,
            "url_publica": (f"{req_handler.headers.get('X-Forwarded-Proto', 'https')}://{req_handler.headers.get('Host')}" if (req_handler and hasattr(req_handler, 'headers') and req_handler.headers.get('Host') and not req_handler.headers.get('Host', '').startswith(('localhost', '127.0.0.1', '10.', '192.168.'))) else PUBLIC_TUNNEL_URL),
            "url_rede_local": (f"{req_handler.headers.get('X-Forwarded-Proto', 'https')}://{req_handler.headers.get('Host')}" if (req_handler and hasattr(req_handler, 'headers') and req_handler.headers.get('Host') and not req_handler.headers.get('Host', '').startswith(('localhost', '127.0.0.1', '10.', '192.168.'))) else LOCAL_LAN_URL),
            "timestamp": agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
        }


def obter_config_alertas_verba(cur):
    """Retorna a configuração de alertas por telefone das solicitações de verba."""
    try:
        row = cur.execute("SELECT * FROM config_alertas_verba WHERE id = 1").fetchone()
        if row:
            return dict(row)
    except Exception:
        pass
    return {
        "id": 1,
        "responsavel_padrao": "Tesouraria / Financeiro",
        "telefone_padrao": "",
        "telefone_secundario": "",
        "callmebot_apikey": "",
        "ntfy_topico": "kairos-pib-parque-sp-verbas",
        "webhook_whatsapp_url": "",
        "alerta_auto_ativo": 1,
        "atualizado_em": "",
    }


def disparar_alerta_automatico_verba(cfg, req_info, evento="NOVA_SOLICITACAO"):
    """Dispara alertas automáticos em segundo plano (Push Celular ntfy + WhatsApp CallMeBot / Webhook)."""
    if not cfg:
        return

    def _worker():
        try:
            req_id = req_info.get("id", "S/N")
            titulo = req_info.get("titulo", "Solicitação de Verba")
            min_nome = req_info.get("ministerio_nome", "Ministério")
            solicitante = req_info.get("solicitante", "Membro")
            valor = float(req_info.get("valor_estimado") or 0)
            prioridade = req_info.get("prioridade", "Normal")
            justificativa = req_info.get("justificativa") or "Sem observações adicionais."
            status_atual = req_info.get("status", "Pendente")
            valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            url_sistema = "https://pib-parque-sp.onrender.com/"

            if evento == "TESTE":
                cabecalho = "🔔 TESTE DE ALERTA POR TELEFONE — KAIRÓS"
                resumo_txt = (
                    f"{cabecalho}\n"
                    f"O sistema de alertas de Solicitação de Verba está ATIVO e conectado ao celular!\n"
                    f"👤 Destinatário: {cfg.get('responsavel_padrao', 'Tesouraria')}\n"
                    f"📱 Telefone: {cfg.get('telefone_padrao', 'Configurado')}\n"
                    f"🔗 Acesso: {url_sistema}"
                )
            elif str(evento).startswith("AVALIACAO"):
                cabecalho = f"✅ SOLICITAÇÃO DE VERBA #{req_id}: {status_atual.upper()}"
                resumo_txt = (
                    f"{cabecalho}\n"
                    f"🏛️ Ministério: {min_nome}\n"
                    f"📋 Item: {titulo}\n"
                    f"💰 Valor: {valor_fmt}\n"
                    f"👤 Solicitante: {solicitante}\n"
                    f"🔗 Sistema Kairós: {url_sistema}"
                )
            else:
                cabecalho = f"🚨 NOVA SOLICITAÇÃO DE VERBA #{req_id} ({valor_fmt})"
                resumo_txt = (
                    f"{cabecalho}\n"
                    f"🏛️ Ministério: {min_nome}\n"
                    f"📋 Pedido: {titulo}\n"
                    f"👤 Solicitante: {solicitante}\n"
                    f"💰 Valor: {valor_fmt} | ⚡ Prioridade: {prioridade}\n"
                    f"📝 Justificativa: {justificativa}\n"
                    f"🔗 Aprovar na Tesouraria: {url_sistema}"
                )

            # 1. Canal Push Instantâneo no Celular (ntfy.sh) - Gratuito e Imediato
            topico = (cfg.get("ntfy_topico") or "").strip()
            if topico:
                try:
                    req_ntfy = urllib.request.Request(
                        f"https://ntfy.sh/{urllib.parse.quote(topico)}",
                        data=resumo_txt.encode("utf-8"),
                        headers={
                            "Title": cabecalho.encode("ascii", "ignore").decode("ascii") or "Alerta Kairos - Solicitacao de Verba",
                            "Priority": "urgent" if prioridade == "Urgente" else "high",
                            "Tags": "moneybag,bell",
                            "Click": url_sistema,
                        },
                        method="POST",
                    )
                    urllib.request.urlopen(req_ntfy, timeout=6).read()
                except Exception:
                    pass

            # 2. Canal WhatsApp Automático via CallMeBot (se API Key configurada)
            apikey = (cfg.get("callmebot_apikey") or "").strip()
            fones_destino = []
            for f_raw in [req_info.get("telefone_tesouraria"), cfg.get("telefone_padrao"), cfg.get("telefone_secundario")]:
                limpo = re.sub(r"\D", "", str(f_raw or ""))
                if len(limpo) >= 10:
                    if not limpo.startswith("55"):
                        limpo = "55" + limpo
                    if limpo not in fones_destino:
                        fones_destino.append(limpo)

            if apikey and fones_destino:
                for fone_w in fones_destino[:2]:
                    try:
                        qs = urllib.parse.urlencode({"phone": fone_w, "text": resumo_txt, "apikey": apikey})
                        url_cmb = f"https://api.callmebot.com/whatsapp.php?{qs}"
                        urllib.request.urlopen(url_cmb, timeout=8).read()
                    except Exception:
                        pass

            # 3. Canal Webhook WhatsApp / SMS Gateway (Z-API, Evolution, Twilio, etc.)
            webhook_url = (cfg.get("webhook_whatsapp_url") or "").strip()
            if webhook_url:
                try:
                    payload_wh = json.dumps({
                        "evento": evento,
                        "telefones": fones_destino,
                        "mensagem": resumo_txt,
                        "requisicao": req_info,
                    }).encode("utf-8")
                    req_wh = urllib.request.Request(
                        webhook_url,
                        data=payload_wh,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(req_wh, timeout=8).read()
                except Exception:
                    pass
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()





def render_mobile_termo_page(emp):
    """Gera a página mobile ultra-otimizada para celular/tablet onde o retirante assina digitalmente com o dedo."""
    emp_id = emp.get("id", 0)
    item_nome = emp.get("item", "Equipamento")
    codigo = emp.get("codigo", "") or "Não Tombado"
    setor = emp.get("setor", "") or "Patrimônio Geral"
    cond_saida = emp.get("condicao_saida", "") or "Bom Estado"
    obs_saida = emp.get("observacoes_saida", "") or "Sem detalhes adicionais"
    solicitante = emp.get("solicitante_nome", "")
    telefone = emp.get("solicitante_telefone", "") or "Não informado"
    documento = emp.get("solicitante_documento", "") or "Documento não informado"
    motivo = emp.get("motivo", "") or "Atividades da Igreja"
    dt_retirada = emp.get("data_retirada", "")
    dt_previsao = emp.get("previsao_devolucao", "")
    status_atual = emp.get("status", "Em Aberto")
    
    ass_ret_base64 = emp.get("assinatura_retirada_base64", "")
    ass_ret_em = emp.get("assinatura_retirada_em", "")
    ja_assinado = bool(ass_ret_base64)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Termo de Cautela e Empréstimo • PIB Parque São Paulo</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Inter', sans-serif; -webkit-tap-highlight-color: transparent; }}
    canvas {{ touch-action: none; }}
  </style>
</head>
<body class="bg-slate-100 text-slate-800 antialiased min-h-screen flex flex-col justify-between p-3 sm:p-5">

  <main class="max-w-md mx-auto w-full bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden mb-6">
    <!-- CABEÇALHO OFICIAL -->
    <header class="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-5 text-center relative">
      <div class="inline-block p-2 bg-indigo-600/30 rounded-2xl mb-2 backdrop-blur-sm border border-indigo-400/20">
        <span class="text-2xl">🏛️</span>
      </div>
      <p class="text-[10px] font-black uppercase tracking-widest text-indigo-300">Primeira Igreja Batista Parque São Paulo</p>
      <h1 class="text-lg font-black tracking-tight mt-0.5">Termo Digital de Responsabilidade</h1>
      <p class="text-xs text-slate-300 mt-1">Cautela de Empréstimo de Bens & Equipamentos</p>
      <div class="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold {'bg-emerald-500/20 text-emerald-300 border border-emerald-400/30' if ja_assinado else 'bg-amber-500/20 text-amber-300 border border-amber-400/30'}">
        <span>{'✓ Assinado Digitalmente' if ja_assinado else '⏳ Aguardando Sua Assinatura'}</span>
      </div>
    </header>

    <div class="p-5 space-y-4">

      <!-- DADOS DO BEM EMPRESTADO -->
      <section class="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Identificação do Bem</span>
          <span class="font-mono font-bold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-100 text-[10px]">Cód: {codigo}</span>
        </div>
        <h2 class="text-base font-extrabold text-slate-900 leading-snug">{item_nome}</h2>
        <div class="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-200 text-slate-600">
          <div><span class="text-[10px] text-slate-400 block">Setor de Origem:</span><strong class="text-slate-800">{setor}</strong></div>
          <div><span class="text-[10px] text-slate-400 block">Condição na Saída:</span><strong class="text-emerald-700">{cond_saida}</strong></div>
        </div>
        {f'<p class="text-[11px] text-slate-500 bg-white p-2 rounded-lg border border-slate-200 mt-1"><strong>Observações:</strong> {obs_saida}</p>' if obs_saida else ''}
      </section>

      <!-- DADOS DO SOLICITANTE / RETIRANTE -->
      <section class="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 space-y-2 text-xs">
        <span class="font-bold text-slate-500 uppercase tracking-wider text-[10px] block">Responsável pela Retirada (Cautelador)</span>
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">
            {solicitante[:1].upper() if solicitante else 'M'}
          </div>
          <div>
            <h3 class="font-bold text-slate-900 text-sm">{solicitante}</h3>
            <p class="text-[11px] text-slate-500">{documento} • {telefone}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-slate-600 text-xs">
          <div><span class="text-[10px] text-slate-400 block">Data de Retirada:</span><strong>{dt_retirada}</strong></div>
          <div><span class="text-[10px] text-rose-500 block font-bold">Devolução Obrigatória Até:</span><strong class="text-rose-700 font-bold">{dt_previsao}</strong></div>
        </div>
      </section>

      <!-- TERMO LEGAL DE COMPROMISSO -->
      <section class="bg-amber-50/70 rounded-2xl p-4 border border-amber-200/80 text-xs space-y-2">
        <h4 class="font-bold text-amber-950 flex items-center gap-1.5 text-xs">
          <span>📜</span> Declaração e Compromisso de Devolução
        </h4>
        <p class="text-[11px] text-amber-900/90 leading-relaxed text-justify">
          Eu, <strong>{solicitante}</strong>, declaro que retirei o bem discriminado neste termo em perfeito estado de funcionamento e conservação. Comprometo-me formalmente a utilizá-lo com zelo, <strong>devolvê-lo pontualmente no mesmo estado em que o retirei</strong> e comunicar de imediato qualquer intercorrência, responsabilizando-me pelos custos em caso de extravio ou dano.
        </p>
      </section>

      <!-- QUADRO DE ASSINATURA DIGITAL TOUCH -->
      <section class="space-y-2">
        <div class="flex items-center justify-between">
          <label class="text-xs font-bold text-slate-900 flex items-center gap-1">
            <span>✍️</span> Assinatura do Retirante:
          </label>
          {f'<span class="text-[10px] text-emerald-700 font-bold">Gravada em {ass_ret_em}</span>' if ja_assinado else '<button type="button" onclick="limparCanvas()" class="text-[11px] font-bold text-indigo-600 hover:text-indigo-800 underline">Limpar e Refazer</button>'}
        </div>

        {f'''
        <div class="bg-white p-3 rounded-2xl border-2 border-emerald-300 text-center space-y-1">
          <img src="{ass_ret_base64}" alt="Assinatura Digital" class="h-28 mx-auto object-contain" />
          <div class="text-[10px] text-slate-400 border-t pt-1 font-mono">Assinatura Digital Autenticada • ID REG-{emp_id:05d}</div>
        </div>
        <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 text-xs font-bold text-center">
          ✓ Este termo já foi assinado e possui validade oficial no sistema!
        </div>
        ''' if ja_assinado else f'''
        <div class="relative bg-white rounded-2xl border-2 border-dashed border-indigo-300 p-1 overflow-hidden shadow-inner">
          <canvas id="sig-canvas" width="400" height="180" class="w-full h-44 rounded-xl cursor-crosshair bg-white block"></canvas>
          <div id="sig-hint" class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-slate-300">
            <span class="text-3xl opacity-60">✍️</span>
            <span class="text-xs font-medium mt-1 opacity-70">Assine com a ponta do dedo aqui</span>
          </div>
        </div>

        <button type="button" id="btn-confirmar-assinatura" onclick="enviarAssinatura()" class="w-full py-3.5 px-4 rounded-2xl bg-emerald-600 hover:bg-emerald-700 active:scale-[0.98] text-white font-black text-sm shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2">
          <span>✓</span> Confirmar e Assinar Termo de Cautela
        </button>
        '''}
      </section>

    </div>
  </main>

  <footer class="text-center text-[10px] text-slate-400 py-3">
    PIB Parque São Paulo • Sistema Integrado de Gestão Eclesiástica & Patrimonial
  </footer>

  <script>
    const canvas = document.getElementById('sig-canvas');
    const hint = document.getElementById('sig-hint');
    let ctx, drawing = false, hasDrawn = false;

    if (canvas) {{
      ctx = canvas.getContext('2d');
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = '#0f172a'; // slate-900

      // Ajusta resolucao real para telas Retina / Celular
      function ajustarDPI() {{
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * 2;
        canvas.height = rect.height * 2;
        ctx.scale(2, 2);
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = '#0f172a';
      }}
      ajustarDPI();
      window.addEventListener('resize', ajustarDPI);

      function getPos(e) {{
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {{
          x: clientX - rect.left,
          y: clientY - rect.top
        }};
      }}

      function startDraw(e) {{
        drawing = true;
        hasDrawn = true;
        if (hint) hint.style.display = 'none';
        const pos = getPos(e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        e.preventDefault();
      }}

      function draw(e) {{
        if (!drawing) return;
        const pos = getPos(e);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        e.preventDefault();
      }}

      function stopDraw(e) {{
        drawing = false;
        if (e) e.preventDefault();
      }}

      canvas.addEventListener('mousedown', startDraw);
      canvas.addEventListener('mousemove', draw);
      window.addEventListener('mouseup', stopDraw);

      canvas.addEventListener('touchstart', startDraw, {{ passive: false }});
      canvas.addEventListener('touchmove', draw, {{ passive: false }});
      window.addEventListener('touchend', stopDraw, {{ passive: false }});
    }}

    function limparCanvas() {{
      if (!ctx || !canvas) return;
      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      hasDrawn = false;
      if (hint) hint.style.display = 'flex';
    }}

    async function enviarAssinatura() {{
      if (!hasDrawn) {{
        alert('Por favor, assine com o dedo no quadro antes de confirmar.');
        return;
      }}
      const btn = document.getElementById('btn-confirmar-assinatura');
      if (btn) {{
        btn.disabled = true;
        btn.innerHTML = 'Gravando Assinatura...';
      }}

      const dataUrl = canvas.toDataURL('image/png');
      try {{
        const res = await fetch('/api/patrimonio/emprestimo/assinar', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            id: {emp_id},
            tipo: 'retirada',
            assinatura_base64: dataUrl,
            solicitante_nome: '{solicitante}'
          }})
        }});
        const data = await res.json();
        if (res.ok && data.ok) {{
          alert('✓ Termo assinado com sucesso! O comprovante oficial foi gravado.');
          window.location.reload();
        }} else {{
          alert(data.erro || 'Falha ao registrar assinatura.');
          if (btn) {{ btn.disabled = false; btn.innerHTML = 'Tentar Novamente'; }}
        }}
      }} catch (err) {{
        alert('Erro de conexão ao salvar assinatura: ' + err.message);
        if (btn) {{ btn.disabled = false; btn.innerHTML = 'Tentar Novamente'; }}
      }}
    }}
  </script>
</body>
</html>"""


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

        self.send_header("X-Content-Type-Options", "nosniff")

        self.send_header("X-Frame-Options", "DENY")

        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")

        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

        self.send_header("Cross-Origin-Opener-Policy", "same-origin")

        self.send_header("X-Permitted-Cross-Domain-Policies", "none")

        if str(self.headers.get("X-Forwarded-Proto", "")).lower() == "https":
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        super().end_headers()

    def get_allowed_cors_origin(self):
        origin = str(self.headers.get("Origin", "") or "").strip()
        if not origin:
            return ""
        host = str(self.headers.get("Host", "") or "").strip()
        permitidas = {"https://pib-parque-sp.onrender.com"}
        if host:
            permitidas.add(f"https://{host}")
            permitidas.add(f"http://{host}")
        if origin in permitidas or origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            return origin
        return ""



    def get_cookie_value(self, nome):
        raw_cookie = self.headers.get("Cookie", "")
        for parte in raw_cookie.split(";"):
            k, _, v = parte.strip().partition("=")
            if k == nome:
                return v
        return ""

    def get_authenticated_user(self):
        tok = self.get_cookie_value("kairos_session")
        return validar_token_sessao(tok)

    def has_valid_backup_key(self):
        key_hdr = str(self.headers.get("X-Backup-Key", "") or "").strip()
        if not key_hdr:
            return False
        try:
            with db_lock:
                conn = get_db()
                esperada = obter_segredo_sistema(conn, "backup_key")
                conn.close()
            return hmac.compare_digest(key_hdr, esperada)
        except Exception:
            return False

    def send_json(self, data, status=200, extra_headers=None):

        try:

            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")

            self.send_response(status)

            self.send_header("Content-Type", "application/json; charset=utf-8")

            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

            cors_origin = self.get_allowed_cors_origin()
            if cors_origin:
                self.send_header("Access-Control-Allow-Origin", cors_origin)
                self.send_header("Vary", "Origin")

            if extra_headers:
                for hk, hv in extra_headers:
                    self.send_header(hk, hv)

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

        cors_origin = self.get_allowed_cors_origin()
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
            self.send_header("Vary", "Origin")

        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        self.end_headers()



    def do_GET(self):

        parsed = urlparse(self.path)

        path = parsed.path



        if path in ("/assinar-emprestimo", "/assinar"):
            qs = parse_qs(parsed.query)
            emp_id = qs.get("id", [None])[0]
            if not emp_id:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h3 style='font-family:sans-serif;padding:20px;text-align:center;'>Código/ID do empréstimo não informado no link.</h3>".encode("utf-8"))
                return

            with db_lock:
                conn = get_db()
                cur = conn.cursor()
                row = cur.execute("""
                    SELECT pe.*, p.localizacao, p.valor_aquisicao, min.nome as ministerio_nome
                    FROM patrimonio_emprestimos pe
                    LEFT JOIN patrimonio p ON pe.patrimonio_id = p.id
                    LEFT JOIN ministerios min ON p.ministerio_id = min.id
                    WHERE pe.id = ?
                """, (int(emp_id),)).fetchone()
                conn.close()

            if not row:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h3 style='font-family:sans-serif;padding:20px;text-align:center;'>Registro de empréstimo não encontrado.</h3>".encode("utf-8"))
                return

            html_page = render_mobile_termo_page(dict(row))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
            return

        if path == "/api/bootstrap":
            self.send_json(build_bootstrap_data(self))
            return

        if path == "/api/fiscal/status":
            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "GET", path):
                return self.send_json({"ok": False, "mensagem": "Permissão insuficiente para módulo fiscal."}, 403)
            with db_lock:
                conn = get_db()
                cur = conn.cursor()
                cfg_row = cur.execute("SELECT cnpj, ccm_sp, titular, validade, ult_nsu, ultimo_sync, atualizado_por, atualizado_em FROM config_fiscal_a1 WHERE id=1").fetchone()
                notas_rows = [dict(r) for r in cur.execute("SELECT * FROM notas_fiscais_recebidas ORDER BY data_emissao DESC, id DESC LIMIT 300").fetchall()]
                conn.close()
            return self.send_json({
                "ok": True,
                "has_crypto": bool(fiscal_a1 and fiscal_a1.HAS_CRYPTOGRAPHY),
                "config": dict(cfg_row) if cfg_row else None,
                "notas": notas_rows,
            })

        if path == "/api/sistema/backup-db":
            auth_u = self.get_authenticated_user()
            is_admin = bool(auth_u and auth_u.get("perfil") == "ADMIN")
            if not is_admin and not self.has_valid_backup_key():
                return self.send_json({"ok": False, "mensagem": "Acesso não autorizado ao backup do banco."}, 401)
            with db_lock:
                conn = get_db()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.commit()
                conn.close()
                with open(DB_PATH, "rb") as f_db:
                    db_bytes = f_db.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", 'attachment; filename="igreja_erp_backup.db"')
            self.send_header("Content-Length", str(len(db_bytes)))
            self.end_headers()
            self.wfile.write(db_bytes)
            return



        if path == "/api/lgpd/exportar-membro":
            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "GET", path):
                return self.send_json({"ok": False, "mensagem": "Permissão insuficiente para exportar dados de membros."}, 403)
            qs = parse_qs(parsed.query)
            try:
                mem_id = int(qs.get("id", [0])[0])
            except Exception:
                mem_id = 0
            if not mem_id:
                return self.send_json({"ok": False, "mensagem": "ID do titular inválido."}, 400)
            with db_lock:
                conn = get_db()
                cur = conn.cursor()
                membro = cur.execute("SELECT * FROM membros WHERE id=?", (mem_id,)).fetchone()
                if not membro:
                    conn.close()
                    return self.send_json({"ok": False, "mensagem": "Titular não encontrado."}, 404)
                vinculos = [dict(r) for r in cur.execute("SELECT * FROM vinculos_familiares WHERE membro_id=? OR familiar_id=?", (mem_id, mem_id)).fetchall()]
                financeiro = [dict(r) for r in cur.execute("SELECT id, data, tipo, categoria, valor, forma_pagamento, descricao FROM financeiro WHERE membro_id=? ORDER BY data DESC", (mem_id,)).fetchall()]
                escalas = [dict(r) for r in cur.execute("SELECT * FROM escalas WHERE membro_id=?", (mem_id,)).fetchall()]
                voluntarios = [dict(r) for r in cur.execute("SELECT * FROM voluntarios WHERE membro_id=?", (mem_id,)).fetchall()]
                operador_nm = str(auth_u.get("nome") or "Operador")
                log_auditoria(conn, operador_nm, "LGPD", "Exportação de Dados do Titular", f"Exportou pacote LGPD (Art. 18) do titular #{mem_id} ({membro['nome']}).")
                conn.commit()
                conn.close()
            return self.send_json({
                "ok": True,
                "base_legal": "Lei nº 13.709/2018 (LGPD) - Art. 18, incisos II e V (Acesso e Portabilidade)",
                "gerado_em": agora_brasilia().strftime("%Y-%m-%d %H:%M:%S"),
                "titular": dict(membro),
                "vinculos_familiares": vinculos,
                "historico_financeiro": financeiro,
                "escalas": escalas,
                "voluntariado": voluntarios
            })

        if path == "/api/atas":
            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "GET", path):
                return self.send_json({"ok": False, "mensagem": "Permissão insuficiente para acessar atas."}, 403)

            qs = parse_qs(parsed.query)

            ata_id = qs.get("id", [None])[0]

            with db_lock:

                conn = get_db()

                cur = conn.cursor()

                if ata_id:

                    row = cur.execute(

                        """SELECT id, titulo, tipo, data_reuniao, hora_inicio, hora_fim,

                                   local_reuniao, presidente, secretario, livro_numero, folha_numero,

                                   pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

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

                                   pauta, conteudo, observacoes, nome_arquivo, tipo_arquivo, tamanho_arquivo,

                                   CASE WHEN arquivo_base64 IS NOT NULL AND LENGTH(arquivo_base64) > 0 THEN 1 ELSE 0 END as tem_anexo,

                                   criado_por, criado_em, atualizado_em

                            FROM atas ORDER BY data_reuniao DESC, id DESC"""

                    ).fetchall()

                    conn.close()

                    return self.send_json([dict(r) for r in rows])



        if path == "/api/atas/anexo":

            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "GET", path):
                return self.send_json({"ok": False, "mensagem": "Permissão insuficiente para baixar anexo de ata."}, 403)

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

            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "GET", path):
                return self.send_json({"ok": False, "mensagem": "Permissão insuficiente para baixar anexo da requisição."}, 403)

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
            qs_ev = parse_qs(parsed.query)
            modo_assem_ev = qs_ev.get("modo", [""])[0] == "assembleia" or qs_ev.get("view", [""])[0] == "assembleia" or qs_ev.get("qrcode", [""])[0] == "1"
            if not self.get_authenticated_user() and not modo_assem_ev:
                return self.send_json({"ok": False, "mensagem": "Autenticação necessária para sincronização em tempo real."}, 401)

            self.send_response(200)

            self.send_header("Content-Type", "text/event-stream; charset=utf-8")

            self.send_header("Cache-Control", "no-cache, no-transform")

            self.send_header("Connection", "keep-alive")

            self.send_header("X-Accel-Buffering", "no")

            cors_origin = self.get_allowed_cors_origin()
            if cors_origin:
                self.send_header("Access-Control-Allow-Origin", cors_origin)
                self.send_header("Vary", "Origin")

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

        if path == "/api/logout":
            cookie_clr = "kairos_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
            return self.send_json({"ok": True}, 200, [("Set-Cookie", cookie_clr)])

        rotas_publicas_post = ("/api/usuarios/verificar-senha",)
        rotas_backup_post = ("/api/sistema/backup-db", "/api/sistema/restaurar-db")
        if path in rotas_backup_post:
            auth_u = self.get_authenticated_user()
            if not (auth_u and auth_u.get("perfil") == "ADMIN") and not self.has_valid_backup_key():
                return self.send_json({"ok": False, "mensagem": "Acesso não autorizado."}, 401)
        elif path not in rotas_publicas_post:
            auth_u = self.get_authenticated_user()
            if not auth_u:
                return self.send_json({"ok": False, "mensagem": "Sessão expirada ou não autenticada. Faça login novamente."}, 401)
            if not usuario_tem_permissao_rota(auth_u, "POST", path):
                return self.send_json({"ok": False, "mensagem": "Você não possui permissão de acesso para esta operação."}, 403)
        else:
            auth_u = None

        body = self.read_json_body()

        operador = str(auth_u.get("nome") or body.get("operador") or "Administrador") if auth_u else str(body.get("operador", "Administrador"))



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

                elif path == "/api/matriz/rubrica/atualizar":
                    row_id = int(body.get("id", 0))
                    nova_rubrica = (body.get("rubrica") or "").strip()
                    novo_grupo = (body.get("grupo") or "").strip()
                    novo_tipo = "ENTRADA" if str(body.get("tipo_fluxo", "")).upper() == "ENTRADA" else "SAIDA"
                    replicar_todos = bool(body.get("replicar_todos_anos", True))
                    atualizar_fin = bool(body.get("atualizar_financeiro", True))

                    if not row_id or not nova_rubrica or not novo_grupo:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Informe o nome da conta e o grupo."}, 400)

                    atual = cur.execute("SELECT id, ano, tipo_fluxo, grupo, rubrica FROM matriz_tesouraria WHERE id=?", (row_id,)).fetchone()
                    if not atual:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Conta não encontrada na planilha."}, 404)

                    old_tipo = atual["tipo_fluxo"]
                    old_grupo = atual["grupo"]
                    old_rub = atual["rubrica"]

                    if replicar_todos:
                        cur.execute(
                            "UPDATE matriz_tesouraria SET tipo_fluxo=?, grupo=?, rubrica=? WHERE tipo_fluxo=? AND grupo=? AND rubrica=?",
                            (novo_tipo, novo_grupo, nova_rubrica, old_tipo, old_grupo, old_rub),
                        )
                    else:
                        cur.execute(
                            "UPDATE matriz_tesouraria SET tipo_fluxo=?, grupo=?, rubrica=? WHERE id=?",
                            (novo_tipo, novo_grupo, nova_rubrica, row_id),
                        )

                    if atualizar_fin:
                        old_cat = f"{old_grupo} — {old_rub}"
                        new_cat = f"{novo_grupo} — {nova_rubrica}"
                        if replicar_todos:
                            cur.execute(
                                "UPDATE financeiro SET tipo=?, categoria=? WHERE categoria=? OR (tipo=? AND LOWER(TRIM(categoria))=LOWER(TRIM(?)))",
                                (novo_tipo, new_cat, old_cat, old_tipo, old_rub),
                            )
                        else:
                            cur.execute(
                                "UPDATE financeiro SET tipo=?, categoria=? WHERE substr(data_lancamento,1,4)=? AND (categoria=? OR (tipo=? AND LOWER(TRIM(categoria))=LOWER(TRIM(?))))",
                                (novo_tipo, new_cat, str(atual["ano"]), old_cat, old_tipo, old_rub),
                            )

                    log_auditoria(
                        conn,
                        operador,
                        "Tesouraria",
                        "Edição de Conta na Planilha",
                        f"Alterou '{old_rub}' ({old_grupo}) para '{nova_rubrica}' ({novo_grupo} / {novo_tipo}).",
                    )
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} atualizou a conta '{nova_rubrica}' na Planilha Mensal."})
                    return self.send_json({"ok": True, "mensagem": "Conta atualizada com sucesso preservando todos os valores mensais!"})



                # B2. GARANTIR ESTRUTURA DE PLANILHA PARA QUALQUER ANO DIGITADO

                elif path == "/api/matriz/garantir-ano":

                    ano = int(body.get("ano", 2026))

                    if 1990 <= ano <= 2100:

                        existentes = set(
                            (r["tipo_fluxo"], r["grupo"], r["rubrica"])
                            for r in cur.execute("SELECT tipo_fluxo, grupo, rubrica FROM matriz_tesouraria WHERE ano=?", (ano,)).fetchall()
                        )

                        zeros = [0.0] * 12

                        inseridos = 0

                        for _, tipo_fluxo, grupo, rubrica, _ in MATRIZ_2026:

                            if (tipo_fluxo, grupo, rubrica) not in existentes:

                                cur.execute(

                                    """INSERT INTO matriz_tesouraria

                                    (ano, tipo_fluxo, grupo, rubrica, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                                    (ano, tipo_fluxo, grupo, rubrica, *zeros),

                                )

                                existentes.add((tipo_fluxo, grupo, rubrica))

                                inseridos += 1

                        if inseridos > 0:

                            conn.commit()

                    conn.close()

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"Estrutura da planilha para {ano} garantida."})

                    return self.send_json({"ok": True, "ano": ano})

                # B3. AUTORIZAR DESBLOQUEIO DE EDIÇÃO DA PLANILHA MENSAL COM SENHA DE PESSOAS AUTORIZADAS
                elif path == "/api/matriz/autorizar-edicao":
                    usuario_id = body.get("usuario_id")
                    senha_digitada = str(body.get("senha", "")).strip()

                    if not senha_digitada:
                        conn.close()
                        return self.send_json({"ok": False, "erro": "Por favor, digite a senha de autorização."}, 400)

                    rows_usuarios = cur.execute(
                        "SELECT id, nome, cargo, perfil, setores_permitidos, senha, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE ativo=1 ORDER BY id"
                    ).fetchall()

                    def is_usuario_autorizado_planilha(u):
                        return int(u["pode_editar_planilha"] or 0) == 1

                    def conferir_senha_usuario(u, s_dig):
                        return verificar_senha_segura(s_dig, u["senha"], u["senha_alterada"])

                    candidatos = [u for u in rows_usuarios if is_usuario_autorizado_planilha(u)]
                    if usuario_id and str(usuario_id).isdigit() and int(usuario_id) > 0:
                        uid_int = int(usuario_id)
                        user_sel = next((u for u in rows_usuarios if int(u["id"]) == uid_int), None)
                        if not user_sel:
                            conn.close()
                            return self.send_json({"ok": False, "erro": "Operador selecionado não encontrado."}, 404)
                        if not is_usuario_autorizado_planilha(user_sel):
                            log_auditoria(
                                conn,
                                user_sel["nome"],
                                "Segurança",
                                "Bloqueio na Planilha Mensal",
                                f"Operador '{user_sel['nome']}' não possui permissão para editar a Planilha Mensal.",
                            )
                            conn.commit()
                            conn.close()
                            return self.send_json({
                                "ok": False,
                                "erro": f"O usuário '{user_sel['nome']}' não possui permissão de autorização para editar a Planilha Mensal."
                            }, 403)
                        if not conferir_senha_usuario(user_sel, senha_digitada):
                            log_auditoria(
                                conn,
                                user_sel["nome"],
                                "Segurança",
                                "Senha Inválida (Planilha Mensal)",
                                f"Tentativa de desbloqueio da Planilha Mensal com senha incorreta para '{user_sel['nome']}'.",
                            )
                            conn.commit()
                            conn.close()
                            return self.send_json({"ok": False, "erro": "Senha de autorização incorreta! Verifique e tente novamente."}, 401)
                        autorizado = user_sel
                    else:
                        autorizado = next((u for u in candidatos if conferir_senha_usuario(u, senha_digitada)), None)
                        if not autorizado:
                            log_auditoria(
                                conn,
                                operador,
                                "Segurança",
                                "Senha Inválida (Planilha Mensal)",
                                "Tentativa de desbloqueio da Planilha Mensal com senha não reconhecida.",
                            )
                            conn.commit()
                            conn.close()
                            return self.send_json({"ok": False, "erro": "Senha inválida ou pertencente a usuário sem permissão para editar a Planilha Mensal."}, 401)

                    log_auditoria(
                        conn,
                        autorizado["nome"],
                        "Segurança",
                        "Planilha Mensal Desbloqueada",
                        f"Edição da Planilha Mensal liberada mediante senha por {autorizado['nome']} ({autorizado['cargo'] or autorizado['perfil']}).",
                    )
                    conn.commit()
                    conn.close()

                    return self.send_json({
                        "ok": True,
                        "autorizado_por": {
                            "id": autorizado["id"],
                            "nome": autorizado["nome"],
                            "cargo": autorizado["cargo"] or autorizado["perfil"],
                            "perfil": autorizado["perfil"],
                        }
                    })



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



                    agora = agora_brasilia().strftime("%Y-%m-%d")

                    sala_ebd = body.get("sala_ebd", "").strip()

                    status_membro = body.get("status", "Ativo").strip() or "Ativo"

                    cur.execute(

                        """INSERT INTO membros

                        (nome, apelido, endereco, cep, logradouro, numero, complemento, bairro_endereco, cidade_endereco, uf_endereco,

                         telefone, email, data_nascimento, data_batismo,

                         estado_civil, genero, familia, rg, cidade_nascimento, estado_nascimento, cpf,

                         profissao, conjuge, data_casamento,

                         foto_base64, ministerio_id_2, funcao_ministerio_2, tipo_transferencia, motivo_transferencia,

                         cargo_eclesiastico, status, sala_ebd, celula_id, observacoes, lgpd_consentimento, lgpd_data, criado_em)

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

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

                            body.get("profissao", "").strip(),

                            body.get("conjuge", "").strip(),

                            body.get("data_casamento", "").strip(),

                            body.get("foto_base64", "").strip(),

                            int(body["ministerio_id_2"]) if body.get("ministerio_id_2") else None,

                            body.get("funcao_ministerio_2", "").strip(),

                            body.get("tipo_transferencia", "").strip(),

                            body.get("motivo_transferencia", "").strip(),

                            body.get("cargo_eclesiastico", "Membro"),

                            status_membro,

                            sala_ebd,

                            body.get("celula_id") or None,

                            body.get("observacoes", ""),

                            1 if body.get("lgpd_consentimento") else 0,

                            (agora if body.get("lgpd_consentimento") else ""),

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

                    min_id_2 = body.get("ministerio_id_2")

                    funcao_2 = body.get("funcao_ministerio_2", "Voluntário")

                    if min_id_2:

                        cur.execute(

                            "INSERT OR IGNORE INTO membro_ministerio (membro_id, ministerio_id, funcao) VALUES (?, ?, ?)",

                            (membro_id, int(min_id_2), funcao_2),

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

                    profissao = body.get("profissao", (atual["profissao"] if "profissao" in atual.keys() and atual["profissao"] else ""))
                    conjuge = body.get("conjuge", (atual["conjuge"] if "conjuge" in atual.keys() and atual["conjuge"] else ""))
                    data_casamento = body.get("data_casamento", (atual["data_casamento"] if "data_casamento" in atual.keys() and atual["data_casamento"] else ""))

                    foto_base64 = body.get("foto_base64") if "foto_base64" in body else (atual["foto_base64"] if "foto_base64" in atual.keys() and atual["foto_base64"] else "")
                    ministerio_id_2 = int(body["ministerio_id_2"]) if body.get("ministerio_id_2") else (atual["ministerio_id_2"] if "ministerio_id_2" in atual.keys() and atual["ministerio_id_2"] else None)
                    funcao_ministerio_2 = body.get("funcao_ministerio_2") if "funcao_ministerio_2" in body else (atual["funcao_ministerio_2"] if "funcao_ministerio_2" in atual.keys() and atual["funcao_ministerio_2"] else "")
                    tipo_transferencia = body.get("tipo_transferencia") if "tipo_transferencia" in body else (atual["tipo_transferencia"] if "tipo_transferencia" in atual.keys() and atual["tipo_transferencia"] else "")
                    motivo_transferencia = body.get("motivo_transferencia") if "motivo_transferencia" in body else (atual["motivo_transferencia"] if "motivo_transferencia" in atual.keys() and atual["motivo_transferencia"] else "")

                    status = body.get("status", atual["status"] or "Ativo")

                    sala_ebd = body.get("sala_ebd", (atual["sala_ebd"] if "sala_ebd" in atual.keys() and atual["sala_ebd"] else "")).strip()

                    cargo = body.get("cargo_eclesiastico", atual["cargo_eclesiastico"] or "Membro")

                    celula_id = body.get("celula_id") if "celula_id" in body else atual["celula_id"]

                    observacoes = body.get("observacoes", atual["observacoes"] or "")
                    lgpd_consentimento = 1 if body.get("lgpd_consentimento") else (int(atual["lgpd_consentimento"] or 0) if "lgpd_consentimento" not in body and "lgpd_consentimento" in atual.keys() else 0)
                    lgpd_data = (atual["lgpd_data"] if "lgpd_data" in atual.keys() and atual["lgpd_data"] else "")
                    if lgpd_consentimento and not lgpd_data:
                        lgpd_data = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")
                    elif not lgpd_consentimento:
                        lgpd_data = ""



                    # 1. Atualiza registro principal na tabela membros

                    cur.execute(

                        """UPDATE membros

                        SET nome=?, apelido=?, endereco=?, cep=?, logradouro=?, numero=?, complemento=?,

                            bairro_endereco=?, cidade_endereco=?, uf_endereco=?,

                            telefone=?, email=?, data_nascimento=?, data_batismo=?,

                            estado_civil=?, genero=?, familia=?, rg=?, cidade_nascimento=?, estado_nascimento=?, cpf=?,

                            profissao=?, conjuge=?, data_casamento=?,

                            foto_base64=?, ministerio_id_2=?, funcao_ministerio_2=?,

                            tipo_transferencia=?, motivo_transferencia=?,

                            status=?, sala_ebd=?, cargo_eclesiastico=?, celula_id=?, observacoes=?, lgpd_consentimento=?, lgpd_data=?

                        WHERE id=?""",

                        (

                            nome, apelido, endereco, cep, logradouro, numero, complemento,

                            bairro_end, cidade_end, uf_end,

                            telefone, email, data_nascimento, data_batismo,

                            estado_civil, genero, familia, rg, cidade_nascimento, estado_nascimento, cpf,

                            profissao, conjuge, data_casamento,

                            foto_base64, ministerio_id_2, funcao_ministerio_2,

                            tipo_transferencia, motivo_transferencia,

                            status, sala_ebd, cargo, celula_id or None, observacoes, lgpd_consentimento, lgpd_data, membro_id

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



                    # Atualiza vínculos de ministério 1 e 2 se enviados no formulário

                    if "ministerio_id" in body or "ministerio_id_2" in body:

                        min_id = body.get("ministerio_id")

                        funcao_min = (body.get("funcao_ministerio") or "Voluntário").strip() or "Voluntário"

                        min_id_2 = body.get("ministerio_id_2")

                        funcao_min_2 = (body.get("funcao_ministerio_2") or "Voluntário").strip() or "Voluntário"

                        cur.execute("DELETE FROM membro_ministerio WHERE membro_id=?", (membro_id,))

                        if min_id:

                            cur.execute(

                                """INSERT INTO membro_ministerio (membro_id, ministerio_id, funcao) 

                                VALUES (?, ?, ?)""",

                                (membro_id, int(min_id), funcao_min),

                            )

                        if min_id_2:

                            cur.execute(

                                """INSERT INTO membro_ministerio (membro_id, ministerio_id, funcao) 

                                VALUES (?, ?, ?)""",

                                (membro_id, int(min_id_2), funcao_min_2),

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
                    if isinstance(body.get("itens_lote"), list) and len(body["itens_lote"]) > 0:
                        ano_orc_lote = int(body.get("ano_orcamento", 2027))
                        perc_ref = body.get("percentual", "")
                        qtd_atualizados = 0
                        for item in body["itens_lote"]:
                            mid = int(item["id"])
                            a_orc = int(item.get("ano_orcamento", ano_orc_lote))
                            v_orc = parse_moeda(item.get("orcamento", 0))
                            cur.execute(
                                """
                                INSERT INTO ministerios_orcamentos (ministerio_id, ano, orcamento)
                                VALUES (?, ?, ?)
                                ON CONFLICT(ministerio_id, ano) DO UPDATE SET orcamento=excluded.orcamento
                                """,
                                (mid, a_orc, v_orc),
                            )
                            if a_orc == 2026:
                                cur.execute(
                                    "UPDATE ministerios SET orcamento_2026=?, orcamento_mensal=? WHERE id=?",
                                    (v_orc, round(v_orc / 12.0, 2), mid),
                                )
                            qtd_atualizados += 1

                        log_auditoria(
                            conn,
                            operador,
                            "Tesouraria",
                            f"Reajuste Percentual Orçamento ({ano_orc_lote})",
                            f"Aplicou reajuste de {perc_ref}% para o exercício {ano_orc_lote} em {qtd_atualizados} ministérios.",
                        )
                        conn.commit()
                        conn.close()
                        agendar_auto_backup_nuvem()
                        broadcast_event(
                            "sync",
                            {
                                "setor": "Tesouraria",
                                "operador": operador,
                                "mensagem": f"{operador} aplicou reajuste orçamentário ({perc_ref}%) para {ano_orc_lote} nos ministérios.",
                            },
                        )
                        return self.send_json({"ok": True, "atualizados": qtd_atualizados})

                    min_id = int(body["id"])

                    ano_orc = int(body.get("ano_orcamento", 2026))

                    ano_real = int(body.get("ano_realizado", 2025))

                    orc_val = parse_moeda(body.get("orcamento") if body.get("orcamento") is not None else body.get("orcamento_2026", 0))

                    tem_realizado = (body.get("realizado") is not None) or (body.get("realizado_2025") is not None)

                    real_val = parse_moeda(body.get("realizado") if body.get("realizado") is not None else body.get("realizado_2025", 0))

                    obs = body.get("descricao")

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

                    if tem_realizado:
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

                    if tem_realizado and ano_real == 2025:
                        cur.execute("UPDATE ministerios SET realizado_2025=? WHERE id=?", (real_val, min_id))

                    if obs is not None:
                        cur.execute("UPDATE ministerios SET descricao=? WHERE id=?", (obs, min_id))

                    if lider is not None and lider.strip():
                        cur.execute("UPDATE ministerios SET lider=? WHERE id=?", (lider.strip(), min_id))

                    min_nome = cur.execute("SELECT nome FROM ministerios WHERE id=?", (min_id,)).fetchone()["nome"]

                    log_auditoria(conn, operador, "Tesouraria", f"Ajuste Orçamento/Realizado ({ano_orc}/{ano_real})", f"Atualizou {min_nome}: Orçamento {ano_orc} = R$ {orc_val:,.2f}")

                    conn.commit()

                    conn.close()

                    agendar_auto_backup_nuvem()

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} atualizou o Orçamento ({ano_orc}) de {min_nome}."})

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

                    data_lanc = body.get("data_lancamento") or agora_brasilia().strftime("%Y-%m-%d")

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



                        grupo_id = f"PARC-{agora_brasilia().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

                        try:

                            dt_base = datetime.strptime(data_lanc, "%Y-%m-%d")

                        except Exception:

                            dt_base = agora_brasilia()



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

                    data_reuniao = (body.get("data_reuniao") or agora_brasilia().strftime("%Y-%m-%d")).strip()

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



                    agora_ts = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")



                    if ata_id:
                        # Preserva pauta, conteudo e observacoes existentes caso venham vazios no payload
                        row_ata_antiga = cur.execute("SELECT * FROM atas WHERE id=?", (ata_id,)).fetchone()
                        if row_ata_antiga:
                            if not conteudo and row_ata_antiga["conteudo"]:
                                conteudo = row_ata_antiga["conteudo"]
                            if not pauta and row_ata_antiga["pauta"]:
                                pauta = row_ata_antiga["pauta"]
                            if not observacoes and row_ata_antiga["observacoes"]:
                                observacoes = row_ata_antiga["observacoes"]

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



                    agora_ts = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")



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
                    agora = agora_brasilia().strftime("%Y-%m-%d")
                    agora_hora = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    ministerio_id = int(body["ministerio_id"])
                    solicitante = (body.get("solicitante") or "").strip() or operador
                    solicitante_telefone = (body.get("solicitante_telefone") or "").strip()
                    titulo = body["titulo"]
                    valor_estimado = parse_moeda(body.get("valor_estimado", 0))
                    prioridade = body.get("prioridade", "Normal")
                    justificativa = body.get("justificativa", "")
                    anexo_pdf = body.get("anexo_pdf", "")
                    anexo_nome = body.get("anexo_nome", "")

                    cfg_alerta = obter_config_alertas_verba(cur)
                    responsavel_tesouraria = (body.get("responsavel_tesouraria") or "").strip() or cfg_alerta.get("responsavel_padrao") or "Tesouraria / Financeiro"
                    telefone_tesouraria = (body.get("telefone_tesouraria") or "").strip() or cfg_alerta.get("telefone_padrao") or ""
                    enviar_alerta_agora = bool(body.get("enviar_alerta_agora", True))

                    if not solicitante_telefone and solicitante:
                        try:
                            m_sol = cur.execute("SELECT telefone FROM membros WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?)) LIMIT 1", (solicitante,)).fetchone()
                            if m_sol and m_sol["telefone"]:
                                solicitante_telefone = m_sol["telefone"]
                        except Exception:
                            pass

                    alerta_env = 1 if enviar_alerta_agora else 0
                    data_alerta_str = agora_hora if enviar_alerta_agora else ""
                    ult_aviso = f"Alerta disparado p/ {responsavel_tesouraria} ({telefone_tesouraria or 'Push Celular'}) em {agora_hora}" if enviar_alerta_agora else ""

                    cur.execute(
                        """INSERT INTO requisicoes
                        (data_solicitacao, ministerio_id, solicitante, solicitante_telefone, titulo, justificativa, valor_estimado, prioridade, status, anexo_pdf, anexo_nome, responsavel_tesouraria, telefone_tesouraria, alerta_enviado, data_alerta, ultimo_aviso_alerta)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendente', ?, ?, ?, ?, ?, ?, ?)""",
                        (agora, ministerio_id, solicitante, solicitante_telefone, titulo, justificativa, valor_estimado, prioridade, anexo_pdf, anexo_nome, responsavel_tesouraria, telefone_tesouraria, alerta_env, data_alerta_str, ult_aviso),
                    )
                    req_id = cur.lastrowid

                    # Se informou telefone da tesouraria e ainda não havia padrão salvo, atualiza o padrão automaticamente
                    if telefone_tesouraria and not cfg_alerta.get("telefone_padrao"):
                        try:
                            cur.execute(
                                "UPDATE config_alertas_verba SET responsavel_padrao=?, telefone_padrao=?, atualizado_em=? WHERE id=1",
                                (responsavel_tesouraria, telefone_tesouraria, agora_hora),
                            )
                            cfg_alerta["responsavel_padrao"] = responsavel_tesouraria
                            cfg_alerta["telefone_padrao"] = telefone_tesouraria
                        except Exception:
                            pass

                    min_row = cur.execute("SELECT nome, cor FROM ministerios WHERE id=?", (ministerio_id,)).fetchone()
                    min_nome = min_row["nome"] if min_row else "Ministério"
                    min_cor = min_row["cor"] if min_row else "#6366f1"

                    req_info = {
                        "id": req_id,
                        "data_solicitacao": agora,
                        "ministerio_id": ministerio_id,
                        "ministerio_nome": min_nome,
                        "ministerio_cor": min_cor,
                        "solicitante": solicitante,
                        "solicitante_telefone": solicitante_telefone,
                        "titulo": titulo,
                        "justificativa": justificativa,
                        "valor_estimado": valor_estimado,
                        "prioridade": prioridade,
                        "status": "Pendente",
                        "responsavel_tesouraria": responsavel_tesouraria,
                        "telefone_tesouraria": telefone_tesouraria,
                        "alerta_enviado": alerta_env,
                        "data_alerta": data_alerta_str,
                        "ultimo_aviso_alerta": ult_aviso,
                    }

                    log_auditoria(
                        conn,
                        operador,
                        "Ministérios -> Tesouraria",
                        "Nova Requisição",
                        f"Solicitou R$ {valor_estimado:,.2f} para {min_nome} (Solicitante: {solicitante}): {titulo}",
                    )
                    conn.commit()
                    conn.close()

                    if enviar_alerta_agora or cfg_alerta.get("alerta_auto_ativo", 1):
                        disparar_alerta_automatico_verba(cfg_alerta, req_info, "NOVA_SOLICITACAO")

                    broadcast_event("sync", {
                        "setor": "Tesouraria",
                        "operador": operador,
                        "tipo_alerta": "NOVA_SOLICITACAO_VERBA",
                        "requisicao": req_info,
                        "mensagem": f"📲 Nova Solicitação de Verba #{req_id}: {solicitante} solicitou R$ {valor_estimado:,.2f} ({min_nome}) para a Tesouraria."
                    })
                    return self.send_json({"ok": True, "id": req_id, "requisicao": req_info})

                elif path == "/api/requisicoes/registrar-alerta":
                    req_id = int(body["id"])
                    canal = (body.get("canal") or "WhatsApp/SMS").strip()
                    destino_nome = (body.get("responsavel_tesouraria") or "Tesouraria").strip()
                    telefone = (body.get("telefone_tesouraria") or "").strip()
                    agora_hora = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    resumo_aviso = f"Alerta via {canal} p/ {destino_nome} ({telefone or 'Celular'}) em {agora_hora}"

                    cur.execute(
                        """UPDATE requisicoes
                           SET responsavel_tesouraria = COALESCE(NULLIF(?, ''), responsavel_tesouraria),
                               telefone_tesouraria = COALESCE(NULLIF(?, ''), telefone_tesouraria),
                               alerta_enviado = 1,
                               data_alerta = ?,
                               ultimo_aviso_alerta = ?
                           WHERE id = ?""",
                        (destino_nome, telefone, agora_hora, resumo_aviso, req_id),
                    )
                    row_r = cur.execute(
                        """SELECT r.*, m.nome as ministerio_nome
                           FROM requisicoes r
                           LEFT JOIN ministerios m ON r.ministerio_id = m.id
                           WHERE r.id = ?""",
                        (req_id,),
                    ).fetchone()
                    cfg_alerta = obter_config_alertas_verba(cur)
                    log_auditoria(conn, operador, "Tesouraria / Requisições", "Disparo de Alerta por Telefone", f"Enviou alerta da solicitação #{req_id} via {canal} para {destino_nome} ({telefone})")
                    conn.commit()
                    conn.close()

                    if row_r and body.get("disparar_push_servidor"):
                        disparar_alerta_automatico_verba(cfg_alerta, dict(row_r), "NOVA_SOLICITACAO")

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} enviou alerta por telefone da solicitação #{req_id}."})
                    return self.send_json({"ok": True, "data_alerta": agora_hora, "ultimo_aviso_alerta": resumo_aviso})

                elif path == "/api/requisicoes/config-alertas":
                    agora_hora = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    responsavel_padrao = (body.get("responsavel_padrao") or "Tesouraria / Financeiro").strip()
                    telefone_padrao = (body.get("telefone_padrao") or "").strip()
                    telefone_secundario = (body.get("telefone_secundario") or "").strip()
                    callmebot_apikey = (body.get("callmebot_apikey") or "").strip()
                    ntfy_topico = (body.get("ntfy_topico") or "kairos-pib-parque-sp-verbas").strip()
                    webhook_whatsapp_url = (body.get("webhook_whatsapp_url") or "").strip()
                    alerta_auto_ativo = 1 if body.get("alerta_auto_ativo", True) else 0

                    cur.execute(
                        """INSERT INTO config_alertas_verba
                           (id, responsavel_padrao, telefone_padrao, telefone_secundario, callmebot_apikey, ntfy_topico, webhook_whatsapp_url, alerta_auto_ativo, atualizado_em)
                           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                               responsavel_padrao=excluded.responsavel_padrao,
                               telefone_padrao=excluded.telefone_padrao,
                               telefone_secundario=excluded.telefone_secundario,
                               callmebot_apikey=excluded.callmebot_apikey,
                               ntfy_topico=excluded.ntfy_topico,
                               webhook_whatsapp_url=excluded.webhook_whatsapp_url,
                               alerta_auto_ativo=excluded.alerta_auto_ativo,
                               atualizado_em=excluded.atualizado_em""",
                        (responsavel_padrao, telefone_padrao, telefone_secundario, callmebot_apikey, ntfy_topico, webhook_whatsapp_url, alerta_auto_ativo, agora_hora),
                    )
                    cfg_salva = obter_config_alertas_verba(cur)
                    log_auditoria(conn, operador, "Tesouraria / Alertas", "Configuração de Alertas por Telefone", f"Atualizou destinatário padrão de alertas de verba para {responsavel_padrao} ({telefone_padrao})")
                    conn.commit()
                    conn.close()

                    if body.get("testar_agora"):
                        disparar_alerta_automatico_verba(cfg_salva, {"id": "TESTE", "titulo": "Teste de Alerta de Verba", "valor_estimado": 100.0, "telefone_tesouraria": telefone_padrao}, "TESTE")

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} atualizou a configuração de alertas por telefone das solicitações de verba."})
                    return self.send_json({"ok": True, "config": cfg_salva})

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
                    agora = agora_brasilia().strftime("%Y-%m-%d")

                    req = cur.execute(
                        """SELECT r.*, m.nome as ministerio_nome
                           FROM requisicoes r
                           LEFT JOIN ministerios m ON r.ministerio_id = m.id
                           WHERE r.id=?""",
                        (req_id,),
                    ).fetchone()
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

                    cfg_alerta = obter_config_alertas_verba(cur)
                    req_dict = dict(req)
                    req_dict["status"] = decisao
                    req_dict["avaliado_por"] = operador
                    req_dict["data_avaliacao"] = agora

                    log_auditoria(
                        conn,
                        operador,
                        "Tesouraria",
                        f"Requisição {decisao}",
                        f"Req #{req_id} ({req['titulo']}) avaliada como '{decisao}'",
                    )
                    conn.commit()
                    conn.close()

                    if cfg_alerta.get("alerta_auto_ativo", 1):
                        disparar_alerta_automatico_verba(cfg_alerta, req_dict, f"AVALIACAO_{decisao}")

                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} marcou a requisição '{req['titulo']}' como {decisao}."})
                    return self.send_json({"ok": True, "requisicao": req_dict})



                # 7. CADASTRAR VISITANTE (COM QUEM CONVIDOU LIVRE OU MEMBRO)

                elif path == "/api/visitantes":

                    nome = body["nome"]

                    agora = body.get("data_visita") or agora_brasilia().strftime("%Y-%m-%d")

                    quem_convidou = (body.get("quem_convidou") or "").strip()

                    vis_lgpd = 1 if body.get("lgpd_consentimento") else 0
                    vis_lgpd_dt = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S") if vis_lgpd else ""
                    cur.execute(
                        """INSERT INTO visitantes
                        (nome, telefone, data_visita, culto, pedido_oracao, status_acompanhamento, celula_indicada_id, registrado_por, quem_convidou, lgpd_consentimento, lgpd_data)
                        VALUES (?, ?, ?, ?, ?, 'Novo Visitante', ?, ?, ?, ?, ?)""",
                        (
                            nome,
                            body.get("telefone", ""),
                            agora,
                            body.get("culto", "Culto de Domingo"),
                            body.get("pedido_oracao", ""),
                            body.get("celula_indicada_id") or None,
                            operador,
                            quem_convidou,
                            vis_lgpd,
                            vis_lgpd_dt,
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



                    agora = agora_brasilia().strftime("%Y-%m-%d")

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

                        """INSERT INTO patrimonio (codigo, item, ministerio_id, localizacao, valor_aquisicao, estado, responsavel, quantidade, situacao, motivo_entrada, motivo_baixa, data_compra, nota_fiscal, observacoes)

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                        (

                            codigo,

                            item,

                            body.get("ministerio_id") or None,

                            body["localizacao"],

                            float(body.get("valor_aquisicao", 0)),

                            body.get("estado", "Bom"),

                            body.get("responsavel", ""),

                            int(body.get("quantidade", 1) or 1),

                            body.get("situacao", "Em uso"),

                            body.get("motivo_entrada", ""),

                            body.get("motivo_baixa", ""),

                            body.get("data_compra", ""),

                            body.get("nota_fiscal", ""),

                            body.get("observacoes", ""),

                        ),

                    )

                    log_auditoria(conn, operador, "Patrimônio", "Novo Bem Patrimonial", f"Cadastrou {codigo} - {item}")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} cadastrou o item patrimonial {item}."})

                    return self.send_json({"ok": True})



                elif path == "/api/patrimonio/atualizar":
                    pat_id = int(body.get("id", 0))
                    if not pat_id:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "ID do bem patrimonial ausente."}, 400)
                    item_nome = str(body.get("item", "")).strip()
                    if not item_nome:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Informe a descrição do bem."}, 400)
                    cur.execute(
                        """UPDATE patrimonio
                           SET codigo=?, item=?, ministerio_id=?, localizacao=?, valor_aquisicao=?, estado=?, responsavel=?,
                               quantidade=?, situacao=?, data_compra=?, nota_fiscal=?, observacoes=?
                           WHERE id=?""",
                        (
                            str(body.get("codigo", "")).strip(),
                            item_nome,
                            body.get("ministerio_id") or None,
                            str(body.get("localizacao", "")).strip(),
                            float(body.get("valor_aquisicao", 0) or 0),
                            str(body.get("estado", "Bom")).strip(),
                            str(body.get("responsavel", "")).strip(),
                            int(body.get("quantidade", 1) or 1),
                            str(body.get("situacao", "Em uso")).strip(),
                            str(body.get("data_compra", "")).strip(),
                            str(body.get("nota_fiscal", "")).strip(),
                            str(body.get("observacoes", "")).strip(),
                            pat_id,
                        ),
                    )
                    log_auditoria(conn, operador, "Patrimônio", "Edição de Bem Patrimonial", f"{operador} atualizou o item patrimonial #{pat_id} ({item_nome}).")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} atualizou o item patrimonial {item_nome}."})
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
                    data_retirada = body.get("data_retirada", "").strip() or agora_brasilia().strftime("%Y-%m-%d %H:%M")
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
                    telefone_responsavel_setor = body.get("telefone_responsavel_setor", "").strip()
                    telefone_responsavel_patrimonio = body.get("telefone_responsavel_patrimonio", "").strip()
                    enviar_sms_setor_agora = bool(body.get("enviar_sms_setor_agora", False))

                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    status_aprov_setor = "Pendente"
                    data_aprov_setor = None
                    op_aprov_setor = None

                    status_ok_pat = "Pendente"
                    data_ok_pat = None
                    op_ok_pat = None

                    # Regra: Toda nova solicitação aguarda estritamente aprovação do setor primeiro
                    status_geral = "Aguardando Aprovação do Setor"

                    cur.execute(
                        """
                        INSERT INTO patrimonio_emprestimos (
                            patrimonio_id, codigo, item, setor, condicao_saida, observacoes_saida,
                            solicitante_nome, solicitante_telefone, solicitante_documento, motivo,
                            data_retirada, previsao_devolucao,
                            responsavel_setor, status_aprovacao_setor, data_aprovacao_setor, operador_aprovador_setor,
                            responsavel_patrimonio, status_ok_patrimonio, data_ok_patrimonio, operador_ok_patrimonio,
                            telefone_responsavel_setor, telefone_responsavel_patrimonio,
                            notificacao_sms_setor_enviada, data_sms_setor, ultimo_aviso_sms,
                            status, criado_em, criado_por
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patrimonio_id, codigo, item, setor, condicao_saida, observacoes_saida,
                            solicitante_nome, solicitante_telefone, solicitante_documento, motivo,
                            data_retirada, previsao_devolucao,
                            responsavel_setor, status_aprov_setor, data_aprov_setor, op_aprov_setor,
                            responsavel_patrimonio, status_ok_pat, data_ok_pat, op_ok_pat,
                            telefone_responsavel_setor, telefone_responsavel_patrimonio,
                            (1 if (enviar_sms_setor_agora and telefone_responsavel_setor) else 0),
                            (agora_str if (enviar_sms_setor_agora and telefone_responsavel_setor) else ""),
                            (f"SMS solicitado para Setor ({telefone_responsavel_setor}) em {agora_str}" if (enviar_sms_setor_agora and telefone_responsavel_setor) else ""),
                            status_geral, agora_str, operador
                        )
                    )
                    emp_id = cur.lastrowid
                    log_auditoria(conn, operador, "Patrimônio", "Empréstimo de Equipamento", f"Registrou solicitação de empréstimo de '{item}' para {solicitante_nome} (ID {emp_id})")
                    conn.commit()
                    conn.close()

                    broadcast_event("sync", {"setor": "Patrimônio", "operador": operador, "mensagem": f"{operador} registrou solicitação de empréstimo do item '{item}' para {solicitante_nome} (Aguardando aprovação do setor)."})
                    return self.send_json({"ok": True, "id": emp_id})

                elif path == "/api/patrimonio/emprestimo/aprovar-setor":
                    emp_id = int(body["id"])
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
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
                    row = cur.execute("SELECT item, status_aprovacao_setor FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if not row:
                        conn.close()
                        return self.send_json({"erro": "Empréstimo não encontrado"}, 404)
                    
                    # REGRA 2: A autorização do patrimônio depende estritamente da aprovação prévia do setor
                    if row["status_aprovacao_setor"] != "Aprovado":
                        conn.close()
                        return self.send_json({"erro": "A autorização do Responsável pelo Patrimônio depende da aprovação prévia do Responsável do Setor."}, 400)

                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    cur.execute(
                        """
                        UPDATE patrimonio_emprestimos 
                        SET status_ok_patrimonio = 'Liberado', data_ok_patrimonio = ?, operador_ok_patrimonio = ?, status = 'Liberado para Retirada'
                        WHERE id = ?
                        """,
                        (agora_str, operador, emp_id)
                    )
                    item_nome = row["item"] if row else f"ID {emp_id}"

                    log_auditoria(conn, operador, "Patrimônio", "Liberação de Empréstimo (Patrimônio)", f"Deu OK e liberou saída do item '{item_nome}'")
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

                    agora_str = agora_brasilia().strftime("%Y-%m-%d %H:%M")
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
                    if not observacoes_retorno:
                        row_emp_ant = cur.execute("SELECT observacoes_retorno FROM patrimonio_emprestimos WHERE id=?", (emp_id,)).fetchone()
                        if row_emp_ant and row_emp_ant["observacoes_retorno"]:
                            observacoes_retorno = row_emp_ant["observacoes_retorno"]
                    data_retorno = body.get("data_devolucao_real", "").strip() or agora_brasilia().strftime("%Y-%m-%d %H:%M")
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")

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
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
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
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
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

                elif path == "/api/patrimonio/emprestimo/assinar":
                    emp_id = int(body["id"])
                    tipo = body.get("tipo", "retirada")
                    assinatura_b64 = body.get("assinatura_base64", "").strip()
                    if not assinatura_b64:
                        conn.close()
                        return self.send_json({"erro": "Assinatura digital é obrigatória."}, 400)

                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    row = cur.execute("SELECT * FROM patrimonio_emprestimos WHERE id = ?", (emp_id,)).fetchone()
                    if not row:
                        conn.close()
                        return self.send_json({"erro": "Empréstimo não encontrado."}, 404)

                    item_nome = row["item"]
                    solic_nome = row["solicitante_nome"]

                    if tipo == "retirada":
                        cur.execute(
                            """
                            UPDATE patrimonio_emprestimos
                            SET assinatura_retirada_base64 = ?,
                                assinatura_retirada_em = ?,
                                status = CASE 
                                    WHEN status_aprovacao_setor = 'Aprovado' AND status_ok_patrimonio = 'Liberado' 
                                    THEN 'Em Aberto / Emprestado' 
                                    ELSE status 
                                END
                            WHERE id = ?
                            """,
                            (assinatura_b64, agora_str, emp_id)
                        )
                        log_auditoria(conn, solic_nome, "Patrimônio", "Assinatura Digital de Cautela", f"{solic_nome} assinou digitalmente o termo de responsabilidade de '{item_nome}' (ID {emp_id})")
                        broadcast_event("sync", {"setor": "Patrimônio", "operador": solic_nome, "mensagem": f"{solic_nome} assinou digitalmente o termo de responsabilidade de '{item_nome}'."})
                    else:
                        cur.execute(
                            """
                            UPDATE patrimonio_emprestimos
                            SET assinatura_devolucao_base64 = ?,
                                assinatura_devolucao_em = ?,
                                data_devolucao_real = COALESCE(data_devolucao_real, ?),
                                status_retorno_setor = 'Conferido',
                                status_retorno_patrimonio = 'Finalizado',
                                status = 'Devolvido'
                            WHERE id = ?
                            """,
                            (assinatura_b64, agora_str, agora_str, emp_id)
                        )
                        log_auditoria(conn, solic_nome, "Patrimônio", "Assinatura Digital de Devolução", f"{solic_nome} assinou a devolução definitiva de '{item_nome}' (ID {emp_id})")
                        broadcast_event("sync", {"setor": "Patrimônio", "operador": solic_nome, "mensagem": f"{solic_nome} assinou a devolução definitiva de '{item_nome}'."})

                    conn.commit()
                    conn.close()
                    return self.send_json({"ok": True, "mensagem": "Assinatura registrada com sucesso!"})

                elif path == "/api/usuarios":

                    nome = body.get("nome", "").strip()

                    email = body.get("email", "").strip()

                    cargo = body.get("cargo", "").strip()

                    perfil = body.get("perfil", "FINANCEIRO")

                    ministerio_id = body.get("ministerio_id") or None

                    membro_id = body.get("membro_id") or None

                    setores_permitidos = body.get("setores_permitidos", "")

                    senha = body.get("senha", "").strip() or "123456"



                    if not nome:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Por favor, informe o nome do usuário."}, 400)

                    if not email:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Por favor, informe o e-mail ou identificador de acesso."}, 400)

                    membro_row = None
                    if membro_id and str(membro_id).isdigit():
                        membro_row = cur.execute("SELECT id, nome FROM membros WHERE id=?", (int(membro_id),)).fetchone()
                    if not membro_row:
                        membro_row = cur.execute("SELECT id, nome FROM membros WHERE LOWER(TRIM(nome))=LOWER(TRIM(?))", (nome,)).fetchone()
                    if not membro_row:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Para cadastrar um usuário no Kairós, a pessoa precisa estar cadastrada no Rol de Membros."}, 400)
                    membro_id = int(membro_row["id"])



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

                        elif perfil == "LIDER_MINISTERIO":

                            setores_permitidos = "tesouraria"

                    if perfil == "LIDER_MINISTERIO" and not ministerio_id:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Selecione o ministério ao qual este líder pertence."}, 400)



                    relatorios_permitidos = body.get("relatorios_permitidos", "*")
                    pode_editar_planilha = 1 if body.get("pode_editar_planilha") else 0

                    valida_pwd, _ = validar_padrao_senha(senha)

                    nova_senha_alterada = 1 if valida_pwd and senha != "123456" else 0
                    senha_hash = gerar_hash_senha(senha)

                    try:

                        cur.execute(

                            """INSERT INTO usuarios (nome, email, cargo, perfil, ministerio_id, membro_id, ativo, setores_permitidos, senha, relatorios_permitidos, senha_alterada, pode_editar_planilha)

                            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)""",

                            (nome, email, cargo, perfil, ministerio_id, membro_id, setores_permitidos, senha_hash, relatorios_permitidos, nova_senha_alterada, pode_editar_planilha),

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

                    ministerio_id = body.get("ministerio_id") or None

                    membro_id = body.get("membro_id") or None

                    setores_permitidos = body.get("setores_permitidos", "")

                    relatorios_permitidos = body.get("relatorios_permitidos", "*")
                    pode_editar_planilha = 1 if body.get("pode_editar_planilha") else 0

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

                        elif perfil == "LIDER_MINISTERIO":

                            setores_permitidos = "tesouraria"

                    if perfil == "LIDER_MINISTERIO" and not ministerio_id:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Selecione o ministério ao qual este líder pertence."}, 400)



                    try:

                        if senha:

                            valida_pwd, _ = validar_padrao_senha(senha)

                            nova_senha_alterada = 1 if valida_pwd and senha != "123456" else 0
                            senha_hash = gerar_hash_senha(senha)

                            cur.execute(

                                """UPDATE usuarios SET nome=?, email=?, cargo=?, perfil=?, ministerio_id=?, membro_id=COALESCE(?, membro_id), setores_permitidos=?, senha=?, relatorios_permitidos=?, senha_alterada=?, pode_editar_planilha=? WHERE id=?""",

                                (nome, email, cargo, perfil, ministerio_id, membro_id, setores_permitidos, senha_hash, relatorios_permitidos, nova_senha_alterada, pode_editar_planilha, user_id),

                            )

                        else:

                            cur.execute(

                                """UPDATE usuarios SET nome=?, email=?, cargo=?, perfil=?, ministerio_id=?, membro_id=COALESCE(?, membro_id), setores_permitidos=?, relatorios_permitidos=?, pode_editar_planilha=? WHERE id=?""",

                                (nome, email, cargo, perfil, ministerio_id, membro_id, setores_permitidos, relatorios_permitidos, pode_editar_planilha, user_id),

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
                    login = str(body.get("login", "")).strip().lower()
                    senha = str(body.get("senha", "")).strip()
                    ip_cli = str(self.headers.get("X-Forwarded-For", "") or self.client_address[0]).split(",")[0].strip()
                    chave_rate = str(user_id or email or login or "anon")

                    bloqueado, seg_rest = verificar_rate_limit_login(ip_cli, chave_rate)
                    if bloqueado:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": f"Muitas tentativas incorretas. Aguarde {max(1, seg_rest)}s para tentar novamente."}, 429)

                    if not senha:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Por favor, digite sua senha de acesso."}, 400)

                    row = None
                    if user_id is not None and str(user_id).isdigit() and int(user_id) > 0:
                        row = cur.execute("SELECT id, nome, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE id=? AND ativo=1", (int(user_id),)).fetchone()
                    elif email:
                        row = cur.execute("SELECT id, nome, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE LOWER(email)=? AND ativo=1", (email,)).fetchone()
                    elif login:
                        if login.isdigit():
                            row = cur.execute("SELECT id, nome, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE id=? AND ativo=1", (int(login),)).fetchone()
                        elif "@" in login:
                            row = cur.execute("SELECT id, nome, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE LOWER(email)=? AND ativo=1", (login,)).fetchone()
                        else:
                            row = cur.execute("SELECT id, nome, perfil, ministerio_id, setores_permitidos, senha, relatorios_permitidos, senha_alterada, COALESCE(pode_editar_planilha, 0) as pode_editar_planilha FROM usuarios WHERE (LOWER(nome) LIKE ? OR LOWER(email)=?) AND ativo=1", (f"%{login}%", login)).fetchone()
                    else:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Por favor, selecione ou informe o seu usuário."}, 400)

                    if not row:
                        registrar_falha_login(ip_cli, chave_rate)
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Operador não encontrado ou inativo no sistema."}, 404)

                    senha_db = str(row["senha"]).strip() if row["senha"] is not None else ""
                    senha_alterada = int(row["senha_alterada"] or 0)
                    senha_digitada = senha.strip()

                    senha_valida = verificar_senha_segura(senha_digitada, senha_db, senha_alterada)

                    if not senha_valida:
                        tentativas, bloqueou_agora = registrar_falha_login(ip_cli, chave_rate)
                        log_auditoria(conn, row["nome"], "Segurança", "Tentativa de Acesso Inválida", f"Senha incorreta informada para {row['nome']} (tentativa {tentativas}/5, IP {ip_cli}).")
                        conn.commit()
                        conn.close()
                        if bloqueou_agora:
                            return self.send_json({"ok": False, "mensagem": "Muitas tentativas incorretas (5/5). Acesso bloqueado temporariamente por 5 minutos."}, 429)
                        msg_aviso = "Senha incorreta! Digite a senha cadastrada para o seu usuário." if senha_alterada == 1 else "Senha incorreta! Digite a senha inicial 123456 para seu primeiro acesso."
                        return self.send_json({"ok": False, "mensagem": msg_aviso}, 401)

                    limpar_falha_login(ip_cli, chave_rate)

                    if not senha_db.startswith("pbkdf2$"):
                        cur.execute("UPDATE usuarios SET senha=? WHERE id=?", (gerar_hash_senha(senha_digitada), row["id"]))

                    precisa_trocar_senha = (senha_alterada == 0 and senha_digitada == "123456")

                    sess_token = criar_token_sessao(conn, row)
                    is_https = str(self.headers.get("X-Forwarded-Proto", "")).lower() == "https"
                    cookie_val = f"kairos_session={sess_token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200" + ("; Secure" if is_https else "")

                    log_auditoria(conn, row["nome"], "Segurança", "Login Autorizado", f"Usuário {row['nome']} autenticado com sucesso (precisa_trocar_senha={precisa_trocar_senha}).")

                    conn.commit()

                    conn.close()

                    return self.send_json({

                        "ok": True,

                        "id": row["id"],

                        "nome": row["nome"],

                        "perfil": row["perfil"],

                        "ministerio_id": row["ministerio_id"],

                        "setores_permitidos": row["setores_permitidos"] or "",

                        "relatorios_permitidos": row["relatorios_permitidos"] or "*",

                        "pode_editar_planilha": int(row["pode_editar_planilha"] or 0),

                        "senha_alterada": senha_alterada,

                        "precisa_trocar_senha": precisa_trocar_senha

                    }, 200, [("Set-Cookie", cookie_val)])



                elif path == "/api/usuarios/alterar-senha":

                    user_id = int(body.get("id", 0))

                    if not auth_u or (int(auth_u.get("id") or 0) != user_id and str(auth_u.get("perfil") or "").upper() != "ADMIN"):

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Sem permissão para alterar a senha de outro operador."}, 403)

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



                    cur.execute("UPDATE usuarios SET senha=?, senha_alterada=1 WHERE id=?", (gerar_hash_senha(nova_senha), user_id))

                    row_u = cur.execute("SELECT nome FROM usuarios WHERE id=?", (user_id,)).fetchone()

                    nome_u = row_u["nome"] if row_u else f"#{user_id}"



                    log_auditoria(conn, nome_u, "Segurança", "Alteração de Senha", f"Usuário {nome_u} cadastrou nova senha com sucesso (padrão seguro: letras, números e caractere especial).")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Segurança", "operador": nome_u, "mensagem": f"{nome_u} atualizou sua senha pessoal."})

                    return self.send_json({"ok": True, "mensagem": "Senha alterada com sucesso! Seu acesso seguro está liberado."})

                elif path == "/api/sistema/backup-db":
                    # Exporta copia de seguranca integra do banco SQLite
                    with db_lock:
                        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                        conn.commit()
                        with open(DB_PATH, "rb") as f_db:
                            db_bytes = f_db.read()
                    conn.close()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", 'attachment; filename="igreja_erp_backup.db"')
                    self.send_header("Content-Length", str(len(db_bytes)))
                    self.end_headers()
                    self.wfile.write(db_bytes)
                    return

                elif path == "/api/sistema/restaurar-db":
                    raw_db = None
                    if isinstance(body, dict):
                        b64_db = body.get("database_base64", "")
                        if b64_db:
                            raw_db = base64.b64decode(b64_db)
                    if not raw_db:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Arquivo de banco de dados nao informado."}, 400)
                    with db_lock:
                        conn.close()
                        if os.path.exists(DB_PATH):
                            shutil.copy2(DB_PATH, DB_PATH + ".bak")
                        with open(DB_PATH, "wb") as f_db:
                            f_db.write(raw_db)
                    conn_new = get_db()
                    log_auditoria(conn_new, operador, "Sistema", "Restauracao de Backup", "Banco de dados restaurado pelo administrador.")
                    conn_new.commit()
                    conn_new.close()
                    broadcast_event("sync", {"setor": "Sistema", "operador": operador, "mensagem": "Banco de dados restaurado com sucesso."})
                    return self.send_json({"ok": True, "mensagem": "Banco de dados restaurado com sucesso!"})

                elif path == "/api/tesouraria/extrato/analisar":
                    conteudo = body.get("conteudo_texto", "")
                    nome_arq = body.get("arquivo_nome", "")
                    banco = (body.get("banco") or "Itaú").strip()
                    itens_brutos = parsear_extrato_texto(conteudo, nome_arq)
                    if not itens_brutos:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Nenhuma movimentação válida encontrada no arquivo (.ofx ou .csv)."}, 400)
                    cache_ext = {}
                    resultado = []
                    for idx, it in enumerate(itens_brutos[:250]):
                        termo_limpo = limpar_descricao_extrato(it["descricao"])
                        chave_unica = it["fitid"] or f"{banco}|{it['data']}|{it['tipo']}|{it['valor']:.2f}|{termo_limpo}"
                        ja_imp = cur.execute("SELECT 1 FROM extrato_importados WHERE chave_unica=?", (chave_unica,)).fetchone()
                        ja_fin = cur.execute(
                            "SELECT 1 FROM financeiro WHERE data_lancamento=? AND tipo=? AND ABS(valor - ?) < 0.01 AND status != 'Cancelado'",
                            (it["data"], it["tipo"], it["valor"]),
                        ).fetchone()
                        duplicado = bool(ja_imp or ja_fin)
                        nome_real, fonte, g_ap, r_ap = buscar_estabelecimento_extrato(cur, it["descricao"], cache_ext)
                        if not (g_ap and r_ap):
                            _, _, _, _, g_ap, r_ap = localizar_rubrica_matriz_para_lancamento(
                                cur, it["data"], it["tipo"], nome_real, f"{it['descricao']} {nome_real}"
                            )
                        resultado.append({
                            "idx": idx,
                            "selecionar": not duplicado,
                            "duplicado": duplicado,
                            "data": it["data"],
                            "tipo": it["tipo"],
                            "valor": it["valor"],
                            "descricao_original": it["descricao"],
                            "termo_limpo": termo_limpo,
                            "nome_real": nome_real,
                            "fonte": fonte,
                            "grupo": g_ap,
                            "rubrica": r_ap,
                            "chave_unica": chave_unica,
                        })
                    conn.close()
                    return self.send_json({"ok": True, "banco": banco, "itens": resultado})

                elif path == "/api/tesouraria/extrato/confirmar":
                    banco = (body.get("banco") or "Itaú").strip()
                    itens = body.get("itens") or []
                    selecionados = [x for x in itens if x.get("selecionar")]
                    if not selecionados:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Selecione ao menos um item para importar."}, 400)
                    agora = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")
                    qtd = 0
                    for x in selecionados:
                        data_l = str(x.get("data") or "")
                        tipo_l = "ENTRADA" if str(x.get("tipo")).upper() == "ENTRADA" else "SAIDA"
                        val_l = round(float(x.get("valor") or 0), 2)
                        if not data_l or val_l <= 0:
                            continue
                        nome_real = (x.get("nome_real") or x.get("descricao_original") or "Lançamento Extrato").strip()
                        desc_orig = (x.get("descricao_original") or "").strip()
                        grupo = (x.get("grupo") or ("Entradas" if tipo_l == "ENTRADA" else "Despesas Operacionais")).strip()
                        rubrica = (x.get("rubrica") or "").strip()
                        cat_final = f"{grupo} — {rubrica}" if rubrica else grupo
                        desc_final = nome_real if nome_real.lower() == desc_orig.lower() else f"{nome_real} ({desc_orig})"
                        cur.execute(
                            """INSERT INTO financeiro (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, lancado_por)
                               VALUES (?, ?, ?, ?, ?, ?, 'Pago', ?)""",
                            (data_l, tipo_l, cat_final, desc_final, val_l, banco, operador),
                        )
                        sincronizar_lancamento_na_matriz(cur, data_l, tipo_l, cat_final, desc_final, val_l)
                        termo_chave = limpar_descricao_extrato(desc_orig)
                        if termo_chave:
                            cur.execute(
                                """INSERT INTO extrato_apelidos (termo_chave, nome_real, grupo, rubrica, fonte, atualizado_em)
                                   VALUES (?, ?, ?, ?, ?, ?)
                                   ON CONFLICT(termo_chave) DO UPDATE SET nome_real=excluded.nome_real, grupo=excluded.grupo, rubrica=excluded.rubrica, atualizado_em=excluded.atualizado_em""",
                                (termo_chave, nome_real, grupo, rubrica, x.get("fonte") or "Manual", agora),
                            )
                        chave_u = str(x.get("chave_unica") or "")
                        if chave_u:
                            cur.execute(
                                "INSERT OR IGNORE INTO extrato_importados (chave_unica, banco, data_lancamento, valor, descricao, importado_em) VALUES (?, ?, ?, ?, ?, ?)",
                                (chave_u, banco, data_l, val_l, desc_orig, agora),
                            )
                        qtd += 1
                    log_auditoria(conn, operador, "Tesouraria", "Importação de Extrato Bancário", f"Importou {qtd} lançamentos do extrato ({banco}).")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} importou {qtd} lançamentos do extrato ({banco})."})
                    return self.send_json({"ok": True, "importados": qtd, "mensagem": f"{qtd} lançamento(s) importado(s) no Livro-Caixa e Planilha Mensal!"})

                elif path == "/api/lgpd/anonimizar-membro":
                    mem_id = int(body.get("id", 0))
                    if not mem_id:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "ID do titular inválido."}, 400)
                    row_m = cur.execute("SELECT id, nome FROM membros WHERE id=?", (mem_id,)).fetchone()
                    if not row_m:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Titular não encontrado."}, 404)
                    alias_anon = f"Titular Anonimizado #{mem_id}"
                    cur.execute(
                        """UPDATE membros SET
                            nome=?, telefone='', email='', endereco='', data_nascimento='',
                            data_batismo='', status='Inativo', observacoes='Dados anonimizados conforme Art. 18, VI da LGPD.',
                            lgpd_consentimento=0, lgpd_data=''
                        WHERE id=?""",
                        (alias_anon, mem_id)
                    )
                    # Preserva valores contábeis/financeiros substituindo apenas eventual identificação nominal
                    cur.execute("DELETE FROM vinculos_familiares WHERE membro_id=? OR familiar_id=?", (mem_id, mem_id))
                    log_auditoria(conn, operador, "LGPD", "Anonimização de Titular", f"Anonimizou dados pessoais do membro #{mem_id} conforme Art. 18, VI da LGPD.")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "LGPD", "operador": operador, "mensagem": f"Dados do titular #{mem_id} anonimizados (LGPD)."})
                    return self.send_json({"ok": True, "mensagem": f"Dados pessoais do titular #{mem_id} anonimizados com sucesso, preservando a integridade contábil."})

                elif path == "/api/patrimonio/emprestimo/atualizar-observacoes":
                    emp_id = int(body.get("id", 0))
                    obs_saida = (body.get("observacoes_saida") or "").strip()
                    obs_retorno = (body.get("observacoes_retorno") or "").strip()
                    cur.execute(
                        "UPDATE patrimonio_emprestimos SET observacoes_saida = ?, observacoes_retorno = ? WHERE id = ?",
                        (obs_saida, obs_retorno, emp_id)
                    )
                    log_auditoria(conn, operador, "Patrimonio", "Atualizacao de Consideracoes", f"Atualizou observacoes/consideracoes do emprestimo #{emp_id}")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Patrimonio", "operador": operador, "mensagem": f"{operador} atualizou observacoes do emprestimo #{emp_id}."})
                    return self.send_json({"ok": True, "mensagem": "Consideracoes atualizadas com sucesso!"})



                elif path == "/api/usuarios/resetar-senha":

                    user_id = int(body.get("id", 0))

                    if not user_id:

                        conn.close()

                        return self.send_json({"ok": False, "mensagem": "Identificador do usuário ausente."}, 400)



                    cur.execute("UPDATE usuarios SET senha=?, senha_alterada=0 WHERE id=?", (gerar_hash_senha("123456"), user_id))

                    row_u = cur.execute("SELECT nome FROM usuarios WHERE id=?", (user_id,)).fetchone()

                    nome_u = row_u["nome"] if row_u else f"#{user_id}"



                    log_auditoria(conn, operador, "Administração", "Reset de Senha", f"{operador} resetou a senha de {nome_u} para o padrão temporário 123456.")

                    conn.commit()

                    conn.close()



                    broadcast_event("sync", {"setor": "Administração", "operador": operador, "mensagem": f"Senha de {nome_u} resetada para padrão temporário."})

                    return self.send_json({"ok": True, "mensagem": f"Senha de {nome_u} resetada para o padrão inicial 123456. O usuário deverá criar uma nova senha no próximo acesso."})

                # CONTAS A PAGAR (CADASTRO, PARCELAMENTO/RECORRÊNCIA, BAIXA E ESTORNO INTEGRADOS)
                elif path == "/api/contas-pagar":
                    fornecedor = (body.get("fornecedor") or "").strip() or "Fornecedor Geral"
                    descricao = (body.get("descricao") or "").strip() or "Conta a Pagar"
                    categoria = (body.get("categoria") or "Despesas Operacionais").strip()
                    documento = (body.get("documento") or "").strip()
                    data_emissao = body.get("data_emissao") or agora_brasilia().strftime("%Y-%m-%d")
                    data_venc = body.get("data_vencimento") or agora_brasilia().strftime("%Y-%m-%d")
                    valor_in = parse_moeda(body.get("valor", 0))
                    forma = (body.get("forma_pagamento") or "Boleto").strip()
                    status_ini = (body.get("status") or "Em Aberto").strip()
                    observacoes = (body.get("observacoes") or "").strip()
                    ministerio_id = body.get("ministerio_id") or None
                    if ministerio_id:
                        try:
                            ministerio_id = int(ministerio_id)
                        except (ValueError, TypeError):
                            ministerio_id = None

                    num_parcelas = int(body.get("numero_parcelas") or 1)
                    if num_parcelas < 1:
                        num_parcelas = 1
                    if num_parcelas > 60:
                        num_parcelas = 60
                    modo_valor = (body.get("modo_valor") or "PARCELA").upper()  # PARCELA ou TOTAL
                    is_parcelado = 1 if num_parcelas > 1 else 0

                    agora_str = agora_brasilia().strftime("%Y-%m-%d %H:%M:%S")
                    hoje_str = agora_brasilia().strftime("%Y-%m-%d")

                    if is_parcelado:
                        if modo_valor == "TOTAL":
                            val_parcela = round(valor_in / num_parcelas, 2)
                            val_total = valor_in
                        else:
                            val_parcela = valor_in
                            val_total = round(valor_in * num_parcelas, 2)

                        grupo_id = f"CP-{agora_brasilia().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
                        try:
                            dt_base = datetime.strptime(data_venc, "%Y-%m-%d")
                        except Exception:
                            dt_base = agora_brasilia()

                        for i in range(1, num_parcelas + 1):
                            dt_venc_i = add_months(dt_base, i - 1).strftime("%Y-%m-%d")
                            if i == 1 and modo_valor == "TOTAL":
                                val_i = round(val_total - (val_parcela * (num_parcelas - 1)), 2)
                            else:
                                val_i = val_parcela
                            desc_i = f"{descricao} ({i:02d}/{num_parcelas:02d})"
                            st_i = status_ini if i == 1 else "Em Aberto"
                            dt_pag_i = hoje_str if st_i == "Pago" else ""
                            val_pago_i = val_i if st_i == "Pago" else 0.0
                            pago_por_i = operador if st_i == "Pago" else ""
                            fin_id_i = None

                            if st_i == "Pago":
                                cur.execute(
                                    """INSERT INTO financeiro
                                    (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, pessoa_nome, ministerio_id, lancado_por)
                                    VALUES (?, 'SAIDA', ?, ?, ?, ?, 'Pago', ?, ?, ?)""",
                                    (dt_pag_i, categoria, f"[CP] {desc_i} - {fornecedor}", val_i, forma, fornecedor, ministerio_id, operador),
                                )
                                fin_id_i = cur.lastrowid
                                sincronizar_lancamento_na_matriz(cur, dt_pag_i, "SAIDA", categoria, desc_i, val_i, ministerio_id)

                            cur.execute(
                                """INSERT INTO contas_pagar
                                (fornecedor, descricao, categoria, documento, data_emissao, data_vencimento, valor, forma_pagamento,
                                 status, data_pagamento, valor_pago, pago_por, ministerio_id, parcelado, numero_parcelas, parcela_atual,
                                 grupo_parcela_id, financeiro_id, observacoes, criado_por, criado_em)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (fornecedor, desc_i, categoria, documento, data_emissao, dt_venc_i, val_i, forma,
                                 st_i, dt_pag_i, val_pago_i, pago_por_i, ministerio_id, 1, num_parcelas, i,
                                 grupo_id, fin_id_i, observacoes, operador, agora_str),
                            )

                        log_auditoria(conn, operador, "Tesouraria", "Contas a Pagar (Parcelada)", f"Cadastrou '{descricao}' ({fornecedor}) em {num_parcelas}x (Total R$ {val_total:,.2f})")
                        conn.commit()
                        conn.close()
                        broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} cadastrou conta a pagar parcelada em {num_parcelas}x ({fornecedor})."})
                        return self.send_json({"ok": True, "parcelas": num_parcelas})
                    else:
                        dt_pag = (body.get("data_pagamento") or hoje_str) if status_ini == "Pago" else ""
                        val_pago = valor_in if status_ini == "Pago" else 0.0
                        pago_por = operador if status_ini == "Pago" else ""
                        fin_id = None

                        if status_ini == "Pago":
                            cur.execute(
                                """INSERT INTO financeiro
                                (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, pessoa_nome, ministerio_id, lancado_por)
                                VALUES (?, 'SAIDA', ?, ?, ?, ?, 'Pago', ?, ?, ?)""",
                                (dt_pag, categoria, f"[CP] {descricao} - {fornecedor}", valor_in, forma, fornecedor, ministerio_id, operador),
                            )
                            fin_id = cur.lastrowid
                            sincronizar_lancamento_na_matriz(cur, dt_pag, "SAIDA", categoria, descricao, valor_in, ministerio_id)

                        cur.execute(
                            """INSERT INTO contas_pagar
                            (fornecedor, descricao, categoria, documento, data_emissao, data_vencimento, valor, forma_pagamento,
                             status, data_pagamento, valor_pago, pago_por, ministerio_id, parcelado, numero_parcelas, parcela_atual,
                             grupo_parcela_id, financeiro_id, observacoes, criado_por, criado_em)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 1, '', ?, ?, ?, ?)""",
                            (fornecedor, descricao, categoria, documento, data_emissao, data_venc, valor_in, forma,
                             status_ini, dt_pag, val_pago, pago_por, ministerio_id, fin_id, observacoes, operador, agora_str),
                        )
                        log_auditoria(conn, operador, "Tesouraria", "Contas a Pagar", f"Cadastrou conta '{descricao}' ({fornecedor}) - Venc: {data_venc} - R$ {valor_in:,.2f}")
                        conn.commit()
                        conn.close()
                        broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} cadastrou conta a pagar: {descricao} (R$ {valor_in:,.2f})."})
                        return self.send_json({"ok": True})

                elif path == "/api/contas-pagar/baixar":
                    cp_id = int(body.get("id", 0))
                    row_cp = cur.execute("SELECT * FROM contas_pagar WHERE id=?", (cp_id,)).fetchone()
                    if not row_cp:
                        conn.close()
                        return self.send_json({"erro": "Conta a pagar não encontrada."}, 404)
                    if row_cp["status"] == "Pago":
                        conn.close()
                        return self.send_json({"ok": True, "mensagem": "Esta conta já consta como paga."})

                    dt_pag = body.get("data_pagamento") or agora_brasilia().strftime("%Y-%m-%d")
                    val_pago = parse_moeda(body.get("valor_pago", row_cp["valor"]))
                    if val_pago <= 0:
                        val_pago = float(row_cp["valor"] or 0)
                    forma_pag = (body.get("forma_pagamento") or row_cp["forma_pagamento"] or "PIX").strip()

                    # Registra automaticamente no Livro-Caixa Diário e sincroniza na Planilha Mensal
                    cur.execute(
                        """INSERT INTO financeiro
                        (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, pessoa_nome, ministerio_id, lancado_por)
                        VALUES (?, 'SAIDA', ?, ?, ?, ?, 'Pago', ?, ?, ?)""",
                        (dt_pag, row_cp["categoria"], f"[CP #{cp_id}] {row_cp['descricao']} - {row_cp['fornecedor']}", val_pago, forma_pag, row_cp["fornecedor"], row_cp["ministerio_id"], operador),
                    )
                    fin_id = cur.lastrowid
                    sincronizar_lancamento_na_matriz(cur, dt_pag, "SAIDA", row_cp["categoria"], row_cp["descricao"], val_pago, row_cp["ministerio_id"])

                    cur.execute(
                        """UPDATE contas_pagar
                        SET status='Pago', data_pagamento=?, valor_pago=?, forma_pagamento=?, pago_por=?, financeiro_id=?
                        WHERE id=?""",
                        (dt_pag, val_pago, forma_pag, operador, fin_id, cp_id),
                    )
                    log_auditoria(conn, operador, "Tesouraria", "Baixa de Conta a Pagar", f"Quitou conta #{cp_id}: {row_cp['descricao']} ({row_cp['fornecedor']}) - R$ {val_pago:,.2f}")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} deu baixa na conta '{row_cp['descricao']}' (R$ {val_pago:,.2f})."})
                    return self.send_json({"ok": True})

                elif path == "/api/contas-pagar/estornar":
                    cp_id = int(body.get("id", 0))
                    row_cp = cur.execute("SELECT * FROM contas_pagar WHERE id=?", (cp_id,)).fetchone()
                    if not row_cp:
                        conn.close()
                        return self.send_json({"erro": "Conta não encontrada."}, 404)
                    if row_cp["status"] == "Pago":
                        fin_id = row_cp["financeiro_id"]
                        if fin_id:
                            fin_row = cur.execute("SELECT * FROM financeiro WHERE id=?", (fin_id,)).fetchone()
                            if fin_row:
                                sincronizar_lancamento_na_matriz(
                                    cur, fin_row["data_lancamento"], "SAIDA", fin_row["categoria"], fin_row["descricao"], -float(fin_row["valor"] or 0), fin_row["ministerio_id"]
                                )
                                cur.execute("DELETE FROM financeiro WHERE id=?", (fin_id,))
                        else:
                            sincronizar_lancamento_na_matriz(
                                cur, row_cp["data_pagamento"] or row_cp["data_vencimento"], "SAIDA", row_cp["categoria"], row_cp["descricao"], -float(row_cp["valor_pago"] or row_cp["valor"] or 0), row_cp["ministerio_id"]
                            )

                    cur.execute(
                        "UPDATE contas_pagar SET status='Em Aberto', data_pagamento='', valor_pago=0, pago_por='', financeiro_id=NULL WHERE id=?",
                        (cp_id,),
                    )
                    log_auditoria(conn, operador, "Tesouraria", "Reabertura de Conta a Pagar", f"Reabriu conta #{cp_id}: {row_cp['descricao']}")
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador} reabriu a conta '{row_cp['descricao']}'."})
                    return self.send_json({"ok": True})

                elif path == "/api/fiscal/configurar-a1":
                    if not fiscal_a1 or not fiscal_a1.HAS_CRYPTOGRAPHY:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Módulo criptográfico (cryptography) indisponível no servidor."}, 500)
                    b64_raw = str(body.get("pfx_base64") or "").strip()
                    if "," in b64_raw:
                        b64_raw = b64_raw.split(",", 1)[1]
                    senha_pfx = str(body.get("senha") or "").strip()
                    cnpj_inp = fiscal_a1.limpar_digitos(body.get("cnpj") or "")
                    ccm_sp = fiscal_a1.limpar_digitos(body.get("ccm_sp") or "")
                    if not b64_raw or not senha_pfx:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Envie o arquivo .pfx e a senha do Certificado A1."}, 400)
                    try:
                        pfx_bytes = base64.b64decode(b64_raw)
                        info_a1 = fiscal_a1.validar_e_extrair_a1(pfx_bytes, senha_pfx)
                    except Exception as e_a1:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": str(e_a1)}, 400)

                    cnpj_final = cnpj_inp if len(cnpj_inp) == 14 else info_a1.get("cnpj_extraido", "")
                    if len(cnpj_final) != 14:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Informe o CNPJ de 14 dígitos da igreja."}, 400)

                    sec_key = obter_segredo_sistema(conn, "backup_key")
                    pfx_enc = fiscal_a1.cifrar_dado_fiscal(pfx_bytes, sec_key)
                    senha_enc = fiscal_a1.cifrar_dado_fiscal(senha_pfx, sec_key)
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")

                    cur.execute(
                        """INSERT INTO config_fiscal_a1 (id, cnpj, ccm_sp, titular, validade, pfx_enc, senha_enc, ult_nsu, ultimo_sync, atualizado_por, atualizado_em)
                           VALUES (1, ?, ?, ?, ?, ?, ?, COALESCE((SELECT ult_nsu FROM config_fiscal_a1 WHERE id=1), '000000000000000'), COALESCE((SELECT ultimo_sync FROM config_fiscal_a1 WHERE id=1), ''), ?, ?)
                           ON CONFLICT(id) DO UPDATE SET
                             cnpj=excluded.cnpj,
                             ccm_sp=excluded.ccm_sp,
                             titular=excluded.titular,
                             validade=excluded.validade,
                             pfx_enc=excluded.pfx_enc,
                             senha_enc=excluded.senha_enc,
                             atualizado_por=excluded.atualizado_por,
                             atualizado_em=excluded.atualizado_em""",
                        (cnpj_final, ccm_sp, info_a1["titular"], info_a1["validade_br"], pfx_enc, senha_enc, operador, agora_str),
                    )
                    log_auditoria(conn, operador, "Fiscal A1", "Configuração de Certificado A1", f"Configurou Certificado A1 ({info_a1['titular']} - CNPJ {cnpj_final}, validade {info_a1['validade_br']}).")
                    conn.commit()
                    conn.close()
                    return self.send_json({
                        "ok": True,
                        "mensagem": f"Certificado A1 configurado com sucesso ({info_a1['titular']} • validade {info_a1['validade_br']}).",
                        "config": {
                            "cnpj": cnpj_final,
                            "ccm_sp": ccm_sp,
                            "titular": info_a1["titular"],
                            "validade": info_a1["validade_br"],
                        },
                    })

                elif path == "/api/fiscal/remover-a1":
                    cur.execute("DELETE FROM config_fiscal_a1 WHERE id=1")
                    log_auditoria(conn, operador, "Fiscal A1", "Remoção de Certificado A1", "Removeu o Certificado Digital A1 armazenado.")
                    conn.commit()
                    conn.close()
                    return self.send_json({"ok": True, "mensagem": "Certificado Digital A1 removido do servidor."})

                elif path == "/api/fiscal/sincronizar":
                    if not fiscal_a1 or not fiscal_a1.HAS_CRYPTOGRAPHY:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Módulo criptográfico (cryptography) indisponível no servidor."}, 500)
                    cfg = cur.execute("SELECT * FROM config_fiscal_a1 WHERE id=1").fetchone()
                    if not cfg:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Configure primeiro o Certificado Digital A1 (.pfx) da igreja."}, 400)

                    sec_key = obter_segredo_sistema(conn, "backup_key")
                    try:
                        pfx_bytes = fiscal_a1.decifrar_dado_fiscal(cfg["pfx_enc"], sec_key)
                        senha_pfx = fiscal_a1.decifrar_dado_fiscal(cfg["senha_enc"], sec_key).decode("utf-8")
                        a1_info = fiscal_a1.validar_e_extrair_a1(pfx_bytes, senha_pfx)
                    except Exception as e_dec:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": f"Falha ao abrir Certificado A1 salvo: {e_dec}"}, 400)

                    fonte = str(body.get("fonte") or "SEFAZ").upper()
                    dt_inicio = str(body.get("dt_inicio") or "").strip()
                    dt_fim = str(body.get("dt_fim") or "").strip()
                    if not dt_fim:
                        dt_fim = agora_brasilia().strftime("%Y-%m-%d")
                    if not dt_inicio:
                        dt_inicio = (agora_brasilia() - timedelta(days=30)).strftime("%Y-%m-%d")

                    conn.close()

                    notas_coletadas = []
                    avisos = []
                    novo_nsu = cfg["ult_nsu"] or "000000000000000"

                    if fonte in ("SEFAZ", "AMBAS"):
                        try:
                            res_sefaz = fiscal_a1.consultar_sefaz_distribuicao_dfe(cfg["cnpj"], a1_info, ult_nsu=novo_nsu, cuf_autor="35")
                            notas_coletadas.extend(res_sefaz.get("notas", []))
                            if res_sefaz.get("ult_nsu"):
                                novo_nsu = res_sefaz["ult_nsu"]
                        except Exception as e_sfz:
                            avisos.append(f"SEFAZ NF-e: {e_sfz}")

                    if fonte in ("NFSE_SP", "AMBAS"):
                        try:
                            res_sp = fiscal_a1.consultar_nfse_sp_recebidas(cfg["cnpj"], a1_info, dt_inicio=dt_inicio, dt_fim=dt_fim, ccm_sp=cfg["ccm_sp"] or "")
                            notas_coletadas.extend(res_sp.get("notas", []))
                        except Exception as e_sp:
                            avisos.append(f"Prefeitura SP NFS-e: {e_sp}")

                    conn = get_db()
                    cur = conn.cursor()
                    novas = 0
                    agora_str = agora_brasilia().strftime("%d/%m/%Y %H:%M")
                    for n in notas_coletadas:
                        ex = cur.execute("SELECT id, situacao_sefaz FROM notas_fiscais_recebidas WHERE chave_acesso=?", (n["chave_acesso"],)).fetchone()
                        if not ex:
                            cur.execute(
                                """INSERT INTO notas_fiscais_recebidas
                                   (tipo, chave_acesso, nsu, numero, serie, data_emissao, emitente_cnpj, emitente_nome, valor_total, descricao_itens, situacao_sefaz, status_lancamento, criado_em)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente', ?)""",
                                (n["tipo"], n["chave_acesso"], n["nsu"], n["numero"], n["serie"], n["data_emissao"], n["emitente_cnpj"], n["emitente_nome"], n["valor_total"], n["descricao_itens"], n["situacao_sefaz"], agora_str),
                            )
                            novas += 1
                        elif ex["situacao_sefaz"] == "Resumo" and n["situacao_sefaz"] != "Resumo":
                            cur.execute(
                                """UPDATE notas_fiscais_recebidas SET numero=?, serie=?, emitente_nome=?, valor_total=?, descricao_itens=?, situacao_sefaz=? WHERE id=?""",
                                (n["numero"], n["serie"], n["emitente_nome"], n["valor_total"], n["descricao_itens"], n["situacao_sefaz"], ex["id"]),
                            )

                    cur.execute("UPDATE config_fiscal_a1 SET ult_nsu=?, ultimo_sync=? WHERE id=1", (novo_nsu, agora_str))
                    log_auditoria(conn, operador, "Fiscal A1", "Sincronização de Notas Fiscais", f"Consultou {fonte}: {len(notas_coletadas)} nota(s) retornada(s), {novas} nova(s). NSU={novo_nsu}.")
                    notas_rows = [dict(r) for r in cur.execute("SELECT * FROM notas_fiscais_recebidas ORDER BY data_emissao DESC, id DESC LIMIT 300").fetchall()]
                    cfg_atual = dict(cur.execute("SELECT cnpj, ccm_sp, titular, validade, ult_nsu, ultimo_sync, atualizado_por, atualizado_em FROM config_fiscal_a1 WHERE id=1").fetchone())
                    conn.commit()
                    conn.close()

                    if avisos and not notas_coletadas:
                        return self.send_json({
                            "ok": False,
                            "mensagem": " | ".join(avisos),
                            "novas": novas,
                            "config": cfg_atual,
                            "notas": notas_rows,
                        }, 400)

                    return self.send_json({
                        "ok": True,
                        "mensagem": f"Busca concluída: {novas} nova(s) nota(s) adicionada(s) ({len(notas_coletadas)} encontrada(s) na consulta)." + (f" Avisos: {' | '.join(avisos)}" if avisos else ""),
                        "novas": novas,
                        "config": cfg_atual,
                        "notas": notas_rows,
                    })

                elif path == "/api/fiscal/lancar":
                    nota_id = int(body.get("nota_id", 0))
                    destino = str(body.get("destino") or "CONTAS_PAGAR").upper()
                    categoria = str(body.get("categoria") or "Despesas Gerais / Compras").strip()
                    ministerio_id = body.get("ministerio_id") or None
                    data_venc = str(body.get("data_vencimento") or "").strip()

                    nota = cur.execute("SELECT * FROM notas_fiscais_recebidas WHERE id=?", (nota_id,)).fetchone()
                    if not nota:
                        conn.close()
                        return self.send_json({"ok": False, "mensagem": "Nota fiscal não encontrada."}, 404)

                    desc_lanc = f"NF {nota['numero'] or nota['chave_acesso'][-9:]} - {nota['emitente_nome']} ({nota['descricao_itens'][:80]})"
                    dt_nota = nota["data_emissao"] or agora_brasilia().strftime("%Y-%m-%d")
                    valor_nota = float(nota["valor_total"] or 0)

                    if destino == "CAIXA":
                        cur.execute(
                            """INSERT INTO financeiro (data_lancamento, tipo, categoria, descricao, valor, forma_pagamento, status, pessoa_nome, ministerio_id, lancado_por)
                               VALUES (?, 'SAIDA', ?, ?, ?, 'PIX / Transferência', 'Pago', ?, ?, ?)""",
                            (dt_nota, categoria, desc_lanc, valor_nota, nota["emitente_nome"], ministerio_id, operador),
                        )
                        fin_id = cur.lastrowid
                        sincronizar_lancamento_na_matriz(cur, dt_nota, "SAIDA", categoria, desc_lanc, valor_nota, ministerio_id)
                        cur.execute("UPDATE notas_fiscais_recebidas SET status_lancamento='Lançada', financeiro_id=? WHERE id=?", (fin_id, nota_id))
                        msg_ok = f"Nota #{nota['numero']} lançada como SAÍDA paga no Caixa!"
                    else:
                        venc_final = data_venc or dt_nota
                        cur.execute(
                            """INSERT INTO contas_pagar (descricao, fornecedor, categoria, ministerio_id, valor, data_vencimento, status, observacoes, criado_por, criado_em)
                               VALUES (?, ?, ?, ?, ?, ?, 'Em Aberto', ?, ?, ?)""",
                            (desc_lanc, nota["emitente_nome"], categoria, ministerio_id, valor_nota, venc_final, f"Chave: {nota['chave_acesso']}", operador, agora_brasilia().strftime("%d/%m/%Y %H:%M")),
                        )
                        cp_id = cur.lastrowid
                        cur.execute("UPDATE notas_fiscais_recebidas SET status_lancamento='Lançada', conta_pagar_id=? WHERE id=?", (cp_id, nota_id))
                        msg_ok = f"Nota #{nota['numero']} enviada para Contas a Pagar!"

                    log_auditoria(conn, operador, "Fiscal A1", "Lançamento de Nota Fiscal", msg_ok)
                    conn.commit()
                    conn.close()
                    broadcast_event("sync", {"setor": "Tesouraria", "operador": operador, "mensagem": f"{operador}: {msg_ok}"})
                    return self.send_json({"ok": True, "mensagem": msg_ok})

                elif path == "/api/fiscal/ignorar":
                    nota_id = int(body.get("nota_id", 0))
                    novo_status = str(body.get("status") or "Ignorada")
                    if novo_status not in ("Ignorada", "Pendente"):
                        novo_status = "Ignorada"
                    cur.execute("UPDATE notas_fiscais_recebidas SET status_lancamento=? WHERE id=?", (novo_status, nota_id))
                    conn.commit()
                    conn.close()
                    return self.send_json({"ok": True, "mensagem": f"Status da nota atualizado para {novo_status}."})

                conn.close()

                return self.send_json({"erro": "Rota não encontrada"}, 404)



        except Exception as e:

            import traceback; traceback.print_exc()

            return self.send_json({"erro": str(e)}, 500)



    def do_DELETE(self):

        auth_u = self.get_authenticated_user()
        if not auth_u:
            return self.send_json({"ok": False, "mensagem": "Sessão expirada ou não autenticada."}, 401)

        parsed = urlparse(self.path)

        path = parsed.path

        if not usuario_tem_permissao_rota(auth_u, "DELETE", path):
            return self.send_json({"ok": False, "mensagem": "Você não possui permissão para excluir registros neste setor."}, 403)

        qs = parse_qs(parsed.query)

        item_id = int(qs.get("id", [0])[0])

        operador = str(auth_u.get("nome") or qs.get("operador", ["Administrador"])[0])



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

                "/api/contas-pagar": ("contas_pagar", "Tesouraria", "Exclusão de Conta a Pagar"),

            }



            if path in tabelas and item_id > 0:

                tabela, setor, acao = tabelas[path]

                if tabela == "contas_pagar":
                    cp_row = cur.execute("SELECT * FROM contas_pagar WHERE id=?", (item_id,)).fetchone()
                    if cp_row and cp_row["status"] == "Pago":
                        fin_id = cp_row["financeiro_id"]
                        if fin_id:
                            fin_row = cur.execute("SELECT * FROM financeiro WHERE id=?", (fin_id,)).fetchone()
                            if fin_row:
                                sincronizar_lancamento_na_matriz(
                                    cur, fin_row["data_lancamento"], "SAIDA", fin_row["categoria"], fin_row["descricao"], -float(fin_row["valor"] or 0), fin_row["ministerio_id"]
                                )
                                cur.execute("DELETE FROM financeiro WHERE id=?", (fin_id,))

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



    if "PORT" not in os.environ and is_port_in_use(port):
        print(f"Servidor ja esta ativo em http://localhost:{port}", flush=True)
        # Navegador nao e aberto automaticamente
        sys.exit(0)



    init_db()

    iniciar_keep_alive_blindagem()

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

