# NOME DO SISTEMA - Descrição breve do Objetivo do Sistema

## Software Requirements Specification - SRS completo

- Modelo ER
- Diagramas UML principais
- Documento de Requisitos de Software (SRS)

### Introdução

#### Propósito

Este documento descreve os requisitos funcionais e não funcionais do Sistema

O sistema tem como objetivo fornecer:

- 
- 
- 
...

Focando em: 

#### 1.2 Escopo do Sistema

O sistema permitirá:

- 
- 
- 
...

O sistema será acessado via: (Exemplo: Aplicação web e possuirá uma aplicação mobile)

#### 1.3 Definições

Termo            | Definição                                                    |
-----------------|--------------------------------------------------------------|
Exemplo Termo 1  | Descrição do termo...........................................|
Exemplo Termo 1  | Descrição do termo...........................................|
.................|..............................................................|

### 2. Visão Geral do Sistema

#### 2.1 Usuários do Sistema

Tipo de Usuário         | Descrição                                             |
------------------------|-------------------------------------------------------|
Exemplo Adm             | Responsável pela gestão geral do sistema              |
Técnico 1               | Gerencia operações do condomínio                      |
Técnico 2               | Utiliza funcionalidades sociais e solicita serviços   |
------------------------|-------------------------------------------------------|

#### 2.2 Arquitetura Geral

Arquitetura proposta:

Arquitetura em Camadas

<!-- Exemplo -->

```text

Frontend (Web / Mobile)
API Backend
Camada de Serviços
Camada de Persistência
Banco de Dados
```

### 3. Requisitos Funcionais

**`RF01 — Exemplo 1`**

O sistema deve permitir...

Campos:

- 
- 
- 
...

**`RF02 — Exemplo 2`**

O sistema deve permitir...

Campos:

- 
- 
- 
...

**`RF03 — Exemplo 3`**

O sistema deve permitir...

Campos:

- 
- 
- 
...

**`RF04 — Exemplo 4`**

### 5. Modelo Entidade Relacionamento (ER)

Entidades principais

```sql

- id_
- nome
- 


```

Diagrama ER simplificado

´´´sql
TABELA_1
    |
    | 1:N
    |
TABELA_2
    |
    | 1:N
    |

### 6. Diagramas UML

#### 6.1 Diagrama de Casos de Uso

Atores:

- 
- 
- 
...

Casos de uso principais

```text
Ator_1
  ├─ 
  ├─ 
  ├─ 
  └─ 

Ator_2
  ├─ 
  ├─ 
  ├─ 
  └─ 

Ator_N
  ├─ 
  ├─ 
  ├─ 
  └─ 
```

#### 6.2 Diagrama de Classes (UML)

Nome_da_classe_1

```text
- 
- 
- 
...

Nome_da_classe_2

- 
- 
- 
...

Nome_da_classe_3

- 
- 
- 
...

Nome_da_classe_N

- 
- 
- 
...


Relacionamentos:

```text

Nome_da_classe_1 --- Nome_da_classe_2

- 
- 
- 
...Nome_da_classe_N --- Nome_da_classe_M

```

### 7. Roadmap de Desenvolvimento

Fase 1 — 

Implementar:

- 
- 
- 
...


Fase 2 — 

Implementar:

- 
- 
- 
...

Fase N — 

Implementar:

- 
- 
- 
...