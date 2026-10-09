WITH por_cliente AS (
    SELECT
        cliente_id,
        CASE
            WHEN COUNT(DISTINCT area) = 2 THEN 'Ambas'
            WHEN MAX(area) = 'IA/Copilot' THEN 'Somente Copilot'
            ELSE 'Somente Segurança'
        END AS perfil
    FROM oportunidades
    WHERE area IN ('IA/Copilot', 'Segurança')
    GROUP BY cliente_id
)
SELECT
    perfil,
    COUNT(*) AS quantidade_clientes
FROM por_cliente
GROUP BY perfil
ORDER BY quantidade_clientes DESC;