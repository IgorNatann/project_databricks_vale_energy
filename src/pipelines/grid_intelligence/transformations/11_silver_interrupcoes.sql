-- As expectations abaixo só registram violações no event log, sem descartar linhas.
-- O filtro de duração é regra regulatória (RN-01), não qualidade, e continua no WHERE.
CREATE OR REFRESH STREAMING TABLE ${catalogo}.${schema_silver}.interrupcoes_validas (
  CONSTRAINT evento_identificado EXPECT (coalesce(id_interrupcao IS NOT NULL AND id_conjunto IS NOT NULL, false)),
  CONSTRAINT periodo_coerente EXPECT (coalesce(fim >= inicio, false)),
  CONSTRAINT ucs_afetadas_positivas EXPECT (coalesce(qtd_ucs_afetadas > 0, false))
)
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT
  *,
  to_date(inicio) AS data_evento,
  date_trunc('MONTH', inicio) AS mes_apuracao,
  duracao_minutos / 60.0 AS duracao_horas,
  duracao_minutos / 60.0 * qtd_ucs_afetadas AS uc_horas_interrompidas,
  causa = 'climatica' AS causa_climatica
FROM STREAM(${catalogo}.${schema_bronze}.interrupcoes)
-- Abaixo do limiar, o religador pode restabelecer a rede em segundos.
-- Essas ocorrências permanecem na bronze, fora dos indicadores de continuidade.
WHERE duracao_minutos >= ${duracao_minima_interrupcao};
