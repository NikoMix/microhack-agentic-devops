using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Services;

/// <summary>Application service that orchestrates order use cases.</summary>
public interface IOrderService
{
    Task<IReadOnlyList<OrderResponse>> ListOrdersAsync(
        OrderStatus? status,
        CancellationToken cancellationToken);

    Task<OrderResponse?> GetOrderAsync(Guid id, CancellationToken cancellationToken);

    Task<OrderResponse> CreateOrderAsync(
        CreateOrderRequest request,
        CancellationToken cancellationToken);

    Task<OrderResponse?> UpdateOrderAsync(
        Guid id,
        UpdateOrderRequest request,
        CancellationToken cancellationToken);

    Task<OrderStatusChangeResult> ChangeStatusAsync(
        Guid id,
        OrderStatus newStatus,
        CancellationToken cancellationToken);

    Task<bool> DeleteOrderAsync(Guid id, CancellationToken cancellationToken);
}
