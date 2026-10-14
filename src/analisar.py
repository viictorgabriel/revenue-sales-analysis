"""Pipeline local: valida CSV, classifica soluções, executa SQL e gera relatório."""
import csv
import datetime
import json
import sqlite3
from decimal import Decimal
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPA = {'COPILOT': 'IA/Copilot', 'COPIOT': 'IA/Copilot',
        'DATA SECURITY': 'Segurança', 'THREAT PROTECTION': 'Segurança',
        'CPOR': 'Parcerias de TI', 'PAL': 'Parcerias de TI'}

# Arquivo SQL, nome do CSV gerado, título e objetivo no relatório.
CONSULTAS = [
    ('receita_por_area.sql', 'por_area', 'Vendas por área', 'Comparar quantidade de oportunidades, vendas e ticket médio de Copilot e Segurança.'),
    ('vendas_por_ano.sql', 'por_ano', 'Vendas por ano', 'Comparar janeiro a agosto dos dois anos da simulação.'),
    ('top_clientes.sql', 'top_clientes', 'Principais clientes', 'Identificar os cinco clientes com maior valor vendido.'),
    ('comparativo_clientes.sql', 'comparativo_clientes', 'Comparativo por cliente', 'Classificar cada cliente por presença em Copilot, Segurança ou ambas.'),
    ('clientes_ambas_areas.sql', 'clientes_ambas_areas', 'Clientes nas duas áreas', 'Identificar clientes com oportunidades tanto em Copilot quanto em Segurança.'),
    ('perfil_clientes.sql', 'perfil_clientes', 'Perfis de clientes', 'Contar clientes com ambas as áreas, somente Copilot ou somente Segurança.'),
]

def br(value):
    return f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def preparar(rows):
    """Rejeita dados inválidos em vez de produzir totais incompletos."""
    result, ids = [], set()
    for row in rows:
        oid = row['oportunidade_id'].strip()
        if not oid or oid in ids:
            raise ValueError(f'Identificador ausente ou duplicado: {oid}')
        ids.add(oid)
        datetime.date.fromisoformat(row['fechamento'])
        if not row['cliente_id'].strip():
            raise ValueError(f'Cliente ausente em {oid}')
        solucao = row['solucao'].strip().upper()
        if solucao not in MAPA:
            raise ValueError(f'Solução não mapeada: {solucao}')
        value = Decimal(row['valor_venda'])
        if not value.is_finite() or value < 0 or value*100 != (value*100).to_integral_value():
            raise ValueError(f'Valor inválido em {oid}')
        result.append((oid, row['cliente_id'].strip(), row['fechamento'],
                       solucao, MAPA[solucao], row['origem'], int(value*100)))
    if not result:
        raise ValueError('Base vazia')
    return result

def grafico(path, title, pairs, currency=True):
    """SVG com rótulos diretos e escala comum; sem dependências externas."""
    height = 115 + 66*len(pairs)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img" aria-label="{escape(title)}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<g font-family="Arial,sans-serif" fill="#16324a">',
             f'<text x="24" y="34" font-size="22" font-weight="bold">{escape(title)}</text>',
             '<text x="24" y="59" font-size="13">Dados inteiramente fictícios • Valores nominais em reais</text>']
    maximum = max((v for _,v in pairs), default=1) or 1
    for i,(label,value) in enumerate(pairs):
        y=95+66*i
        parts.extend([f'<text x="24" y="{y}" font-size="15">{escape(label)}</text>',
                      f'<rect x="230" y="{y-17}" width="{470*value/maximum:.2f}" height="23" fill="#2764bb"/>',
                      f'<text x="870" y="{y}" text-anchor="end" font-size="15">R$ {br(value)}</text>'])
    parts.append('</g></svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')

