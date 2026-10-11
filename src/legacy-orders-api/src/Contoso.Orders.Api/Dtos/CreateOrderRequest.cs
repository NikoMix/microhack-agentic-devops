using System.ComponentModel.DataAnnotations;

namespace Contoso.Orders.Api.Dtos;

/// <summary>Payload for creating a new order.</summary>
public sealed class CreateOrderRequest
{
    [Required]
    [StringLength(200, MinimumLength = 1)]
    public string CustomerName { get; set; } = string.Empty;

    [Required]
    [EmailAddress]
    [StringLength(320)]
    public string CustomerEmail { get; set; } = string.Empty;

    [Required]
    [MinLength(1, ErrorMessage = "An order must contain at least one item.")]
    public IList<OrderItemInput> Items { get; set; } = [];
}
