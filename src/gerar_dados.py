"""Gera dados inteiramente fictícios. Não lê arquivos da empresa."""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    rng = random.Random(20260929)
    rows = []
    # Quantidades escolhidas para o exercício, sem correspondência com o CRM.
    ofertas = [('COPILOT', 58), ('DATA SECURITY', 24),
               ('THREAT PROTECTION', 16), ('CPOR', 12), ('PAL', 10)]
    for oferta, quantidade in ofertas:
        for _ in range(quantidade):
            ano = rng.choice([2025, 2026])
            mes = rng.randint(1, 8)
            parceria = oferta in ('CPOR', 'PAL')
            valor = 0 if parceria else rng.choice(
                [24000, 48000, 96000, 144000] if oferta == 'COPILOT'
                else [18000, 30000, 42000, 60000])
            # Clientes sintéticos; distribuição desigual permite estudar concentração.
            cliente = rng.choices(range(1, 31), weights=[8]*5+[1]*25)[0]
            rows.append({
                'oportunidade_id': f'OP-{len(rows)+1:04}',
                'cliente_id': f'CLIENTE-{cliente:03}',
                'fechamento': f'{ano}-{mes:02}-{rng.randint(1,28):02}',
                'solucao': oferta,
                'origem': rng.choice(['CS', 'CS', 'CS', 'Vendas', 'Parceiro']),
                'valor_venda': f'{valor:.2f}',
            })
    # Erro proposital para demonstrar tratamento rastreável.
    rows[0]['solucao'] = 'COPIOT'
    path = ROOT / 'data/oportunidades_sinteticas.csv'
    path.parent.mkdir(exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} registros fictícios gerados.')

if __name__ == '__main__':
    main()
