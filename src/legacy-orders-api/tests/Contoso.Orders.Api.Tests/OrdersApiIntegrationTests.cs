using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using Contoso.Orders.Api.Data;
using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Models;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace Contoso.Orders.Api.Tests;

/// <summary>
/// End-to-end HTTP tests booting the API in-process with <see cref="WebApplicationFactory{TEntryPoint}"/>.
/// Each test gets a freshly seeded, isolated in-memory database via a unique database name.
/// </summary>
public sealed class OrdersApiIntegrationTests
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() },
    };

    private static WebApplicationFactory<Program> CreateFactory() =>
        new WebApplicationFactory<Program>().WithWebHostBuilder(builder =>
            builder.UseSetting("Orders:Database:Name", $"it-{Guid.NewGuid()}"));

    [Fact]
    public async Task Health_ReturnsHealthy()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var response = await client.GetAsync("/health", CancellationToken.None);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var body = await response.Content.ReadAsStringAsync(CancellationToken.None);
        Assert.Contains("Healthy", body, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ListOrders_ReturnsSeededOrders()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        var orders = await client.GetFromJsonAsync<List<OrderResponse>>(
            "orders",
            JsonOptions,
            CancellationToken.None);

        Assert.NotNull(orders);
        Assert.Equal(3, orders!.Count);
    }

    [Fact]
    public async Task ListOrders_FilterByStatus_ReturnsOnlyMatching()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        var paid = await client.GetFromJsonAsync<List<OrderResponse>>(
            "orders?status=Paid",
            JsonOptions,
            CancellationToken.None);

        Assert.NotNull(paid);
        Assert.Single(paid!);
        Assert.Equal(OrderStatus.Paid, paid![0].Status);
        Assert.Equal(OrderSeeder.PaidOrderId, paid[0].Id);
    }

    [Fact]
    public async Task GetOrderById_ReturnsOrder_WhenItExists()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        var order = await client.GetFromJsonAsync<OrderResponse>(
            $"orders/{OrderSeeder.PaidOrderId}",
            JsonOptions,
            CancellationToken.None);

        Assert.NotNull(order);
        Assert.Equal(OrderSeeder.PaidOrderId, order!.Id);
        Assert.Equal("Ada Lovelace", order.CustomerName);
        Assert.Equal(138.00m, order.Total);
    }

    [Fact]
    public async Task GetOrderById_Returns404_WhenMissing()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var response = await client.GetAsync(
            $"orders/{Guid.NewGuid()}",
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task CreateOrder_Returns201_WithLocationAndPendingStatus()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        var request = new CreateOrderRequest
        {
            CustomerName = "New Customer",
            CustomerEmail = "new.customer@contoso.example",
            Items =
            [
                new OrderItemInput
                {
                    Sku = "CCM-CABLE-01",
                    Description = "USB-C cable",
                    Quantity = 3,
                    UnitPrice = 7.00m,
                },
            ],
        };

        using var response = await client.PostAsJsonAsync(
            "orders",
            request,
            JsonOptions,
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        Assert.NotNull(response.Headers.Location);

        var created = await response.Content.ReadFromJsonAsync<OrderResponse>(
            JsonOptions,
            CancellationToken.None);
        Assert.NotNull(created);
        Assert.Equal(OrderStatus.Pending, created!.Status);
        Assert.Equal(21.00m, created.Total);
    }

    [Fact]
    public async Task CreateOrder_Returns400_WhenNoItems()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        var request = new CreateOrderRequest
        {
            CustomerName = "Invalid Customer",
            CustomerEmail = "invalid@contoso.example",
            Items = [],
        };

        using var response = await client.PostAsJsonAsync(
            "orders",
            request,
            JsonOptions,
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task ChangeStatus_Returns200_ForLegalTransition()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var response = await client.PutAsJsonAsync(
            $"orders/{OrderSeeder.PendingOrderId}/status",
            new UpdateOrderStatusRequest { Status = OrderStatus.Paid },
            JsonOptions,
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var updated = await response.Content.ReadFromJsonAsync<OrderResponse>(
            JsonOptions,
            CancellationToken.None);
        Assert.Equal(OrderStatus.Paid, updated!.Status);
    }

    [Fact]
    public async Task ChangeStatus_Returns409_ForIllegalTransition()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var response = await client.PutAsJsonAsync(
            $"orders/{OrderSeeder.DeliveredOrderId}/status",
            new UpdateOrderStatusRequest { Status = OrderStatus.Shipped },
            JsonOptions,
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
    }

    [Fact]
    public async Task ChangeStatus_Returns404_WhenOrderMissing()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var response = await client.PutAsJsonAsync(
            $"orders/{Guid.NewGuid()}/status",
            new UpdateOrderStatusRequest { Status = OrderStatus.Paid },
            JsonOptions,
            CancellationToken.None);

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task DeleteOrder_Returns204_ThenGetReturns404()
    {
        await using var factory = CreateFactory();
        using var client = factory.CreateClient();

        using var deleteResponse = await client.DeleteAsync(
            $"orders/{OrderSeeder.PendingOrderId}",
            CancellationToken.None);
        Assert.Equal(HttpStatusCode.NoContent, deleteResponse.StatusCode);

        using var getResponse = await client.GetAsync(
            $"orders/{OrderSeeder.PendingOrderId}",
            CancellationToken.None);
        Assert.Equal(HttpStatusCode.NotFound, getResponse.StatusCode);
    }
}
