# Chomatter

Código privado · Protótipo de linguagem para narrativas

## A proposta

Criei uma linguagem para representar narrativas ramificadas e controlar seus fluxos de execução. Saltos (`jump`) e chamadas (`call`) permitem organizar os caminhos da narrativa, junto de diálogos, condicionais e funções.

## Minha contribuição

Desenvolvi o lexer, o parser e a representação da árvore sintática em Rust. Também construí um runtime em Deno/TypeScript para interpretar a narrativa, com escopos, memória, eventos, diálogos e saltos.

## Como funciona

O código-fonte passa pela tokenização e pelo parser em Rust. A árvore sintática é serializada em JSON para consumo pelo runtime em TypeScript, que interpreta as instruções da narrativa.

Separar a análise da linguagem de sua execução permite trabalhar essas duas partes de forma independente. A árvore sintática em JSON faz a ligação entre as implementações em Rust e TypeScript.

**Tecnologias:** Rust, Deno, TypeScript, lexer, parser e AST.

## Estado e código privado

O projeto começou em 2022 e é um protótipo. Há funcionalidades incompletas e a integração entre as versões dos módulos ainda precisa ser validada antes de oferecer uma demonstração reproduzível. O código permanece privado; este relato apresenta a proposta e o trabalho que desenvolvi.

[Voltar ao perfil](../README.md) · [Contato](mailto:jordyfontoura@outlook.com)
