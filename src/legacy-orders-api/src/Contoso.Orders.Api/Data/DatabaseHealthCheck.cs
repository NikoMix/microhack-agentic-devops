using System.Data.Common;
using Microsoft.Extensions.Diagnostics.HealthChecks;

namespace Contoso.Orders.Api.Data;

/// <summary>Reports whether the configured order store is reachable.</summary>
public sealed class DatabaseHealthCheck(OrdersDbContext dbContext) : IHealthCheck
{
    private readonly OrdersDbContext _dbContext = dbContext;

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var canConnect = await _dbContext.Database.CanConnectAsync(cancellationToken);
            return canConnect
                ? HealthCheckResult.Healthy("Order store is reachable.")
                : HealthCheckResult.Unhealthy("Order store is not reachable.");
        }
        catch (DbException ex)
        {
            return HealthCheckResult.Unhealthy("Order store health check failed.", ex);
        }
    }
}
