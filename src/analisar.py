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
    queries=(ROOT/'sql/analise.sql').read_text(encoding='utf-8').split(';')
    results=[]
    for name,query in zip(['por_area','por_ano','top_clientes'],[q for q in queries if q.strip()]):
        cur=db.execute(query); values=cur.fetchall();results.append(values)
        with (out/f'{name}.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f);writer.writerow([c[0] for c in cur.description]);writer.writerows(values)
    areas, years, clients=results
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
    lines+=['','![Vendas por área](vendas_por_area.svg)','','![Comparação anual](vendas_por_ano.svg)','','![Clientes](top_clientes.svg)','',
            '## Interpretação e ações propostas','',
            'A composição das vendas e o ticket ajudam a distinguir volume de oportunidades de valor comercial. A concentração orienta quais contas merecem planos de relacionamento. Investigar necessidades complementares de Segurança nos compradores de IA é uma hipótese de expansão, não uma venda prevista.','',
            'Comparações usam janeiro a agosto em ambos os anos. Variação temporal desta simulação é consequência do gerador aleatório e não evidência sobre o mercado. Não há perdas, leads, contratos recorrentes ou pipeline aberto: não calculamos conversão, churn, MRR, ARR ou forecast.','',
            'As recomendações não foram implementadas e não há impacto de negócio medido.']
    (out/'resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Concluído: {len(rows)} registros; R$ {br(total)} em vendas fictícias.')
    db.close()

if __name__=='__main__':
    main()
