using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Mapping;
using Contoso.Orders.Api.Models;
using Contoso.Orders.Api.Repositories;

namespace Contoso.Orders.Api.Services;

/// <summary>Default <see cref="IOrderService"/> implementation.</summary>
public sealed class OrderService(IOrderRepository repository) : IOrderService
{
    private readonly IOrderRepository _repository = repository;

    public async Task<IReadOnlyList<OrderResponse>> ListOrdersAsync(
        OrderStatus? status,
        CancellationToken cancellationToken)
    {
        var orders = await _repository.ListAsync(status, cancellationToken);
        return [.. orders.Select(OrderMapper.ToResponse)];
    }

    public async Task<OrderResponse?> GetOrderAsync(Guid id, CancellationToken cancellationToken)
    {
        var order = await _repository.GetAsync(id, cancellationToken);
        return order is null ? null : OrderMapper.ToResponse(order);
    }

    public async Task<OrderResponse> CreateOrderAsync(
        CreateOrderRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var order = new Order
        {
            Id = Guid.NewGuid(),
            CustomerName = request.CustomerName,
            CustomerEmail = request.CustomerEmail,
            Status = OrderStatus.Pending,
            CreatedAtUtc = DateTimeOffset.UtcNow,
        };

        foreach (var input in request.Items)
        {
            order.Items.Add(OrderMapper.ToEntity(input));
        }

        await _repository.AddAsync(order, cancellationToken);
        await _repository.SaveChangesAsync(cancellationToken);
        return OrderMapper.ToResponse(order);
    }

    public async Task<OrderResponse?> UpdateOrderAsync(
        Guid id,
        UpdateOrderRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var order = await _repository.GetAsync(id, cancellationToken);
        if (order is null)
        {
            return null;
        }

        order.CustomerName = request.CustomerName;
        order.CustomerEmail = request.CustomerEmail;

        // Replace the line items. Existing rows are removed via orphan cascade (clearing the
        // navigation), and new items are created without an Id so EF Core treats them as inserts
        // and generates the key. Pre-assigning the key would make the change tracker classify a
        // new child of an already-tracked order as Modified, producing a phantom UPDATE.
        order.Items.Clear();
        foreach (var input in request.Items)
        {
            order.Items.Add(OrderMapper.ToEntity(input));
        }

        order.UpdatedAtUtc = DateTimeOffset.UtcNow;
        await _repository.SaveChangesAsync(cancellationToken);
        return OrderMapper.ToResponse(order);
    }

    public async Task<OrderStatusChangeResult> ChangeStatusAsync(
        Guid id,
        OrderStatus newStatus,
        CancellationToken cancellationToken)
    {
        var order = await _repository.GetAsync(id, cancellationToken);
        if (order is null)
        {
            return new OrderStatusChangeResult(OrderStatusChangeOutcome.NotFound, null);
        }

        if (!OrderStatusPolicy.CanTransition(order.Status, newStatus))
        {
            return new OrderStatusChangeResult(OrderStatusChangeOutcome.InvalidTransition, null);
        }

        order.Status = newStatus;
        order.UpdatedAtUtc = DateTimeOffset.UtcNow;
        await _repository.SaveChangesAsync(cancellationToken);
        return new OrderStatusChangeResult(
            OrderStatusChangeOutcome.Updated,
            OrderMapper.ToResponse(order));
    }

    public async Task<bool> DeleteOrderAsync(Guid id, CancellationToken cancellationToken)
    {
        var removed = await _repository.RemoveAsync(id, cancellationToken);
        if (removed)
        {
            await _repository.SaveChangesAsync(cancellationToken);
        }

        return removed;
    }
}
