# Orders API (Azure DevOps export snapshot)

> This is the **README from the source Azure DevOps repository**, captured as part of the
> bundled sample export. It represents what a real repo looks like *before* migration.
> The real, maintained service lives at [`src/legacy-orders-api/`](../../../src/legacy-orders-api/).

The **Contoso Orders API** is a small .NET service that stores customer orders. It was built and
shipped from Azure DevOps using the pipeline in [`../pipelines/azure-pipelines.yml`](../pipelines/azure-pipelines.yml)
and tracked on Azure Boards (exported to [`../boards/`](../boards/)).

## Build

```bash
dotnet build src/legacy-orders-api/Contoso.Orders.slnx -c Release
dotnet test src/legacy-orders-api/Contoso.Orders.slnx -c Release
```

## Endpoints

- `GET /health`
- `GET /orders`
- `GET /orders/{id}`
- `POST /orders`
- `PUT /orders/{id}`
- `DELETE /orders/{id}`
