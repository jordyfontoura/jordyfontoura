# Uso registrado dos agentes

O painel do perfil é um snapshot parcial dos contadores disponíveis no cache de uso do T3 Code.
Não representa todo o histórico de uso nem gasto financeiro. Os valores incluem contexto
reutilizado em cache e, por isso, podem ser muito maiores que o volume de texto produzido.

## O que é contado

- Entrada sem cache + leitura de cache + criação de cache + saída.
- Raciocínio já incluído na saída não é somado novamente.
- A primeira ocorrência de cada chave de requisição é mantida; cópias são descartadas.
- Registros sem chave são mantidos individualmente. A inspeção inicial não encontrou cópias
  idênticas entre esses registros no período publicado.
- A janela é o mês civil anterior, no fuso fixo UTC−03:00: primeiro dia do mês passado
  inclusivo até o primeiro dia deste mês exclusivo. Exemplo: `[2026-10-01, 2026-11-01)`.
- A série tem uma barra por dia, respeitando meses de 28, 29, 30 ou 31 dias.
- Sem registro num dia significa ausência de volume registrado, não prova de uso zero.

O painel mostra os agentes presentes na fonte e os três modelos com maior volume. O restante
fica em `Remaining models`. O JSON mantém os agregados diários sanitizados e todas as
categorias de modelo permitidas, para tornar os totais conferíveis.

## Privacidade e cobertura

A coleta lê somente `usage-scan-cache-v9.json`, nunca transcrições, credenciais ou `.env`.
Não soma novamente logs nativos do Claude/Codex. Esse cache tem metadados internos de sessão
e caminho, mas o exportador usa uma projeção fechada e nunca os copia para o arquivo público.

O JSON público contém apenas período, data do último registro, origem genérica, fuso e
contadores agregados por dia/agente/modelo. Ficam de fora conteúdo de conversas, nomes de
clientes, caminhos, IDs de sessão/requisição e valores financeiros.

Somente identificadores exatamente presentes na lista de aliases do exportador recebem um
nome de modelo. Todos os demais viram `Other models`; não se infere que sejam locais.
Uma fonte identificada como local sempre vira `Local models`, mesmo se o identificador do
modelo coincidir com um alias permitido. Nomes e versões locais nunca são exportados.
Aliases nominais são aceitos apenas quando a fonte e a família correspondem: Claude Code
para Claude e Codex para GPT. Fontes desconhecidas, inclusive ferramentas que possam executar
modelos locais, sempre usam `Other agents` e `Other models`, mesmo com ID parecido com um alias.
O cache v9 atual não tem um provedor chamado `local`; esse tratamento é uma proteção adicional,
não uma integração já disponível com runtimes locais.

O snapshot atual contém métricas de Claude Code e Codex. Não há fonte local conhecida nele;
por isso, nenhum uso local é acrescentado ou apresentado como zero. Adicionar essa fonte
exigirá conferir seu contrato de contagem e manter a mesma regra de anonimização.

## Atualizar e conferir

Requisitos: Python com biblioteca padrão e cache T3 v9 disponível na máquina da coleta.
Não há servidor de métricas ou tarefa agendada configurada neste repositório.

```powershell
python -I scripts/build_usage.py --collect
python -I scripts/build_assets.py --check
python -I -m unittest discover -s tests
git diff --check
```

O primeiro comando atualiza `data/agent-usage.json` e os dois SVGs. Ele não faz commit ou push.
Para escolher uma data de referência, use `--as-of YYYY-MM-DD`: será coletado o mês civil
anterior ao mês dessa data. `--as-of 2026-11-02`, por exemplo, coleta outubro de 2026.
No schema público v2, `since` é inclusivo e `until_exclusive` é exclusivo.
`--cache CAMINHO` permite indicar outro cache v9 sem configurar credenciais.

Sem `--collect`, `scripts/build_usage.py` regenera apenas os SVGs a partir do JSON público.
`--check` valida o schema, os aliases, as referências no README e a reprodução dos SVGs;
ele nunca acessa dados da máquina de coleta. O gerador principal também executa esse check.

Uma versão de cache incompatível, contador inválido ou período sem registros causa erro e
preserva o último painel válido. A data visível do último registro permite perceber atraso.
A gravação usa substituição atômica por arquivo, após validar todos os conteúdos em memória;
uma falha de disco pode exigir executar novamente o gerador para sincronizar os arquivos.

Os testes usam entradas sintéticas separadas dos dados publicados, com cópias de requisição,
chaves nulas, fronteiras de data, raciocínio e identificadores privados contaminando a entrada.
Eles verificam contagem, rejeição de formatos inválidos e ausência de dados privados na saída.
Registros Claude marcados como `<synthetic>` são excluídos antes da deduplicação, como no T3.
Na série diária, um ponto marca um total positivo cuja barra teria menos de um pixel;
dias sem registros têm uma marca cinza, sem afirmar que não houve uso.
