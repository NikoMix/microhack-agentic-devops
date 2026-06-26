using System.ComponentModel.DataAnnotations;

namespace Contoso.Orders.Api.Dtos;

/// <summary>Inbound representation of a single order line item.</summary>
public sealed class OrderItemInput
{
    [Required]
    [StringLength(64, MinimumLength = 1)]
    public string Sku { get; set; } = string.Empty;

    [Required]
    [StringLength(512, MinimumLength = 1)]
    public string Description { get; set; } = string.Empty;

    [Range(1, 10_000)]
    public int Quantity { get; set; }

    [Range(0.0, 1_000_000.0)]
    public decimal UnitPrice { get; set; }
}
