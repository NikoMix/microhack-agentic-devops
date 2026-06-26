using Microsoft.EntityFrameworkCore;

namespace Contoso.Orders.Api.Data;

/// <summary>
/// Creates the schema (for relational providers) and seeds sample data on startup so the
/// API is usable the moment the container is running.
/// </summary>
public static class DatabaseInitializer
{
    public static async Task InitializeAsync(
        IServiceProvider services,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(services);

        await using var scope = services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<OrdersDbContext>();

        await context.Database.EnsureCreatedAsync(cancellationToken);

        if (!await context.Orders.AnyAsync(cancellationToken))
        {
            context.Orders.AddRange(OrderSeeder.SampleOrders());
            await context.SaveChangesAsync(cancellationToken);
        }
    }
}
