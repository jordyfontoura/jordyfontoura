# Correção de redações com IA

Código privado

## O problema

Desenvolvi uma aplicação para receber redações em texto ou imagem e produzir uma correção estruturada com IA. O fluxo reúne extração de texto, processamento e histórico das avaliações.

## Minha contribuição

Construí a aplicação, incluindo a integração com OCR, as chamadas ao modelo, o processamento assíncrono e a persistência dos resultados. Também implementei geração de temas com consulta a fontes e uma etapa de revisão editorial antes da publicação.

## Como funciona

Quando a entrada é uma foto, o texto passa por extração com OCR. A redação segue para processamento pelo modelo e o resultado é validado em um formato estruturado antes de integrar o histórico.

O contrato de saída estruturada permite que a aplicação trate os campos da avaliação, em vez de depender de uma resposta em texto livre. O processamento assíncrono separa as etapas mais demoradas da interação inicial com a interface e permite tratar retentativas.

**Tecnologias:** TypeScript, OpenAI SDK, Vercel AI SDK, Google Document AI e filas de processamento.

## Estado e código privado

O código permanece privado; esta página apresenta o trabalho em termos gerais. As correções são estimativas geradas pelo modelo.

[Voltar ao perfil](../README.md) · [Contato](mailto:jordyfontoura@outlook.com)
