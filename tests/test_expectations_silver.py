"""Contrato de qualidade da silver, verificado sem workspace e executado no CI."""

import re

from conftest import consulta_transformacao, expectations_transformacao, instrucao_transformacao


def test_cadastro_descarta_chaves_invalidas_por_expectation():
    """O descarte de chaves deve ser medido no event log, não feito por WHERE."""
    assert expectations_transformacao("10_silver_cadastro.sql") == [
        ("chaves_preenchidas", "coalesce(id_uc IS NOT NULL AND id_conjunto IS NOT NULL, false)", True)
    ]
    assert "WHERE" not in consulta_transformacao("10_silver_cadastro.sql").upper()


def test_cadastro_mantem_uma_linha_por_uc():
    """Reenvios na bronze não podem duplicar a UC nem inflar o denominador de DEC e FEC."""
    instrucao = instrucao_transformacao("10_silver_cadastro.sql", 1)
    assert "MATERIALIZED VIEW ${catalogo}.${schema_silver}.unidades_consumidoras" in instrucao
    assert "FROM cadastro_validado" in instrucao
    assert re.search(r"QUALIFY\s+row_number\(\)\s+OVER\s*\(\s*PARTITION BY id_uc ORDER BY ingerido_em DESC", instrucao)


def test_consumo_mede_ucs_fora_do_cadastro_e_leituras_implausiveis():
    """As duas causas de descarte ficam separadas para que o event log diga qual ocorreu."""
    expectations = expectations_transformacao("12_silver_consumo.sql")
    assert [(nome, descarta) for nome, _, descarta in expectations] == [
        ("uc_cadastrada", True),
        ("leitura_plausivel", True),
    ]
    leitura = expectations[1][1]
    assert leitura.startswith("coalesce(") and leitura.endswith(", false)")
    for classe, limite in [("residencial", 100), ("comercial", 500), ("industrial", 10000), ("rural", 250),
                           ("poder_publico", 2000)]:
        assert f"WHEN '{classe}' THEN {limite}" in leitura
    assert "LEFT JOIN" in consulta_transformacao("12_silver_consumo.sql")


def test_consumo_deduplica_depois_da_validacao():
    """Uma leitura inválida mais recente não pode esconder a leitura válida anterior."""
    deduplicado = consulta_transformacao("12_silver_consumo.sql", 1)
    assert "FROM consumo_validado" in deduplicado
    assert "QUALIFY row_number() OVER (PARTITION BY id_uc, data ORDER BY ingerido_em DESC) = 1" in deduplicado


def test_interrupcoes_apenas_registram_violacoes():
    """Na silver de interrupções, as expectations medem sem alterar os indicadores."""
    expectations = expectations_transformacao("11_silver_interrupcoes.sql")
    assert [nome for nome, _, _ in expectations] == [
        "evento_identificado", "periodo_coerente", "ucs_afetadas_positivas"
    ]
    assert not any(descarta for _, _, descarta in expectations)
    assert "WHERE duracao_minutos >= ${duracao_minima_interrupcao}" in consulta_transformacao(
        "11_silver_interrupcoes.sql"
    )
