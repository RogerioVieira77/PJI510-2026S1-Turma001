# DevSpecs - Especificações de Desenvolvimento

É o documento tático que descreve a construção com base nas decisões tomadas, define o que deve ser feito com detalhes da execução. 

**Projeto:** Sindiflow 
**Base documental:** Plano de desenvolvimento, SRS e PRD.
**Objetivo deste documento:** definir como construir o sistema do zero, com foco em eficiência operacional, equilíbrio funcional e capacidade de evolução.

---

## 1. Objetivo

O novo sistema deve se concentrar no que funciona bem:

- FastAPI como backend principal
- PostgreSQL como banco transacional
- Redis como cache e fila leve
- Padrões de segurança já existentes: JWT, bcrypt, rate limit, headers OWASP, auditoria
- Modelos centrais de condomínio, unidade, morador, comunicados, reservas e financeiro como referência de domínio

E deve eliminar o que gera complexidade sem retorno imediato:

- microserviços com responsabilidade sobreposta
- dependência estrutural de IA para fluxos operacionais básicos
- infraestrutura de muitos containers antes do produto fechar o básico
- módulos desabilitados e código morto
- acoplamento entre hardware/CFTV e o núcleo da gestão condominial

**Diretriz principal:** construir um produto centrado em gestão, não em tecnologia periférica.

---

## 2. Decisões estruturais para o sistema

1. **Arquitetura:** monolito modular.
2. **Banco:** um PostgreSQL transacional único no MVP.
3. **Fila:** Redis apenas para cache e tarefas assíncronas leves.
4. **Frontend:** uma aplicação web principal; 
5. **Mobile Nativo:** Visando facilitar a adoção e aprimorar a relação Síndico/Morador.
5. **Autenticação:** JWT com refresh token e RBAC.
6. **Multi-tenancy:** isolamento lógico por `condominio_id`, com enforcement em todas as queries.
7. **Observabilidade:** logs estruturados e health checks no MVP; tracing e stack completa só depois.

---

## 3. Stack Recomendada

### 3.1 Stack principal

| Camada | Tecnologia |
|--------|------------|
| Frontend | Next.js 16 + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Data fetching | TanStack Query |
| Estado global | Zustand |
| Backend | FastAPI |
| ORM | SQLAlchemy 2.0 Async |
| Driver PostgreSQL | asyncpg 
| Banco | PostgreSQL 16 | 
| Cache/Fila leve | Redis 7 
| Migrations | Alembic | 
| Auth | PyJWT + Refresh + bcrypt |
| Testes backend | pytest + httpx + factory fixtures | 
| Testes frontend | Vitest + Testing Library + Playwright |
| Deploy | Docker Compose no MVP

---

## 4. Princípios de Arquitetura

### 4.1 Regras obrigatórias

1. Todo módulo deve ter fronteira explícita de domínio.
2. Toda query de negócio deve filtrar por `condominio_id`.
3. Toda alteração administrativa e financeira deve gerar evento de auditoria.
4. Nenhuma regra de negócio crítica deve ficar no router.
5. O banco evolui exclusivamente por migration.
6. Tudo que for integração externa deve entrar por adapter/service isolado.
7. O sistema deve continuar funcional mesmo sem notificações, IA ou integrações bancárias ativas.

### 4.2 Padrão por módulo

Cada módulo deve seguir a mesma composição:

```text
backend/modules/<modulo>/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── router.py
└── policies.py
```

### 4.3 Responsabilidade de cada camada

- `router.py`: HTTP, validação de entrada, paginação, autenticação, resposta
- `schemas.py`: contratos Pydantic
- `service.py`: regras de negócio, transações, orquestração
- `repository.py`: persistência e queries reutilizáveis
- `models.py`: mapeamento ORM
- `policies.py`: autorização contextual por papel e tenant

---

## 5. Estrutura Proposta do Repositório

```text
/opt/unicomunitaria/docker/sistema-de-condominios
├── Specs.md
├── docker-compose.yml
├── docker-compose.staging.yml
├── .env.example
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── core/
│   │   ├── auth/
│   │   ├── db/
│   │   ├── logging/
│   │   ├── middleware/
│   │   ├── pagination/
│   │   ├── storage/
│   │   ├── tenancy/
│   │   ├── exceptions/
│   │   └── tasks/
│   ├── modules/
│   │   ├── admin/
│   │   ├── financeiro/
│   │   ├── manutencao/
│   │   ├── facilities/
│   │   ├── social/
│   │   ├── assembleias/
│   │   ├── ocorrencias/
│   │   ├── portaria/
│   │   └── dashboard/
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── hooks/
│   │   └── stores/
│   └── tests/
├── scripts/
└── docs/
```

### 5.1 Observação importante

- A pasta da aplicação está na estrutura: 

