# Integração contínua

O workflow [validacao.yml](../.github/workflows/validacao.yml) roda em PRs e na `main`:
instala as dependências a partir do `uv.lock`, executa o Ruff e roda o pytest sem workspace.
Ele usa somente permissão de leitura do repositório e não recebe credenciais do Databricks.

Os testes marcados `databricks` e `reexecucao` são ignorados nesse fluxo. Uma execução verde
confirma os testes locais, não o deploy, os dados nem a integração com o workspace. Para
validar a integração em desenvolvimento, siga o comando `pytest --databricks` no README e
execute `databricks bundle validate --strict -t dev --profile project_vale_energy` com o
perfil apropriado. A opção de reexecução tem custo e deve ser selecionada explicitamente.

Entre os testes locais, `test_expectations_silver.py` fixa o contrato de qualidade da silver:
quais expectations existem, quais descartam linhas e a deduplicação do cadastro e do consumo.
Ele verifica a declaração do SQL, não o comportamento no workspace.

A próxima etapa é um job de CD autenticado por OIDC, sem segredo de longa duração no
GitHub, que valide o bundle, faça o deploy em dev e rode `pytest --databricks` depois do
merge. O plano está em [evolução](evolucao.md).
