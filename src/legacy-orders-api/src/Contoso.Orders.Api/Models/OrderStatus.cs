namespace Contoso.Orders.Api.Models;

/// <summary>Lifecycle states for a customer order.</summary>
public enum OrderStatus
{
    Pending,
    Paid,
    Shipped,
    Delivered,
    Cancelled,
}
