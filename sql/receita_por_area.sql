SELECT
    area,
    COUNT(*) AS quantidade,
    ROUND(SUM(valor_centavos) / 100.0, 2) AS receita_reais,
    ROUND(AVG(valor_centavos) / 100.0, 2) AS ticket_medio_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY area
ORDER BY receita_reais DESC;