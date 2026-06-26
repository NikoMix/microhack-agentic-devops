using Contoso.Orders.Api.Data;
using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Models;
using Contoso.Orders.Api.Repositories;
using Contoso.Orders.Api.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Xunit;

namespace Contoso.Orders.Api.Tests;

/// <summary>
/// Service-level tests for <see cref="OrderService"/>. Each test runs against an isolated
/// EF Core in-memory store and uses a *fresh context per operation* (sharing one database
/// root), mirroring the scoped-DbContext-per-request lifetime the API uses in production.
/// </summary>
public sealed class OrderServiceTests
{
    /// <summary>An isolated in-memory database that hands out a fresh context per operation.</summary>
    private sealed class TestStore
    {
        private readonly string _name = $"orders-tests-{Guid.NewGuid()}";
        private readonly InMemoryDatabaseRoot _root = new();

        public async Task<T> WithServiceAsync<T>(Func<IOrderService, Task<T>> action)
        {
            await using var context = new OrdersDbContext(
                new DbContextOptionsBuilder<OrdersDbContext>()
                    .UseInMemoryDatabase(_name, _root)
                    .Options);
            return await action(new OrderService(new OrderRepository(context)));
        }
    }

    private static CreateOrderRequest SampleCreateRequest() => new()
    {
        CustomerName = "Test Customer",
        CustomerEmail = "test.customer@contoso.example",
        Items =
        [
            new OrderItemInput
            {
                Sku = "SKU-1",
                Description = "Widget",
                Quantity = 2,
                UnitPrice = 10.00m,
            },
            new OrderItemInput
            {
                Sku = "SKU-2",
                Description = "Gadget",
                Quantity = 1,
                UnitPrice = 5.50m,
            },
        ],
    };

    [Fact]
    public async Task CreateOrderAsync_PersistsPendingOrder_WithComputedTotal()
    {
        var store = new TestStore();

        var created = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));

        Assert.NotEqual(Guid.Empty, created.Id);
        Assert.Equal(OrderStatus.Pending, created.Status);
        Assert.Equal(25.50m, created.Total);
        Assert.Equal(2, created.Items.Count);

        var all = await store.WithServiceAsync(s =>
            s.ListOrdersAsync(status: null, CancellationToken.None));
        Assert.Single(all);
    }

    [Fact]
    public async Task GetOrderAsync_ReturnsNull_WhenOrderDoesNotExist()
    {
        var store = new TestStore();

        var result = await store.WithServiceAsync(s =>
            s.GetOrderAsync(Guid.NewGuid(), CancellationToken.None));

        Assert.Null(result);
    }

    [Fact]
    public async Task ListOrdersAsync_FiltersByStatus()
    {
        var store = new TestStore();
        var first = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));
        await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));
        await store.WithServiceAsync(s =>
            s.ChangeStatusAsync(first.Id, OrderStatus.Paid, CancellationToken.None));

        var paid = await store.WithServiceAsync(s =>
            s.ListOrdersAsync(OrderStatus.Paid, CancellationToken.None));
        var all = await store.WithServiceAsync(s =>
            s.ListOrdersAsync(status: null, CancellationToken.None));

        Assert.Single(paid);
        Assert.Equal(first.Id, paid[0].Id);
        Assert.Equal(2, all.Count);
    }

    [Fact]
    public async Task ChangeStatusAsync_ReturnsNotFound_WhenOrderDoesNotExist()
    {
        var store = new TestStore();

        var result = await store.WithServiceAsync(s =>
            s.ChangeStatusAsync(Guid.NewGuid(), OrderStatus.Paid, CancellationToken.None));

        Assert.Equal(OrderStatusChangeOutcome.NotFound, result.Outcome);
        Assert.Null(result.Order);
    }

    [Fact]
    public async Task ChangeStatusAsync_ReturnsInvalidTransition_ForIllegalMove()
    {
        var store = new TestStore();
        var created = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));

        // Pending -> Delivered is not a permitted transition.
        var result = await store.WithServiceAsync(s =>
            s.ChangeStatusAsync(created.Id, OrderStatus.Delivered, CancellationToken.None));

        Assert.Equal(OrderStatusChangeOutcome.InvalidTransition, result.Outcome);
        var reloaded = await store.WithServiceAsync(s =>
            s.GetOrderAsync(created.Id, CancellationToken.None));
        Assert.Equal(OrderStatus.Pending, reloaded!.Status);
    }

    [Fact]
    public async Task ChangeStatusAsync_UpdatesStatus_ForLegalMove()
    {
        var store = new TestStore();
        var created = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));

        var result = await store.WithServiceAsync(s =>
            s.ChangeStatusAsync(created.Id, OrderStatus.Paid, CancellationToken.None));

        Assert.Equal(OrderStatusChangeOutcome.Updated, result.Outcome);
        Assert.Equal(OrderStatus.Paid, result.Order!.Status);
        var reloaded = await store.WithServiceAsync(s =>
            s.GetOrderAsync(created.Id, CancellationToken.None));
        Assert.Equal(OrderStatus.Paid, reloaded!.Status);
    }

    [Fact]
    public async Task UpdateOrderAsync_ReplacesCustomerDetailsAndItems()
    {
        var store = new TestStore();
        var created = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));

        var update = new UpdateOrderRequest
        {
            CustomerName = "Renamed Customer",
            CustomerEmail = "renamed@contoso.example",
            Items =
            [
                new OrderItemInput
                {
                    Sku = "SKU-9",
                    Description = "Replacement",
                    Quantity = 3,
                    UnitPrice = 4.00m,
                },
            ],
        };

        var updated = await store.WithServiceAsync(s =>
            s.UpdateOrderAsync(created.Id, update, CancellationToken.None));

        Assert.NotNull(updated);
        Assert.Equal("Renamed Customer", updated!.CustomerName);
        Assert.Equal(12.00m, updated.Total);
        Assert.Single(updated.Items);
        Assert.Equal("SKU-9", updated.Items[0].Sku);

        var reloaded = await store.WithServiceAsync(s =>
            s.GetOrderAsync(created.Id, CancellationToken.None));
        Assert.Single(reloaded!.Items);
        Assert.Equal("SKU-9", reloaded.Items[0].Sku);
    }

    [Fact]
    public async Task UpdateOrderAsync_ReturnsNull_WhenOrderDoesNotExist()
    {
        var store = new TestStore();

        var update = new UpdateOrderRequest
        {
            CustomerName = "Nobody",
            CustomerEmail = "nobody@contoso.example",
            Items =
            [
                new OrderItemInput
                {
                    Sku = "SKU-0",
                    Description = "Nothing",
                    Quantity = 1,
                    UnitPrice = 1.00m,
                },
            ],
        };

        var result = await store.WithServiceAsync(s =>
            s.UpdateOrderAsync(Guid.NewGuid(), update, CancellationToken.None));

        Assert.Null(result);
    }

    [Fact]
    public async Task DeleteOrderAsync_RemovesOrder_ThenReportsMissing()
    {
        var store = new TestStore();
        var created = await store.WithServiceAsync(s =>
            s.CreateOrderAsync(SampleCreateRequest(), CancellationToken.None));

        var firstDelete = await store.WithServiceAsync(s =>
            s.DeleteOrderAsync(created.Id, CancellationToken.None));
        var secondDelete = await store.WithServiceAsync(s =>
            s.DeleteOrderAsync(created.Id, CancellationToken.None));

        Assert.True(firstDelete);
        Assert.False(secondDelete);
        var all = await store.WithServiceAsync(s =>
            s.ListOrdersAsync(status: null, CancellationToken.None));
        Assert.Empty(all);
    }
}
