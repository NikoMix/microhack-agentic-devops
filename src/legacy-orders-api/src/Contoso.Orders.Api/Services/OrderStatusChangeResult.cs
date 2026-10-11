using Contoso.Orders.Api.Dtos;

namespace Contoso.Orders.Api.Services;

/// <summary>The outcome of an attempted order status transition.</summary>
public enum OrderStatusChangeOutcome
{
    NotFound,
    InvalidTransition,
    Updated,
}

/// <summary>Result of a status transition, pairing the outcome with the updated order.</summary>
public sealed record OrderStatusChangeResult(OrderStatusChangeOutcome Outcome, OrderResponse? Order);
