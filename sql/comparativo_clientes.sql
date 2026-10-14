-- Presença nas duas frentes por cliente, em todo o período da base.
-- Não exige sequência entre contratações. PAL/CPOR ficam fora.
WITH por_cliente AS (
    SELECT cliente_id,
           SUM(CASE WHEN area = 'IA/Copilot' THEN 1 ELSE 0 END) AS oportunidades_copilot,
           SUM(CASE WHEN area = 'Segurança' THEN 1 ELSE 0 END) AS oportunidades_seguranca,
           SUM(CASE WHEN area = 'IA/Copilot' THEN valor_centavos ELSE 0 END) AS copilot_centavos,
           SUM(CASE WHEN area = 'Segurança' THEN valor_centavos ELSE 0 END) AS seguranca_centavos
    FROM oportunidades
    WHERE area IN ('IA/Copilot', 'Segurança')
    GROUP BY cliente_id
)
SELECT cliente_id, oportunidades_copilot, oportunidades_seguranca,
       ROUND(copilot_centavos / 100.0, 2) AS vendas_copilot_reais,
       ROUND(seguranca_centavos / 100.0, 2) AS vendas_seguranca_reais,
       ROUND((copilot_centavos + seguranca_centavos) / 100.0, 2) AS vendas_total_reais,
       CASE WHEN oportunidades_copilot > 0 AND oportunidades_seguranca > 0 THEN 'Ambas'
            WHEN oportunidades_copilot > 0 THEN 'Somente Copilot'
            ELSE 'Somente Segurança' END AS perfil
FROM por_cliente
ORDER BY vendas_total_reais DESC, cliente_id;
