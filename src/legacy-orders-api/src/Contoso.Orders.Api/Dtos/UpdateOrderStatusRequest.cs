using System.ComponentModel.DataAnnotations;
using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Dtos;

/// <summary>Payload for transitioning an order to a new status.</summary>
public sealed class UpdateOrderStatusRequest
{
    [Required]
    [EnumDataType(typeof(OrderStatus))]
    public OrderStatus Status { get; set; }
}
