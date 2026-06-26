using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Models;

namespace Contoso.Orders.Api.Mapping;

/// <summary>Translates between domain entities and the API's data-transfer objects.</summary>
public static class OrderMapper
{
    public static OrderResponse ToResponse(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        var items = order.Items.Select(ToItemResponse).ToList();

        return new OrderResponse
        {
            Id = order.Id,
            CustomerName = order.CustomerName,
            CustomerEmail = order.CustomerEmail,
            Status = order.Status,
            Total = items.Sum(i => i.LineTotal),
            CreatedAtUtc = order.CreatedAtUtc,
            UpdatedAtUtc = order.UpdatedAtUtc,
            Items = items,
        };
    }

    public static OrderItem ToEntity(OrderItemInput input)
    {
        ArgumentNullException.ThrowIfNull(input);

        return new OrderItem
        {
            Sku = input.Sku,
            Description = input.Description,
            Quantity = input.Quantity,
            UnitPrice = input.UnitPrice,
        };
    }

    private static OrderItemResponse ToItemResponse(OrderItem item) => new()
    {
        Id = item.Id,
        Sku = item.Sku,
        Description = item.Description,
        Quantity = item.Quantity,
        UnitPrice = item.UnitPrice,
        LineTotal = item.UnitPrice * item.Quantity,
    };
}
