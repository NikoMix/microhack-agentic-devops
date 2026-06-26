namespace Contoso.Orders.Api.Dtos;

/// <summary>Outbound representation of a single order line item.</summary>
public sealed class OrderItemResponse
{
    public Guid Id { get; init; }

    public string Sku { get; init; } = string.Empty;

    public string Description { get; init; } = string.Empty;

    public int Quantity { get; init; }

    public decimal UnitPrice { get; init; }

    public decimal LineTotal { get; init; }
}
