using Contoso.Orders.Api.Data;
using Contoso.Orders.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace Contoso.Orders.Api.Repositories;

/// <summary>EF Core implementation of <see cref="IOrderRepository"/>.</summary>
public sealed class OrderRepository(OrdersDbContext dbContext) : IOrderRepository
{
    private readonly OrdersDbContext _dbContext = dbContext;

    public async Task<IReadOnlyList<Order>> ListAsync(
        OrderStatus? status,
        CancellationToken cancellationToken)
    {
        IQueryable<Order> query = _dbContext.Orders
            .AsNoTracking()
            .Include(o => o.Items);

        if (status is { } value)
        {
            query = query.Where(o => o.Status == value);
        }

        return await query
            .OrderByDescending(o => o.CreatedAtUtc)
            .ToListAsync(cancellationToken);
    }

    public async Task<Order?> GetAsync(Guid id, CancellationToken cancellationToken) =>
        await _dbContext.Orders
            .Include(o => o.Items)
            .FirstOrDefaultAsync(o => o.Id == id, cancellationToken);

    public async Task AddAsync(Order order, CancellationToken cancellationToken) =>
        await _dbContext.Orders.AddAsync(order, cancellationToken);

    public async Task<bool> RemoveAsync(Guid id, CancellationToken cancellationToken)
    {
        var order = await _dbContext.Orders
            .Include(o => o.Items)
            .FirstOrDefaultAsync(o => o.Id == id, cancellationToken);

        if (order is null)
        {
            return false;
        }

        _dbContext.Orders.Remove(order);
        return true;
    }

    public Task SaveChangesAsync(CancellationToken cancellationToken) =>
        _dbContext.SaveChangesAsync(cancellationToken);
}
