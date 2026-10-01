import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from analisar import preparar

class Qualidade(unittest.TestCase):
    def row(self, **changes):
        row=dict(oportunidade_id='OP-1',cliente_id='C-1',fechamento='2026-01-10',solucao='COPIOT',origem='CS',valor_venda='10.25')
        return dict(row,**changes)

    def test_classificacao_e_centavos(self):
        result=preparar([self.row(),self.row(oportunidade_id='OP-2',solucao='PAL',valor_venda='0')])
        self.assertEqual(result[0][4],'IA/Copilot')
        self.assertEqual(result[0][-1],1025)
        self.assertEqual(result[1][4],'Parcerias de TI')

    def test_duplicata_nao_infla_total(self):
        with self.assertRaises(ValueError):preparar([self.row(),self.row()])

    def test_dados_invalidos_interrompem(self):
        for change in [dict(valor_venda='-1'),dict(valor_venda='1.234'),dict(solucao='Outra'),dict(fechamento='2026-02-30'),dict(cliente_id='')]:
            with self.subTest(change=change),self.assertRaises(ValueError):preparar([self.row(**change)])

if __name__=='__main__':unittest.main()
