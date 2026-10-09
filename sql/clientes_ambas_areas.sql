SELECT
    cliente_id,
    SUM(CASE WHEN area = 'IA/Copilot'
        THEN 1 ELSE 0 END) AS oportunidades_copilot,
    SUM(CASE WHEN area = 'Segurança'
        THEN 1 ELSE 0 END) AS oportunidades_seguranca
FROM oportunidades
WHERE area IN ('IA/Copilot', 'Segurança')
GROUP BY cliente_id
HAVING COUNT(DISTINCT area) = 2
ORDER BY cliente_id;