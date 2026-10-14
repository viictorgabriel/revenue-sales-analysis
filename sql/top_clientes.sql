-- Concentração: cinco clientes com maior valor vendido.
-- Empates no valor são desfeitos pelo cliente_id para o resultado ser estável.
SELECT cliente_id,
       COUNT(*) AS oportunidades,
       ROUND(SUM(valor_centavos) / 100.0, 2) AS vendas_reais
FROM oportunidades
WHERE area <> 'Parcerias de TI'
GROUP BY cliente_id
ORDER BY vendas_reais DESC, cliente_id
LIMIT 5;
