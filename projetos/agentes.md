# Agentes de IA para atendimento

Código privado · Trabalho profissional em equipe

## O problema

Uma aplicação de atendimento precisava usar informações relevantes à conversa e executar ações por meio de ferramentas. Participei do desenvolvimento dos recursos de IA desse produto.

## Minha contribuição

Implementei recuperação de contexto com RAG, agentes configuráveis e integração de ferramentas por MCP. Também desenvolvi simulações de conversas com personas para exercitar o comportamento dos agentes. Essas foram contribuições dentro de um projeto em equipe.

## Como funciona

A aplicação recupera informações relacionadas à solicitação e as fornece como contexto para a resposta do modelo. Os agentes podem usar ferramentas e encaminhar solicitações conforme a especialidade necessária.

Uma decisão técnica foi usar busca semântica com embeddings e PostgreSQL/pgvector para selecionar contexto relevante, em vez de depender apenas do texto da conversa. A configuração dos agentes permite separar instruções e ferramentas por responsabilidade.

**Tecnologias:** Node.js, TypeScript, Vercel AI SDK, OpenAI SDK, PostgreSQL/pgvector e MCP.

## Código privado

Este relato descreve minha participação em termos gerais. O código, os nomes de clientes e os detalhes internos do produto permanecem privados.

[Voltar ao perfil](../README.md) · [Contato](mailto:jordyfontoura@outlook.com)
