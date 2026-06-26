using System.Collections.Frozen;

namespace Contoso.Orders.Api.Models;

/// <summary>
/// Encapsulates the allowed order status transitions. Centralizing the rule keeps the
/// business invariant in one place and makes it trivially unit-testable.
/// </summary>
public static class OrderStatusPolicy
{
    private static readonly FrozenDictionary<OrderStatus, OrderStatus[]> AllowedTransitions =
        new Dictionary<OrderStatus, OrderStatus[]>
        {
            [OrderStatus.Pending] = [OrderStatus.Paid, OrderStatus.Cancelled],
            [OrderStatus.Paid] = [OrderStatus.Shipped, OrderStatus.Cancelled],
            [OrderStatus.Shipped] = [OrderStatus.Delivered],
            [OrderStatus.Delivered] = [],
            [OrderStatus.Cancelled] = [],
        }.ToFrozenDictionary();

    /// <summary>Returns <see langword="true"/> when moving from <paramref name="from"/> to
    /// <paramref name="to"/> is a permitted transition.</summary>
    public static bool CanTransition(OrderStatus from, OrderStatus to) =>
        from != to
        && AllowedTransitions.TryGetValue(from, out var targets)
        && Array.IndexOf(targets, to) >= 0;
}
