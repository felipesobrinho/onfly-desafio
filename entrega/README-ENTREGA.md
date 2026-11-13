# Entrega

Usei IA neste desafio. A sessão e a declaração de quem fez o quê estão em [`uso-de-ia/`](uso-de-ia/).

## Defeitos corrigidos

| Defeito | Causa raiz |
|---------|-----------|
| `NO_SHOW` entrava em noites, valores, meses e ranking | A regra de faturamento testava "diferente de `CANCELLED`" em vez de "igual a `CONFIRMED`". |
| Noites erradas na virada de mês ou de ano | O cálculo subtraía o dia do mês das duas datas em vez de subtrair as datas. |
| Valores em moeda estrangeira muito abaixo do real | A conversão dividia o valor pela taxa quando deveria multiplicar. |
| Centavos imprecisos | A conversão passava por `float` antes de voltar para `Decimal`. |
| Ranking mostrava os hotéis de menor valor | A ordenação era crescente por valor; faltava inverter e desempatar por `hotel_id`. |
| Só 200 das 300 reservas eram consideradas | O leitor do CSV interrompia a leitura na linha 200. |

O último não é coberto por nenhum dos testes fornecidos: todos usam poucas linhas.

## Como investiguei

Comecei rodando `pytest -q` no projeto como veio, para confirmar as cinco falhas, e deixei esse estado no primeiro commit. Depois li cada módulo comparando com as regras do README, na ordem do processamento: leitura, conversão de tipos, contagem, filtro e agregação. Os cinco primeiros defeitos apareceram nessa leitura e batem com os cinco testes.

O corte em 200 linhas apareceu ao conferir o leitor contra o tamanho do dataset, que tem 300 reservas. Para ter certeza de que não restava nada, escrevi fora do projeto um script que recalcula o relatório direto das regras do README, sem usar o código do CLI, e comparei com a saída nos dois arquivos. Os resultados são idênticos, e a amostra reproduz as três tabelas do README.

Corrigi primeiro no código original, com o mínimo de mudança, para que cada causa raiz fique visível no diff do segundo commit. Só depois reorganizei.

## O que mais mudou

O código foi separado em três camadas. `domain` tem a reserva, o status, o câmbio e o relatório com valores exatos. `application` tem o caso de uso, que depende de interfaces e não dos leitores CSV. `infrastructure` lê os CSVs e grava o JSON, e é o único lugar onde o dinheiro é arredondado. O `cli.py` apenas monta as peças e traduz erros em códigos de saída.

Aproveitei para fechar três brechas: moeda sem taxa, status desconhecido e reserva inconsistente (quartos menor que 1 ou check-out antes do check-in) agora encerram com código 2 em vez de erro inesperado ou contagem silenciosa.

Comando, argumentos, códigos de saída e formato do relatório não mudaram. Os testes fornecidos e os arquivos de `data/` estão intactos.

## Como validar

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q

PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json
```

Para o dataset completo o resumo esperado é 300 reservas, 235 confirmadas, 31 canceladas, 34 no-show, 1347 noites, total de 396170.00 e média de 294.11.

Na minha máquina rodei com Python 3.12.3. O Python 3.11 foi validado no GitHub Actions: o workflow em `.github/workflows/tests.yml` roda o lint, a suíte e o CLI em 3.11 e 3.12 a cada push, e passou nas duas versões.

## Resultado do pytest

```
$ pytest -q
....................................................                     [100%]
52 passed in 2.59s
```

São os 5 testes fornecidos, sem alteração, mais 47 novos: regras de negócio, contrato do CLI, domínio, caso de uso e os dois datasets.
