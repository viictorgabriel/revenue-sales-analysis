-- Parcerias não entram no denominador dos indicadores comerciais.
SELECT area,
       COUNT(*) AS oportunidades,
       ROUND(SUM(valor_centavos) / 100.0, 2) AS vendas_reais,
       ROUND(AVG(valor_centavos) / 100.0, 2) AS ticket_medio_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY area
ORDER BY vendas_reais DESC;

-- Comparação de janeiro a agosto em ambos os anos da simulação.
SELECT SUBSTR(fechamento, 1, 4) AS ano,
       COUNT(*) AS oportunidades,
       ROUND(SUM(valor_centavos) / 100.0, 2) AS vendas_reais,
       ROUND(AVG(valor_centavos) / 100.0, 2) AS ticket_medio_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
  AND SUBSTR(fechamento, 6, 2) BETWEEN '01' AND '08'
GROUP BY ano ORDER BY ano;

-- Concentração: cinco clientes com maior valor vendido.
SELECT cliente_id, COUNT(*) AS oportunidades,
       ROUND(SUM(valor_centavos) / 100.0, 2) AS vendas_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY cliente_id ORDER BY vendas_reais DESC, cliente_id LIMIT 5;
