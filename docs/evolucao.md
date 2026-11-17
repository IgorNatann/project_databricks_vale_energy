# Limitações conhecidas e evolução planejada

Este é um projeto de laboratório. As lacunas abaixo foram mapeadas de propósito: cada uma
tem o motivo de ter ficado fora agora e o próximo passo planejado. O objetivo é deixar claro
o que o projeto **demonstra** e o que ainda **não demonstra**.

## Já tratado

| Ponto | O que mudou |
|---|---|
| Cadastro duplicável | A silver de cadastro mantém uma linha por UC (SCD tipo 1). Reenvios não inflam o denominador de DEC e FEC. |
| Descartes silenciosos | Os critérios de qualidade da silver são expectations do Lakeflow, medidas no event log ([regras](regras-de-negocio.md#qualidade-medida-no-pipeline)). |

## Próximas evoluções

| # | Lacuna atual | Por que ficou para depois | Evolução planejada |
|---|---|---|---|
| 1 | **Produção em um único workspace.** Dev e prod separam os dados por catálogo, mas compartilham workspace e warehouse, e o deploy de prod usa a identidade de quem o executa. | O isolamento por catálogo já demonstra o mesmo SQL em dois ambientes. Um segundo workspace e um service principal exigem uma conta que o laboratório não tem. | Workspace de prod próprio, `run_as` com service principal, permissões por grupo e deploy feito só pelo pipeline de CD. |
| 2 | **CI sem os testes de regra.** O CI roda o lint e os testes locais, incluindo o contrato de expectations. Os testes que executam o SQL das transformações precisam de um SQL warehouse. | Não colocar credenciais do Databricks no GitHub foi uma decisão consciente para um repositório público. | Executar parte das regras em Spark local no CI e criar um job de CD com OIDC (federação de identidade do GitHub), que rode `bundle validate`, `deploy -t dev` e `pytest --databricks` depois do merge. |
| 3 | **Operação manual.** O job roda sob demanda, sem agendamento nem alertas. | Os dados são sintéticos e estáticos: um agendamento só geraria custo. | Gatilho por chegada de arquivo no volume `raw.landing`, notificação de falha e alertas SQL sobre as violações de expectations. |
| 4 | **Limites de consumo fixos no SQL.** Os limites por classe estão no `CASE` da silver, enquanto os outros limiares são variáveis do bundle. | São critérios demonstrativos aprovados para os dados sintéticos e estão documentados em [regras](regras-de-negocio.md#limites-demonstrativos-de-consumo). | Levar os limites para uma tabela de referência versionada, consultada pelo join, para mudar o critério sem novo deploy. |
| 5 | **Cadastro sem histórico.** DEC e FEC usam o cadastro atual para todos os meses. | O dataset não tem a evolução do cadastro nem os limites regulatórios de cada conjunto. | `AUTO CDC` com SCD tipo 2 no cadastro e base de UCs por mês de apuração. Com os limites da ANEEL, a gold passa a medir conformidade. |
| 6 | **Testes de SQL acoplados ao texto.** Os testes extraem a consulta dividindo o arquivo por `;`. | Isso permite testar o SQL real, sem uma cópia, com pouco código. | Avaliar `pytest` com Spark Connect ou um parser SQL para extrair as instruções com segurança. |
| 7 | **Privacidade com uma identidade.** A máscara foi verificada para o membro do grupo `atendimento`. | O workspace de laboratório tem um único usuário. | Testar com um segundo perfil (`--perfil-nao-atendimento` já existe nos testes) e revisar as permissões do volume. |

O projeto prioriza regras corretas, rastreáveis e testadas sobre infraestrutura que dependa
de uma conta corporativa. Os itens 1 a 3 são o próximo ciclo.
