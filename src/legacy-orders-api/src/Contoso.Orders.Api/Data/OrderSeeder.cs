using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Data;

/// <summary>
/// Deterministic seed data used to make the API immediately explorable in the lab.
/// The fixed identifiers let tests and docs reference specific orders by id.
/// </summary>
public static class OrderSeeder
{
    public static readonly Guid PaidOrderId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    public static readonly Guid PendingOrderId = Guid.Parse("22222222-2222-2222-2222-222222222222");
    public static readonly Guid DeliveredOrderId = Guid.Parse("33333333-3333-3333-3333-333333333333");

    public static IReadOnlyList<Order> SampleOrders()
    {
        var createdAt = new DateTimeOffset(2025, 1, 6, 9, 0, 0, TimeSpan.Zero);

        var paid = new Order
        {
            Id = PaidOrderId,
            CustomerName = "Ada Lovelace",
            CustomerEmail = "ada.lovelace@contoso.example",
            Status = OrderStatus.Paid,
            CreatedAtUtc = createdAt,
        };
        paid.Items.Add(new OrderItem
        {
            Id = Guid.Parse("a1111111-1111-1111-1111-111111111111"),
            OrderId = PaidOrderId,
            Sku = "CCM-KEYBOARD-01",
            Description = "Contoso mechanical keyboard",
            Quantity = 1,
            UnitPrice = 89.00m,
        });
        paid.Items.Add(new OrderItem
        {
            Id = Guid.Parse("a2222222-2222-2222-2222-222222222222"),
            OrderId = PaidOrderId,
            Sku = "CCM-MOUSE-01",
            Description = "Contoso wireless mouse",
            Quantity = 2,
            UnitPrice = 24.50m,
        });

        var pending = new Order
        {
            Id = PendingOrderId,
            CustomerName = "Grace Hopper",
            CustomerEmail = "grace.hopper@contoso.example",
            Status = OrderStatus.Pending,
            CreatedAtUtc = createdAt.AddDays(1),
        };
        pending.Items.Add(new OrderItem
        {
            Id = Guid.Parse("b1111111-1111-1111-1111-111111111111"),
            OrderId = PendingOrderId,
            Sku = "CCM-MONITOR-27",
            Description = "Contoso 27\" 4K monitor",
            Quantity = 1,
            UnitPrice = 329.99m,
        });

        var delivered = new Order
        {
            Id = DeliveredOrderId,
            CustomerName = "Alan Turing",
            CustomerEmail = "alan.turing@contoso.example",
            Status = OrderStatus.Delivered,
            CreatedAtUtc = createdAt.AddDays(2),
            UpdatedAtUtc = createdAt.AddDays(5),
        };
        delivered.Items.Add(new OrderItem
        {
            Id = Guid.Parse("c1111111-1111-1111-1111-111111111111"),
            OrderId = DeliveredOrderId,
            Sku = "CCM-DOCK-01",
            Description = "Contoso USB-C docking station",
            Quantity = 1,
            UnitPrice = 149.00m,
        });

        return [paid, pending, delivered];
    }
}
