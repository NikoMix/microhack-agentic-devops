namespace Contoso.Orders.Api.Models;

/// <summary>A single line item belonging to an <see cref="Order"/>.</summary>
public sealed class OrderItem
{
    public Guid Id { get; set; }

    public Guid OrderId { get; set; }

    public required string Sku { get; set; }

    public required string Description { get; set; }

    public int Quantity { get; set; }

    public decimal UnitPrice { get; set; }
}