def main():
    with (ROOT/'data/oportunidades_sinteticas.csv').open(encoding='utf-8',newline='') as f:
        raw=list(csv.DictReader(f))
    rows=preparar(raw)
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE oportunidades (id TEXT PRIMARY KEY, cliente_id TEXT, fechamento TEXT, solucao TEXT, area TEXT, origem TEXT, valor_centavos INTEGER)')
    db.executemany('INSERT INTO oportunidades VALUES (?,?,?,?,?,?,?)',rows)
    results=[]
    for sql_file,name,_,_ in CONSULTAS:
        # Cada arquivo em sql/ tem uma única consulta; é a mesma que o relatório linka.
        cur=db.execute((ROOT/'sql'/sql_file).read_text(encoding='utf-8')); values=cur.fetchall();results.append(values)
        with (out/f'{name}.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f);writer.writerow([c[0] for c in cur.description]);writer.writerows(values)
    areas, years, clients, comparison, both_ids, profiles=results
    # As consultas de apoio precisam concordar com o comparativo por cliente.
    assert sorted(r[0] for r in both_ids)==sorted(r[0] for r in comparison if r[6]=='Ambas')
    assert dict(profiles)=={p:sum(r[6]==p for r in comparison) for p in dict(profiles)}
    cents=sum(r[-1] for r in rows if r[4]!='Parcerias de TI')
    assert cents==db.execute("SELECT SUM(valor_centavos) FROM oportunidades WHERE area <> 'Parcerias de TI'").fetchone()[0]
    n=sum(1 for r in rows if r[4]!='Parcerias de TI')
    total=cents/100
    share=sum(r[2] for r in clients)/total*100 if total else 0
    grafico(out/'vendas_por_area.svg','Vendas por área da solução',[(r[0],r[2]) for r in areas])
    grafico(out/'vendas_por_ano.svg','Vendas de janeiro a agosto',[(r[0],r[2]) for r in years])
    grafico(out/'top_clientes.svg','Cinco maiores clientes fictícios',[(r[0],r[2]) for r in clients])
    audit={'registros':len(rows),'oportunidades_solucoes':n,'parcerias':len(rows)-n,
           'correcoes_copiot':sum(r[3]=='COPIOT' for r in rows),
           'vendas_centavos':cents,'origem':'Dados sintéticos, semente 20260929'}
    (out/'validacao.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Resultados da simulação','', '**Todos os resultados abaixo são fictícios. Não representam desempenho profissional ou empresarial real.**','',
           f'- Registros: {len(rows)}; oportunidades comerciais: {n}; parcerias: {len(rows)-n}.',
           f'- Vendas de soluções: R$ {br(total)}.',f'- Ticket médio: R$ {br(total/n)}.',
           f'- Participação dos cinco maiores clientes: {br(share)}%.','',
           '| Área | Oportunidades | Vendas (R$) | Ticket (R$) |','|---|---:|---:|---:|']
    lines.extend(f'| {a} | {q} | {br(v)} | {br(t)} |' for a,q,v,t in areas)
    both=[r for r in comparison if r[6]=='Ambas']
    both_total=sum(r[5] for r in both)
    lines+=['', '## Clientes com oportunidades em Copilot e Segurança', '',
            'Cruzamento por cliente_id em todo o período disponível. Cada cliente é contado uma vez no perfil. Não há exigência de ordem entre as contratações. PAL/CPOR não entram neste comparativo.', '',
            '| Perfil | Clientes | Participação nos clientes |', '|---|---:|---:|']
    for profile in ('Ambas','Somente Copilot','Somente Segurança'):
        count=sum(r[6]==profile for r in comparison)
        pct=count/len(comparison)*100 if comparison else 0
        lines.append(f'| {profile} | {count} | {br(pct)}% |')
    both_share=both_total/total*100 if total else 0
    lines+=['', f'Os {len(both)} clientes com ambas as frentes somam R$ {br(both_total)}, equivalentes a {br(both_share)}% das vendas de soluções.', '',
            '| Cliente | Oportunidades Copilot | Oportunidades Segurança | Vendas Copilot (R$) | Vendas Segurança (R$) | Total (R$) |',
            '|---|---:|---:|---:|---:|---:|']
    lines.extend(f'| {c} | {nc} | {ns} | {br(vc)} | {br(vs)} | {br(vt)} |' for c,nc,ns,vc,vs,vt,_ in both)
    lines+=['', '[Comparativo completo dos clientes](comparativo_clientes.csv)', '',
            'A presença conjunta descreve a carteira, mas não demonstra que uma venda causou outra. Clientes com uma única frente podem ser avaliados quanto a necessidades complementares em qualquer direção. A ausência de contratação não comprova demanda.']
    lines+=['','![Vendas por área](vendas_por_area.svg)','','![Comparação anual](vendas_por_ano.svg)','','![Clientes](top_clientes.svg)','',
            '## Interpretação e ações propostas','',
            'A composição das vendas e o ticket ajudam a distinguir volume de oportunidades de valor comercial. A concentração orienta quais contas merecem planos de relacionamento. Investigar necessidades complementares de Segurança ou Copilot é uma hipótese de expansão, sem ordem obrigatória entre as soluções e sem venda prevista.','',
            'Comparações usam janeiro a agosto em ambos os anos. Variação temporal desta simulação é consequência do gerador aleatório e não evidência sobre o mercado. Não há perdas, leads, contratos recorrentes ou pipeline aberto: não calculamos conversão, churn, MRR, ARR ou forecast.','',
            'As recomendações não foram implementadas e não há impacto de negócio medido.','',
            '## Consultas SQL','',
            'Cada consulta abaixo é executada pelo script em SQLite e gera o CSV indicado. Os totais são reconciliados com a soma independente em Python.','',
            '| Consulta | Objetivo | Resultado |','|---|---|---|']
    lines.extend(f'| [{title}](../sql/{sql_file}) | {goal} | [{name}.csv]({name}.csv) |' for sql_file,name,title,goal in CONSULTAS)
    lines+=['','### Conceitos praticados','',
            '- Filtragem com WHERE e IN.','- Agrupamento com GROUP BY.','- Agregações com COUNT, SUM e AVG.',
            '- Arredondamento com ROUND.','- Ordenação e seleção dos maiores valores com ORDER BY e LIMIT.',
            '- Contagem condicional com CASE.','- Filtragem de grupos com HAVING e COUNT DISTINCT.',
            '- Organização da consulta em etapas com WITH.']
    (out/'resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Concluído: {len(rows)} registros; R$ {br(total)} em vendas fictícias.')
    db.close()

if __name__=='__main__':
    main()