```bash
/opt/unicomunitaria/docker/sistema-de-condominios
```
- Já criei uma sugestão de **scaffolding** para a aplicação.

---

## 6. Ordem Lógica de Implementação

### Fase 0. Fundação técnica

Objetivo: deixar o projeto executável, previsível e pronto para crescer.

**Entregas:**

1. criar `docker-compose.staging.yml` com PostgreSQL, Redis, backend e frontend
2. criar `.env.example` completo
3. inicializar backend FastAPI novo
4. inicializar frontend Next.js novo
5. configurar Alembic
6. configurar autenticação base e RBAC
7. configurar auditoria, rate limit, logs estruturados e health checks
8. criar seeds de desenvolvimento

**Critério de aceite:** login funcional, ambiente sobe com 4 containers, migrations aplicam com um comando.

### Fase 1. Núcleo administrativo e financeiro

Objetivo: entregar o mínimo sistema realmente útil para um síndico.

**Módulos:**

1. admin
2. financeiro
3. dashboard inicial

**Funcionalidades obrigatórias:**

1. cadastro de condomínios
2. cadastro de unidades
3. cadastro de moradores
4. gestão de usuários e perfis
5. geração mensal de cobranças
6. baixa manual de pagamentos
7. cálculo de inadimplência
8. visão de resumo financeiro no dashboard

### Fase 2. Operação do condomínio

Objetivo: resolver o dia a dia operacional.

**Módulos:**

1. manutenção
2. facilities
3. ocorrências
4. social básico

**Funcionalidades obrigatórias:**

1. abrir solicitação de manutenção
2. gerar ordem de serviço
3. acompanhar status
4. cadastrar áreas comuns
5. reservar espaços
6. registrar ocorrências
7. publicar comunicados

### Fase 3. Expansão administrativa

Objetivo: fechar os fluxos que diferenciam o produto.

**Módulos:**

1. contas a pagar
2. fluxo de caixa e demonstrativos
3. assembleias
4. portaria
5. documentos
6. notificações multi-canal

### Fase 4. Escala e extensões

Objetivo: preparar o produto para operação maior.

**Itens:**

1. tracing e métricas
2. backup automatizado
3. PWA avançada ou app nativo
4. integrações bancárias completas
5. IA assistiva
6. integrações opcionais de hardware

---

## 7. Detalhamento dos Componentes

## 7.1 Backend Core

### 7.1.1 Configuração

O arquivo de configuração deve ficar em [backend/config.py] (/opt/unicomunitaria/docker/sistema-de-condominios/backend/config.py).
Deve ser simples e alinhado ao projeto.

Regras:

1. usar `BaseSettings` com validação forte
2. separar settings por domínio: app, db, auth, redis, storage, email
3. nunca usar defaults inseguros para segredo
4. centralizar `API_PREFIX`, CORS e limites de upload

Exemplo:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Sindiflow"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = ["http://localhost:3000"]
```

### 7.1.2 Banco e sessão

Na nova aplicação, o banco deve ser realmente assíncrono para combinar com FastAPI.

Exemplo:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

### 7.1.3 Middlewares

Os middlewares atuais são uma parte forte da base e devem ser implementados em: [backend/middleware](/opt/unicomunitaria/docker/sistema-de-condominios/backend/middleware).

O MVP deve ter:

1. security headers
2. request id / correlation id
3. audit log para rotas sensíveis
4. rate limit para auth e endpoints públicos

Não Obrigatório:

1. tracing distribuído completo
2. telemetria avançada

### 7.1.4 Autenticação e autorização

O padrão  de organização das autoizações deve estar em:
[backend/dependencies.py](/opt/unicomunitaria/docker/sistema-de-condominios/backend/dependencies.py).

Padrão adotado:

1. `core/auth/security.py`: hash, verify, tokens (usando PyJWT para encode/decode)
2. `core/auth/dependencies.py`: current_user, current_tenant
3. `core/auth/policies.py`: checagens de papel e escopo
4. refresh token persistido para revogação segura

Exemplo:

```python
class Role(str, Enum):
    ADMIN = "admin"
    SINDICO = "sindico"
    MORADOR = "morador"
    FUNCIONARIO = "funcionario"


def require_roles(*allowed_roles: Role):
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permissão insuficiente")
        return user
    return checker
```

### 7.1.5 Auditoria

Toda ação administrativa e financeira precisa gerar registro de auditoria.

Tabela:

```text
audit_logs
- id
- condominio_id
- actor_user_id
- entity_type
- entity_id
- action
- before_data JSONB
- after_data JSONB
- ip_address
- user_agent
- created_at
```

### 7.1.6 Upload de Arquivos (Storage)

O módulo `core/storage/` gerencia upload, download e referência a arquivos usados por vários domínios (fotos de manutenção, anexos de ocorrências, comprovantes, documentos).

**Estratégia MVP:** Filesystem local com abstração por interface.

Interface:

```python
from typing import Protocol

