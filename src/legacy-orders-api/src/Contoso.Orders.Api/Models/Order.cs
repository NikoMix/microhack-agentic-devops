namespace Contoso.Orders.Api.Models;

/// <summary>A customer order aggregate root.</summary>
public sealed class Order
{
    public Guid Id { get; set; }

    public required string CustomerName { get; set; }

    public required string CustomerEmail { get; set; }

    public OrderStatus Status { get; set; } = OrderStatus.Pending;

    public DateTimeOffset CreatedAtUtc { get; set; }

    public DateTimeOffset? UpdatedAtUtc { get; set; }

    public IList<OrderItem> Items { get; } = [];
}
