using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Dtos;

/// <summary>Outbound representation of an order.</summary>
public sealed class OrderResponse
{
    public Guid Id { get; init; }

    public string CustomerName { get; init; } = string.Empty;

    public string CustomerEmail { get; init; } = string.Empty;

    public OrderStatus Status { get; init; }

    public decimal Total { get; init; }

    public DateTimeOffset CreatedAtUtc { get; init; }

    public DateTimeOffset? UpdatedAtUtc { get; init; }

    public IReadOnlyList<OrderItemResponse> Items { get; init; } = [];
}