class StorageProvider(Protocol):
    async def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Retorna o path relativo do arquivo salvo."""
        ...

    async def download(self, path: str) -> bytes:
        ...

    async def delete(self, path: str) -> None:
        ...

    def get_url(self, path: str) -> str:
        """Retorna URL pública ou path para servir o arquivo."""
        ...
```

Implementação MVP:

```python
class LocalStorageProvider:
    def __init__(self, base_path: str = "/app/uploads"):
        self.base_path = Path(base_path)

    async def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        safe_name = f"{uuid4().hex}_{secure_filename(filename)}"
        path = self.base_path / safe_name
        path.write_bytes(file_data)
        return safe_name

    def get_url(self, path: str) -> str:
        return f"/api/v1/files/{path}"
```

Regras:

1. nenhum módulo de domínio deve acessar o filesystem diretamente
2. limite de upload configurável em `config.py` (`max_upload_size_mb`)
3. volume mapeado no Docker para persistência
4. evolução para S3/MinIO por troca de provider, sem mudança nos módulos

---

## 7.2 Módulo Admin

### Objetivo

Ser a fundação cadastral do sistema.

### Entidades

1. Condominio
2. Unidade
3. Morador
4. Usuario
5. Veiculo
6. Documento
7. MultaAdvertencia
8. HistoricoOcupacao

### Regras de implementação

1. `Usuario` e `Morador` devem ser entidades separadas.
2. Nem todo usuário precisa ser morador.
3. Toda unidade deve pertencer a um condomínio.
4. Uma unidade pode ter vários moradores, mas deve permitir marcar um responsável financeiro.
5. CNPJ, CPF e placa devem ter validação explícita.

### Modelo base sugerido

```python
class Condominio(Base):
    __tablename__ = "condominios"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(20))
    endereco: Mapped[dict] = mapped_column(JSONB, default=dict)
    ativo: Mapped[bool] = mapped_column(default=True)
```

### Endpoints mínimos

```text
POST   /admin/condominios
GET    /admin/condominios/{id}
POST   /admin/unidades
GET    /admin/unidades
POST   /admin/moradores
GET    /admin/moradores
PATCH  /admin/moradores/{id}
```

### Fluxo de Onboarding do Morador

**Decisão:** Auto-registro.

O morador se cadastra diretamente na plataforma informando: nome, CPF, email, telefone e unidade (bloco + número).

**Fluxo:**

1. Morador acessa tela de registro público
2. Informa dados pessoais e seleciona condomínio + unidade
3. Sistema cria `Usuario` com status `pendente`
4. Se o CPF já foi pré-cadastrado pelo síndico no módulo admin → vínculo automático, status `ativo`
5. Se não → síndico recebe notificação de solicitação de vínculo e aprova/rejeita
6. Após aprovação, o papel `morador` é concedido e o acesso é liberado

**Regras:**

1. o CPF deve ser único no sistema
2. o email deve ser único no sistema
3. o morador só acessa funcionalidades após vínculo confirmado
4. um síndico pode pré-cadastrar moradores para match automático por CPF
5. o auto-registro não substitui o cadastro pelo síndico — ambos os fluxos coexistem

**Endpoints adicionais:**

```text
POST   /auth/register           # Auto-registro do morador
GET    /admin/vinculos-pendentes # Listagem para síndico aprovar
POST   /admin/vinculos/{id}/aprovar
POST   /admin/vinculos/{id}/rejeitar
```

## 7.3 Módulo Financeiro

### Objetivo

Ser o centro operacional da aplicação.

### Entidades

1. ContaCondominio
2. PlanoRateio
3. TaxaCondominial
4. Cobranca
5. Pagamento
6. ContaPagar
7. LancamentoFinanceiro
8. AcordoInadimplencia
9. CategoriaFinanceira

### Regras obrigatórias

1. cobrança mensal deve ser gerada por competência
2. valor pode ser composto por taxa base, fundo, extras e descontos
3. pagamento não substitui cobrança; ele liquida cobrança
4. inadimplência deve ser calculada por vencimento e status
5. qualquer baixa financeira deve refletir no razão do condomínio

### Modelo mínimo do fluxo

```text
TaxaCondominial -> gera várias Cobrancas -> recebe Pagamentos -> gera LancamentosFinanceiros
```

### Estratégia de implementação

**Passo 1:** cobrança manual com geração interna  
**Passo 2:** segunda via e recibo  
**Passo 3:** integração bancária  
**Passo 4:** Pix e conciliação automática

### Serviço principal

```python
class BillingService:
    def __init__(self, cobranca_repo: CobrancaRepository, lancamento_repo: LancamentoRepository):
        self.cobranca_repo = cobranca_repo
        self.lancamento_repo = lancamento_repo

    async def gerar_cobrancas_mensais(self, condominio_id: UUID, competencia: date) -> int:
        unidades_ativas = await self.cobranca_repo.listar_unidades_ativas(condominio_id)
        cobrancas = []

        for unidade in unidades_ativas:
            cobrancas.append(
                Cobranca(
                    condominio_id=condominio_id,
                    unidade_id=unidade.id,
                    competencia=competencia,
                    valor_nominal=unidade.valor_cota_atual,
                    vencimento=date(competencia.year, competencia.month, 10),
                    status=CobrancaStatus.PENDENTE,
                )
            )

        await self.cobranca_repo.bulk_insert(cobrancas)
        return len(cobrancas)
```

### Endpoint exemplo

```python
@router.post("/cobrancas/gerar", status_code=202)
async def gerar_cobrancas(
    payload: GerarCobrancasInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.SINDICO)),
):
    service = BillingService(CobrancaRepository(db), LancamentoRepository(db))
    total = await service.gerar_cobrancas_mensais(current_user.condominio_id, payload.competencia)
    return {"message": "cobrancas geradas", "total": total}
```

### Dashboard financeiro mínimo

1. total previsto do mês
2. total recebido do mês
3. total em aberto
4. inadimplência por faixa de atraso
5. últimos pagamentos

### Melhor prática importante

Não acoplar emissão bancária ao núcleo de cobrança. Criar uma interface:

```python
class BoletoProvider(Protocol):
    async def emitir_boleto(self, cobranca: Cobranca) -> BoletoEmitido: ...
```

Assim o MVP pode usar um provider local/PDF e a fase 2 pode trocar para banco/API sem reescrever regra de cobrança.

---

## 7.4 Módulo Manutenção

### Objetivo

Atender o problema operacional mais visível para o morador e para o síndico.

### Entidades

1. SolicitacaoManutencao
2. OrdemServico
3. CategoriaServico
4. Tecnico
5. Fornecedor
6. SLAConfig
7. AgendaPreventiva
8. ChecklistExecucao

### Fluxo mínimo

```text
Morador abre solicitação -> Síndico/Zelador triagem -> Sistema gera OS -> Técnico executa -> Conclusão -> Custo vai para financeiro
```

### Regras obrigatórias

1. prioridade e categoria devem ser obrigatórias
2. a OS nasce vinculada à solicitação
3. toda mudança de status deve ser registrada em timeline
4. anexos devem ser aceitos desde o início
5. custo real da OS deve poder gerar lançamento financeiro depois

### Snippet de schema

```python
class SolicitacaoCreate(BaseModel):
    unidade_id: UUID
    categoria: str
    prioridade: Literal["baixa", "normal", "urgente", "emergencia"]
    descricao: str = Field(min_length=10)
    anexos: list[str] = []
```

### Snippet de serviço

```python
async def criar_ordem_servico(self, solicitacao_id: UUID, tecnico_id: UUID | None) -> OrdemServico:
    solicitacao = await self.repo.get_solicitacao(solicitacao_id)
    if not solicitacao:
        raise DomainError("Solicitação não encontrada")

    os = OrdemServico(
        condominio_id=solicitacao.condominio_id,
        solicitacao_id=solicitacao.id,
        tecnico_id=tecnico_id,
        status=StatusOS.ABERTA,
    )
    await self.repo.save_os(os)
    await self.repo.atualizar_status_solicitacao(solicitacao.id, StatusSolicitacao.EM_ATENDIMENTO)
    return os
```

---

## 7.5 Módulo Facilities

### Objetivo

Controlar espaços e ativos físicos do condomínio.

### Submódulos

1. áreas comuns
2. reservas
3. equipamentos
4. agenda integrada de uso e manutenção

### Regras obrigatórias

1. reservas não podem conflitar
2. regras de antecedência e duração devem ser configuráveis por área
3. áreas podem exigir aprovação manual
4. equipamentos precisam de histórico de manutenção

### Regra crítica de reserva

```python
async def validar_disponibilidade(area_id: UUID, inicio: datetime, fim: datetime) -> None:
    conflito = await self.repo.buscar_reserva_conflitante(area_id, inicio, fim)
    if conflito:
        raise DomainError("Já existe reserva aprovada para esse intervalo")
```

### Estrutura sugerida para regras da área

```json
{
  "antecedencia_max_dias": 60,
  "duracao_max_horas": 6,
  "requer_aprovacao": true,
  "taxa_uso": 150.0,
  "limite_reservas_mes": 2
}
```

---

## 7.6 Módulo Social

### Objetivo

Garantir comunicação consistente com os moradores.

### Entidades

1. Comunicado
2. AnexoComunicado
3. Evento
4. InscricaoEvento
5. Enquete
6. VotoEnquete
7. Notificacao

### MVP

No MVP, este módulo deve focar em comunicados.

### Regras obrigatórias

1. suportar comunicados normais e emergenciais
2. permitir fixação de comunicados no topo
3. registrar leitura no portal do morador em fase posterior
4. permitir segmentação por bloco, unidade ou todos

### Exemplo de contrato

```python
class ComunicadoCreate(BaseModel):
    titulo: str = Field(min_length=5, max_length=120)
    conteudo: str = Field(min_length=10)
    tipo: Literal["aviso", "emergencia", "informativo"]
    fixado: bool = False
    destinatario_tipo: Literal["todos", "bloco", "unidade"] = "todos"
    bloco: str | None = None
    unidade_id: UUID | None = None
```

---

## 7.7 Módulo Assembleias

### Objetivo

Cobrir convocação, registro de presença e atas primeiro; votação digital depois.

### Ordem de entrega

1. cadastro de assembleia
2. pauta
3. presença/quórum
4. histórico e ata
5. votação digital
6. procuração digital

### Observação

Votação digital é sensível juridicamente. Implementar apenas depois que presença, pauta, ata e rastreabilidade estiverem sólidos.

---

## 7.8 Módulo Ocorrências

### Objetivo

Registrar incidentes do condomínio sem depender do módulo de segurança eletrônica.

### Entidades

1. Ocorrencia
2. CategoriaOcorrencia
3. TratativaOcorrencia
4. AnexoOcorrencia

### Regras

1. qualquer perfil operacional pode registrar
2. status deve ser simples no início: aberta, em análise, resolvida, cancelada
3. deve haver vínculo opcional com unidade e morador
4. ocorrências críticas podem disparar notificação

---

## 7.9 Módulo Portaria

### Objetivo

Resolver controle operacional básico sem depender de hardware.

### Submódulos

1. visitantes
2. pré-autorização
3. encomendas
4. prestadores

### Estratégia

Este módulo entra só após admin, financeiro, manutenção, facilities e comunicados estarem estáveis.

---

## 8. Contratos de API

### 8.1 Padrão de resposta

Padronizar paginação e erro desde o início.

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 125
  }
}
```

Erro:

```json
{
  "error": {
    "code": "cobranca_duplicada",
    "message": "Já existe cobrança para a competência informada",
    "details": {}
  }
}
```

### 8.2 Convenções

1. usar plural em recursos
2. filtros via query string
3. paginação obrigatória em listagens
4. evitar endpoints com verbos quando o recurso modela bem a ação
5. ações especiais podem existir quando representam um comando claro, como `/cobrancas/gerar`

---

## 9. Frontend

## 9.1 Princípios

1. uma única aplicação web principal
2. App Router
3. `features/` por domínio
4. componentes compartilhados desacoplados de regra de negócio
5. React Query para servidor; Zustand só para estado local global

### Estrutura sugerida

```text
frontend/src/
├── app/
│   ├── login/
│   ├── (protected)/dashboard/
│   ├── (protected)/admin/
│   ├── (protected)/financeiro/
│   ├── (protected)/manutencao/
│   ├── (protected)/reservas/
│   ├── (protected)/comunicados/
│   └── layout.tsx
├── components/
├── features/
│   ├── auth/
│   ├── financeiro/
│   ├── manutencao/
│   └── reservas/
├── lib/
└── stores/
```

### Páginas mínimas do MVP

1. login
2. dashboard do síndico
3. condomínios
4. unidades
5. moradores
6. cobranças
7. pagamentos
8. solicitações de manutenção
9. ordens de serviço
10. reservas
11. comunicados
12. ocorrências

### Exemplo de hook por feature

```ts
export function useCobrancas(params: ListCobrancasParams) {
  return useQuery({
    queryKey: ["cobrancas", params],
    queryFn: () => api.get("/financeiro/cobrancas", { params }).then((res) => res.data),
  })
}
```

### Exemplo de formulário

```tsx
export function ComunicadoForm() {
  const form = useForm<ComunicadoInput>({
    resolver: zodResolver(comunicadoSchema),
    defaultValues: { tipo: "aviso", fixado: false },
  })

  const mutation = useCreateComunicado()

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <Input {...form.register("titulo")} />
        <Textarea {...form.register("conteudo")} />
        <Button type="submit">Publicar</Button>
      </form>
    </Form>
  )
}
```

### UX obrigatória

1. layout administrativo para síndico/admin
2. navegação simples e direta
3. feedback visual de loading, sucesso e erro
4. responsividade real para uso em celular
5. tabelas com filtros úteis e paginação

---

## 10. Banco de Dados

### 10.1 Estratégia

1. PostgreSQL como source of truth
2. UUID em todas as entidades principais
3. JSONB só onde há real flexibilidade de estrutura
4. índices compostos por `condominio_id` + colunas de filtro frequente
5. migrations pequenas e reversíveis

### 10.2 Regras de modelagem

1. evitar JSONB para dados que precisam de filtro recorrente
2. usar enum para status estáveis
3. usar tabelas auxiliares para categorias configuráveis
4. manter `created_at`, `updated_at` e opcionalmente `deleted_at`
5. usar unique constraints de domínio, por exemplo:

```text
unique(condominio_id, bloco, numero) em unidades
unique(condominio_id, competencia, unidade_id) em cobrancas
```

### 10.3 Exemplo de migration

```python
def upgrade() -> None:
    op.create_table(
        "condominios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("cnpj", sa.String(length=18), nullable=True),
        sa.Column("endereco", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
```

---

## 11. Notificações e tarefas assíncronas

### MVP

Usar fila leve com Redis apenas para:

1. envio de e-mail
2. envio de WhatsApp
3. geração assíncrona de relatórios
4. geração mensal de cobranças por agenda

### Decisão para Workers

No MVP, usar tarefas assíncronas simples e um worker leve. Não introduzir Celery com múltiplos brokers e complexidade operacional antes da necessidade real.

Interface sugerida:

```python
class NotificationService:
    async def send_email(self, to: str, subject: str, html: str) -> None:
        ...

  async def send_whatsapp(self, phone: str, template_key: str, payload: dict) -> None:
        ...
```

### Estratégia de canais

No MVP, os canais são:

1. **e-mail (funcional):** comunicação formal, recibos, comprovantes e trilha documental — provider real implementado
2. **WhatsApp (log-only):** interface abstrata implementada com provider que apenas registra em log. O provider real (Meta Business API ou equivalente) será conectado quando escolhido, sem mudança em código de domínio

Push nativo fica para etapa posterior, depois que a experiência mobile estiver consolidada.

**Justificativa:** a integração com WhatsApp Business API requer conta Meta Business verificada, aprovação de templates e custos por mensagem. Não deve bloquear o MVP. A interface abstrata garante que toda lógica de "quando notificar por WhatsApp" já estará pronta.

---

## 12. Infraestrutura

### 12.1 Ambientes

**Desenvolvimento/Staging/Produção inicial**

1. postgres
2. redis
3. backend
4. frontend
5. nginx

### 12.2 Compose mínimo

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sindiflow
      POSTGRES_USER: sindiflow
      POSTGRES_PASSWORD: sindiflow

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    depends_on:
      - backend
```

### 12.3 O que não entra no MVP

1. réplica de Postgres
2. MongoDB
3. Prometheus/Grafana/Jaeger/Loki
4. módulos de CFTV
5. orquestrador de IA
6. integrações com hardware
7. IOT e Smart Spaces

---

## 13. Qualidade e testes

### 13.1 Backend

Cobertura mínima por módulo:

1. testes de schema
2. testes de serviço
3. testes de rota
4. testes de autorização
5. testes de multi-tenancy

Exemplo:

```python
async def test_sindico_nao_lista_cobrancas_de_outro_condominio(client, token_sindico_a):
    response = await client.get(
        "/api/v1/financeiro/cobrancas",
        headers={"Authorization": f"Bearer {token_sindico_a}"},
    )
    assert response.status_code == 200
    assert all(item["condominio_id"] == CONDOMINIO_A_ID for item in response.json()["data"])
```

### 13.2 Frontend

1. testes de componentes críticos
2. testes de formulários
3. smoke tests por página
4. Playwright para login, cadastro, cobrança e reserva

### 13.3 Definição de pronto

Uma feature só está pronta quando:

1. rota existe
2. regra de negócio existe
3. tela existe
4. validação existe
5. auditoria existe se necessário
6. testes essenciais existem

---

## 14. Observabilidade e operação

### MVP

1. logs JSON
2. request id por requisição
3. health check liveness e readiness
4. métricas simples de erro e latência em logs

### Fase posterior

1. Prometheus
2. Grafana
3. OpenTelemetry
4. tracing distribuído

---

## 15. Roadmap tático por sprint

### Sprint 1

1. bootstrap backend
2. bootstrap frontend
3. compose simplificado
4. auth base
5. migrations iniciais

### Sprint 2

1. admin: condomínio, unidade, morador
2. dashboard inicial
3. seeds de demo

### Sprint 3

1. financeiro: cobrança mensal
2. financeiro: pagamentos
3. resumo financeiro

### Sprint 4

1. manutenção: solicitação
2. manutenção: ordem de serviço
3. timeline e status

### Sprint 5

1. facilities: áreas comuns
2. facilities: reservas
3. ocorrências básicas

### Sprint 6

1. comunicados
2. notificações por e-mail e WhatsApp
3. endurecimento de permissões
4. testes E2E críticos

### Sprint 7+

1. contas a pagar
2. relatórios
3. assembleias
4. portaria
5. expansão de canais e automações de notificação

---

## 16. Riscos técnicos e mitigação

### Risco 1: escopo inflar novamente

Mitigação: manter fases rígidas e bloquear features fora do objetivo da sprint.

### Risco 2: financeiro ficar superficial

Mitigação: tratar cobrança, pagamento, inadimplência e razão como núcleo do produto, não como módulo secundário.

### Risco 3: multi-tenancy ser esquecido em queries

Mitigação: criar helpers e testes obrigatórios para escopo por condomínio.

### Risco 4: frontend nascer como admin genérico pouco usável

Mitigação: desenhar primeiro os fluxos do síndico e do morador, não páginas abstratas de CRUD.

### Risco 5: Introdução prematura de IA/hardware

Mitigação: isolar integrações atrás de adapters e só ativar após fechamento do núcleo funcional.

---

## 17. Decisões Gerais

1. **Manter FastAPI.** Aderência ao domínio e velocidade de entrega.
2. **Usar SQLAlchemy async.** Não msiturar `async` com acesso síncrono ao banco.
3. **Só usra o gateway Node.js quando necessário** Ele aumenta superfície operacional sem necessidade.
4. **Entregar experiência mobile-first para o morador via PWA antes de app nativo.** O foco inicial é a relação síndico <-> morador, com boa UX em celular e custo operacional controlado.
5. **Adiar IA para depois da operação básica.** Adiciona custo e complexidade antes de ser vantagem competitiva.
6. **Começar o financeiro com cobrança interna, comprovante e recibo, sem boleto bancário real no MVP.** A integração bancária vem na segunda etapa e não deve travar o núcleo financeiro.
7. **Entrar no MVP com notificações por e-mail funcional e WhatsApp com implementação log-only.** E-mail é o canal operacional do MVP. WhatsApp nasce com interface abstrata e provider log-only; o provider real será conectado quando um fornecedor for escolhido, sem retrabalho na lógica de domínio.

---

## 18. Critério final de sucesso

O projeto só estará no caminho certo quando o síndico e os moradores conseguirem, sem depender de módulos extras:

1. cadastrar condomínio, unidades e moradores
2. gerar cobranças mensais
3. registrar pagamentos
4. acompanhar inadimplência
5. receber e tratar solicitações de manutenção
6. fazer follow up de solicitações
7. registrar e dar feedback de serviços prestados
7. reservar espaços comuns
8. publicar comunicados
9. operar tudo isso com boa experiência em desktop e mobile web

Se o sistema fizer isso bem, ele já terá valor real.

---

## 19. Decisões formais de arquitetura

As decisões abaixo formalizam as escolhas mais sensíveis para a construção. 
Elas devem ser consideradas vinculantes até nova revisão explícita.

### ADR-001: Financeiro do MVP sem boleto bancário real

**Status:** Aprovada

**Contexto**

O produto precisa entregar valor real no módulo financeiro logo no MVP, mas ainda não há banco ou fornecedor definido para emissão bancária. Tentar iniciar com boleto real adicionaria risco de integração, homologação e dependência externa antes de estabilizar o domínio.

**Opções consideradas**

1. iniciar com cobrança interna + comprovante/recibo
2. iniciar com boleto bancário real já no MVP
3. iniciar com Pix/cartão já no MVP

**Decisão**

O MVP usará cobrança interna com geração de competência mensal, cálculo de inadimplência, baixa manual ou semiautomática, e emissão de comprovante/recibo. Boleto bancário real, Pix e conciliação automática ficam para a segunda etapa.

**Consequências**

1. o núcleo financeiro pode ser entregue mais rápido
2. o domínio de cobrança nasce desacoplado de fornecedor externo
3. o produto terá menor automação bancária no primeiro ciclo
4. o módulo precisa prever interfaces de integração desde o início para evitar retrabalho futuro

**Diretriz de implementação**

Criar `BoletoProvider`, `PixProvider` e `BankReconciliationProvider` como contratos, mesmo que o MVP use apenas implementações locais ou mockadas.

### ADR-002: Notificações do MVP com e-mail e WhatsApp

**Status:** Aprovada

**Contexto**

O foco inicial do produto é a relação morador <-> síndico. 
Para isso, é insuficiente depender apenas de e-mail. Ao mesmo tempo, usar só WhatsApp enfraquece trilha formal e comprovável de comunicação.

**Opções consideradas**

1. apenas e-mail
2. apenas WhatsApp
3. e-mail + WhatsApp
4. e-mail + WhatsApp + push no MVP

**Decisão**

O MVP terá dois canais oficiais de notificação: e-mail e WhatsApp.

**Consequências**

1. haverá maior custo e complexidade inicial do que um canal único
2. a comunicação formal e a comunicação de alta atenção ficam cobertas
3. será necessário modelar templates, filas, status de entrega e reprocessamento
4. push nativo deixa de ser bloqueador do MVP

**Diretriz de implementação**

O domínio publica eventos e o serviço de notificação decide o canal. Nenhum módulo de negócio deve chamar diretamente um SDK de e-mail ou WhatsApp.

### ADR-003: Experiência mobile forte via PWA mobile-first

**Status:** Aprovada

**Contexto**

O morador é um usuário prioritário desde o início. A experiência em celular precisa ser forte já no MVP, mas reconstruir simultaneamente web e app nativo aumentaria o risco de execução e duplicaria o custo de manutenção.

**Opções consideradas**

1. web responsiva básica
2. PWA mobile-first
3. app nativo já no MVP
4. web e app nativo simultaneamente

**Decisão**

O produto será entregue inicialmente como aplicação web mobile-first com capacidade de evolução para PWA. App nativo fica para etapa posterior.

**Consequências**

1. o frontend precisa nascer pensando primeiro na jornada do morador em celular
2. a mesma base atende síndico e morador com custo menor
3. alguns recursos nativos avançados ficam fora do escopo inicial
4. a API deve ser desenhada desde o início para futuro consumo por app nativo sem mudanças estruturais

**Diretriz de implementação**

Criar jornadas distintas para síndico e morador, evitando um painel administrativo genérico adaptado para celular.

### ADR-004: Público inicial focado em síndico individual

**Status:** Aprovada

**Contexto**

O produto pode evoluir para administradoras multi-condomínio, mas o foco atual é síndico individual e sua relação com os moradores. Isso muda prioridades de UX, complexidade de permissões e profundidade do módulo operacional.

**Opções consideradas**

1. síndico individual como foco inicial
2. administradora multi-condomínio como foco inicial
3. atender ambos desde o primeiro ciclo

**Decisão**

O foco inicial do produto é síndico individual operando um condomínio e se relacionando diretamente com moradores.

**Consequências**

1. o portal/jornada do morador sobe de prioridade
2. o dashboard do síndico deve ser direto e operacional
3. multi-condomínio continua previsto na arquitetura, mas não orienta o MVP
4. relatórios e automações corporativas avançadas deixam de ser prioridade inicial

**Diretriz de implementação**

Modelar multi-tenancy corretamente desde o início, mas não deixar a experiência multi-condomínio complicar o desenho do MVP.

### ADR-005: Integração bancária desacoplada, sem fornecedor definido agora

**Status:** Aprovada

**Contexto**

Ainda não existe fornecedor financeiro decidido. Fixar essa escolha agora criaria lock-in prematuro e poderia atrasar a entrega do domínio financeiro.

**Opções consideradas**

1. escolher fornecedor agora
2. não escolher fornecedor e abstrair integração
3. adiar totalmente a abstração e decidir depois

**Decisão**

Nenhum fornecedor bancário será definido neste momento. O sistema deve prever integrações por contrato, mantendo o domínio financeiro independente do provedor.

**Consequências**

1. o módulo financeiro terá interfaces formais para emissão e conciliação
2. o MVP não ficará travado por homologação de terceiro
3. será necessário disciplinar bem os contratos de integração
4. a escolha do fornecedor poderá ser feita mais tarde com impacto controlado

**Diretriz de implementação**

Criar adapters separados para boleto, Pix e conciliação, com testes de contrato e implementações locais no MVP.

### ADR-006: Onboarding do morador por auto-registro

**Status:** Aprovada

**Contexto**

O sistema precisa de um fluxo claro para que moradores acessem a plataforma pela primeira vez. Sem definir esse fluxo, a adoção fica dependente de ações manuais do síndico para cada morador.

**Opções consideradas**

1. convite individual enviado pelo síndico
2. auto-registro pelo morador com validação posterior
3. ambos os fluxos simultaneamente

**Decisão**

Auto-registro pelo morador. O cadastro fica pendente até confirmação pelo síndico ou match automático por CPF pré-cadastrado.

**Consequências**

1. menor carga operacional para o síndico
2. maior velocidade de adoção
3. exige fluxo de aprovação de vínculo
4. ambos os fluxos (pré-cadastro pelo síndico e auto-registro) coexistem

**Diretriz de implementação**

Auto-registro cria `Usuario` com status `pendente`. Match por CPF ativa automaticamente. Sem match, síndico aprova manualmente.

### ADR-007: Upload de arquivos com filesystem local no MVP

**Status:** Aprovada

**Contexto**

Módulos como manutenção, ocorrências e documentos requerem upload de arquivos. Definir a estratégia desde o início evita retrabalho.

**Decisão**

Filesystem local com abstração por interface (`StorageProvider`). Evolução para S3/MinIO por troca de provider.

**Consequências**

1. zero dependência externa no MVP
2. volume Docker deve ser mapeado e incluído em backup
3. módulos de domínio nunca acessam filesystem diretamente

**Diretriz de implementação**

Interface `StorageProvider` no `core/storage/`. Implementação `LocalStorageProvider` no MVP. Config `max_upload_size_mb` no `config.py`.
