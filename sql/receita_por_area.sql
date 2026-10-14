-- Vendas, quantidade e ticket médio por área da solução.
-- Parcerias não entram no denominador dos indicadores comerciais.
SELECT area,
       COUNT(*) AS oportunidades,
       ROUND(SUM(valor_centavos) / 100.0, 2) AS vendas_reais,
       ROUND(AVG(valor_centavos) / 100.0, 2) AS ticket_medio_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY area
ORDER BY vendas_reais DESC;
