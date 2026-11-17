-- Cadastro corrente (SCD tipo 1): uma linha por UC, da ingestão válida mais recente.
-- A bronze acumula reenvios. Sem deduplicar, a UC repetida inflaria o total de UCs, que é o
-- denominador de DEC e FEC, e duplicaria os joins de consumo e chamados.
-- Com milhares de UCs, a materialized view basta. AUTO CDC fica para quando a origem enviar
-- exclusões ou o histórico do cadastro (SCD tipo 2) for exigido.
-- Ao migrar da streaming table anterior, faça um full refresh desta tabela.

-- A expectation mede no event log os registros descartados, em vez de um WHERE silencioso.
CREATE TEMPORARY VIEW cadastro_validado (
  CONSTRAINT chaves_preenchidas EXPECT (coalesce(id_uc IS NOT NULL AND id_conjunto IS NOT NULL, false))
    ON VIOLATION DROP ROW
)
AS SELECT
  * EXCEPT (classe_consumo, bairro),
  lower(trim(classe_consumo)) AS classe_consumo,
  coalesce(nullif(trim(bairro), ''), 'nao informado') AS bairro
FROM ${catalogo}.${schema_bronze}.unidades_consumidoras;

CREATE OR REFRESH MATERIALIZED VIEW ${catalogo}.${schema_silver}.unidades_consumidoras
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT *
FROM cadastro_validado
QUALIFY row_number() OVER (
  PARTITION BY id_uc ORDER BY ingerido_em DESC, ingerido_bronze_em DESC, arquivo_origem DESC
) = 1;
