# Declaração de uso de IA

## Ferramenta e modelo

Claude Code, no aplicativo desktop, com o modelo Claude Fable 5.2 (`claude-fable-5-2`). Foi uma única sessão, exportada em [`sessao.jsonl`](sessao.jsonl) no formato nativo da ferramenta. A exportação foi feita logo antes do commit final, então esse commit e o último push não aparecem nela. O único ajuste no arquivo foi mascarar meu e-mail.

## Como o trabalho foi dividido

Atuei como o engenheiro responsável pela entrega: direção, arquitetura, restrições e aceite. A IA atuou como executora, dentro de um plano que aprovei antes de qualquer alteração e de limites que defini. Toda decisão com consequência fora do código (o que publicar, com que permissões, com quais dados pessoais) passou por mim.

## O que eu fiz

**Engenharia de IA: execução controlada por plano e por pontos de aprovação.**
Exigi o plano antes da execução e que ele separasse, com justificativa, o que caberia a mim e o que caberia à IA. Nenhum arquivo foi alterado antes dessa aprovação.

**Guardrails.**
Limitei o trabalho ao escopo do enunciado, para que robustez não virasse excesso de engenharia. Defini as regras de publicação, restrições e guardrails. Na revisão da sessão que ficaria pública, decidi mascarar meu e-mail, que aparecia 3 vezes.

**Arquitetura de software.**
Estabeleci os critérios de qualidade: menos acoplamento, mais coesão, código limpo. O efeito é mensurável: a função que concentrava leitura, regra, agregação e serialização tinha 79 linhas e a maior função do caso de uso hoje tem 24; a média caiu de 16,8 para 7,6 linhas por função.

**Arquitetura de solução: entregar o mínimo correto antes de evoluir.**
A alternativa que escolhi separa a entrega em duas etapas. Primeiro o mínimo que resolve o problema: 5 arquivos, 5 linhas inseridas e 11 removidas, suficientes para os 5 testes fornecidos passarem. Só depois a reorganização, protegida pelos testes. Assim cada causa raiz fica legível em um commit e o refactor não se mistura com a correção.

**Critérios de aceite e evidência.**
Aprovei como condição de pronto mais do que o `pytest` verde: testes fornecidos sem alteração, amostra igual às tabelas do README, recálculo independente do dataset real e execução em Python 3.11.

## O que a IA fez

**Diagnóstico por leitura, antes de executar qualquer coisa.**
Leu os 13 módulos, os testes e os três CSVs e apontou os seis defeitos com causa raiz. Um deles, o corte da leitura em 200 linhas, estava fora do alcance dos testes fornecidos e descartava 100 das 300 reservas.

**Impacto medido no dataset real.**

| Indicador | Projeto recebido | Entrega |
|-----------|-----------------|---------|
| Reservas lidas | 200 | 300 |
| Confirmadas | 153 | 235 |
| Noites de quarto | -1393 | 1347 |
| Total em BRL | 193218.53 | 396170.00 |
| Média por noite | 0.00 | 294.11 |
| Primeiro do ranking | H04, o de menor valor | H06, o de maior valor |

**Arquitetura em camadas.**
Separou o código em `domain`, `application` e `infrastructure`. O domínio não tem nenhuma dependência de arquivo, CSV ou JSON; o caso de uso depende de 2 interfaces e de nenhuma classe concreta; a lógica de abertura e validação de CSV, antes duplicada em 2 leitores, ficou em 1 função; o arredondamento de dinheiro acontece em 1 único ponto, na serialização.

**Estratégia de testes.**
Levou a suíte de 5 para 52 testes, distribuídos por nível: 15 de domínio, 5 do caso de uso com fontes em memória, 16 do contrato do CLI, 9 de regras de negócio ponta a ponta e 2 sobre os datasets. A cobertura de ramos medida com coverage.py é de 95%, com 100% nas camadas de domínio e aplicação. A suíte roda em cerca de 3 segundos.

**Robustez de entrada.**
Quatro situações deixaram de passar despercebidas. Moeda sem taxa encerrava com código 1, como erro inesperado. Status desconhecido, zero quartos e check-out anterior ao check-in encerravam com código 0 e entravam no relatório. As quatro agora encerram com código 2, como entrada inválida.

**Verificação independente.**
Escreveu, fora do projeto, um script que recalcula o relatório a partir das regras do README sem usar o código do CLI. O resultado coincide integralmente nos 2 arquivos de dados. Criou também o workflow que roda lint, suíte e CLI em 2 versões do Python a cada push.

