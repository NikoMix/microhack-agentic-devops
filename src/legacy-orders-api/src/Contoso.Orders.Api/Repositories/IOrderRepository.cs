using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Repositories;

/// <summary>Persistence boundary for the Orders aggregate.</summary>
public interface IOrderRepository
{
    Task<IReadOnlyList<Order>> ListAsync(OrderStatus? status, CancellationToken cancellationToken);

    Task<Order?> GetAsync(Guid id, CancellationToken cancellationToken);

    Task AddAsync(Order order, CancellationToken cancellationToken);

    Task<bool> RemoveAsync(Guid id, CancellationToken cancellationToken);

    Task SaveChangesAsync(CancellationToken cancellationToken);
}
