# Contoso Orders API

A small, deliberately **legacy-styled** .NET 10 Web API for customer orders. It is the
*migration subject* for [Challenge 01 — Azure DevOps → GitHub migration](../../docs/challenges/challenge-01-migration/README.md):
attendees take this service (originally built and shipped on Azure DevOps) and move it,
together with its pipeline, to GitHub.

> The code intentionally uses a classic, controller-based, layered style (controller →
> service → repository → EF Core). It is clean and fully tested, but its shape mirrors a
> typical line-of-business app you would find in an enterprise Azure DevOps org.

## Architecture

```text
HTTP ─▶ OrdersController ─▶ IOrderService ─▶ IOrderRepository ─▶ EF Core (InMemory)
                                  │
                                  └─▶ OrderStatusPolicy (lifecycle invariant)
```

- **Framework:** ASP.NET Core controllers on .NET 10 minimal hosting.
- **Persistence:** EF Core **in-memory** provider. The service is therefore stateless and the
  container ships with **zero native dependencies** (and zero native CVE surface), which keeps
  the lab fast and reproducible. Swapping in a relational provider is a documented stretch goal.
- **OpenAPI:** first-party `Microsoft.AspNetCore.OpenApi` document at `/openapi/v1.json`.
- **Health:** `/health` endpoint backed by an EF Core connectivity check (tagged `ready`).
- **Seed data:** three deterministic orders are seeded on startup so the API is immediately
  explorable and tests/docs can reference fixed ids.

## Endpoints

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/orders` | List orders. Optional `?status=Pending\|Paid\|Shipped\|Delivered\|Cancelled`. |
| `GET` | `/orders/{id}` | Get a single order by id. |
| `POST` | `/orders` | Create an order (starts in `Pending`). |
| `PUT` | `/orders/{id}` | Replace an order's customer details and line items. |
| `PUT` | `/orders/{id}/status` | Transition an order to a new status (policy-enforced). |
| `DELETE` | `/orders/{id}` | Delete an order and its line items. |
| `GET` | `/health` | Liveness/readiness probe. |
| `GET` | `/openapi/v1.json` | OpenAPI 3 document. |

### Order status lifecycle

```text
Pending ─▶ Paid ─▶ Shipped ─▶ Delivered
   │         │
   └────────┴─▶ Cancelled
```

Illegal transitions return **409 Conflict**; unknown ids return **404 Not Found**; invalid
payloads return **400 Bad Request** as RFC 7807 `ProblemDetails`.

## Prerequisites

- [.NET SDK 10.0](https://dotnet.microsoft.com/download/dotnet/10.0) (pinned in `global.json`).
- Optional: Docker, to build and run the container image.

## Run locally

```bash
cd src/legacy-orders-api
dotnet run --project src/Contoso.Orders.Api
```

Then explore the seeded data:

```bash
curl http://localhost:5000/orders
curl http://localhost:5000/health
```

Create an order:

```bash
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{
        "customerName": "Katherine Johnson",
        "customerEmail": "katherine.johnson@contoso.example",
        "items": [
          { "sku": "CCM-LAPTOP-14", "description": "Contoso 14\" laptop", "quantity": 1, "unitPrice": 1299.00 }
        ]
      }'
```

Move it through its lifecycle:

```bash
curl -X PUT http://localhost:5000/orders/{id}/status \
  -H "Content-Type: application/json" \
  -d '{ "status": "Paid" }'
```

## Build, test, and scan

```bash
cd src/legacy-orders-api
dotnet build -c Release -warnaserror          # 0 warnings is the quality gate
dotnet test  -c Release                        # xUnit unit + integration tests
dotnet list src/Contoso.Orders.Api package --vulnerable --include-transitive
dotnet format --verify-no-changes              # style verification
```

The repository uses **Central Package Management** (`Directory.Packages.props`) so every
dependency version is pinned in one place, and **warnings-as-errors** with the latest .NET
analyzers and code-style enforcement.

## Container image

The [`Dockerfile`](./Dockerfile) is a multi-stage build that publishes a framework-dependent
app and runs it on the Ubuntu **chiseled** ASP.NET runtime image — a minimal, shell-less,
**non-root** base. Build from the solution root so the Central Package Management files are in
the build context:

```bash
cd src/legacy-orders-api
docker build -t contoso-orders-api:local .
docker run --rm -p 8080:8080 contoso-orders-api:local
curl http://localhost:8080/health
```

The container listens on port **8080** and runs as the unprivileged `$APP_UID` user. Azure
Container Apps performs its own HTTP health probes against `/health`, so no Docker
`HEALTHCHECK` is defined.

## Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `Orders:Database:Name` | `orders` | Name of the in-memory database (isolates parallel test runs). |
| `ASPNETCORE_HTTP_PORTS` | `8080` (container) | Ingress port. |

No secrets are required. In Azure, the service authenticates to platform resources with its
**managed identity** via `DefaultAzureCredential` — there are no connection strings or keys to
store. See the challenge docs for the full Azure deployment contract.

## Project layout

```text
src/legacy-orders-api
├── Directory.Build.props        # net10.0, nullable, warnings-as-errors, analyzers
├── Directory.Packages.props     # Central Package Management (pinned versions)
├── global.json                  # SDK pin
├── Dockerfile / .dockerignore   # chiseled, non-root container image
├── azure-pipelines.yml          # the "before": classic Azure Pipelines definition
├── Contoso.Orders.slnx          # solution
├── src/Contoso.Orders.Api/      # the API (controllers, services, repositories, EF Core)
└── tests/Contoso.Orders.Api.Tests/  # xUnit unit + integration tests
```

## License

Released under the [MIT License](../../LICENSE). All dependencies are MIT / Apache-2.0.
