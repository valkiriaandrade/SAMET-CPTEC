# Validação da refatoração

- Python 3.11 no Windows: testes de tmin/tmax, média menos climatologia, ausências,
  grades, fechamento de arquivos e mapa offline.
- Processados os 31 arquivos de temperatura máxima de julho/2024 com a climatologia
  correspondente; gerados `output/tmax.png` e `output/tmax.nc`.
- Processamento incremental: não mantém o mês inteiro em memória.
- Instalação editável do pacote e verificação Ruff executadas.

Os arquivos fornecidos não declaram unidades da temperatura. Mantém-se a convenção
do projeto original: temperatura em °C, ou K em ambas as entradas para diferenças.
Metadados de unidade divergentes são rejeitados. Cabe conferir mês, completude dos
dias e climatologia de referência. Valores ausentes propagam por célula.

