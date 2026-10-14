SELECT
    cliente_id,
    COUNT(*) AS quantidade,
    ROUND(SUM(valor_centavos) / 100.0, 2) AS receita_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY cliente_id
ORDER BY receita_reais DESC
LIMIT 5;
