using Contoso.Orders.Api.Models;
using Xunit;

namespace Contoso.Orders.Api.Tests;

/// <summary>Unit tests for the order status transition policy (pure business rule).</summary>
public sealed class OrderStatusPolicyTests
{
    [Theory]
    [InlineData(OrderStatus.Pending, OrderStatus.Paid)]
    [InlineData(OrderStatus.Pending, OrderStatus.Cancelled)]
    [InlineData(OrderStatus.Paid, OrderStatus.Shipped)]
    [InlineData(OrderStatus.Paid, OrderStatus.Cancelled)]
    [InlineData(OrderStatus.Shipped, OrderStatus.Delivered)]
    public void CanTransition_AllowsValidTransitions(OrderStatus from, OrderStatus to) =>
        Assert.True(OrderStatusPolicy.CanTransition(from, to));

    [Theory]
    [InlineData(OrderStatus.Pending, OrderStatus.Shipped)]
    [InlineData(OrderStatus.Pending, OrderStatus.Delivered)]
    [InlineData(OrderStatus.Paid, OrderStatus.Delivered)]
    [InlineData(OrderStatus.Shipped, OrderStatus.Cancelled)]
    [InlineData(OrderStatus.Delivered, OrderStatus.Shipped)]
    [InlineData(OrderStatus.Cancelled, OrderStatus.Paid)]
    public void CanTransition_RejectsInvalidTransitions(OrderStatus from, OrderStatus to) =>
        Assert.False(OrderStatusPolicy.CanTransition(from, to));

    [Theory]
    [InlineData(OrderStatus.Pending)]
    [InlineData(OrderStatus.Paid)]
    [InlineData(OrderStatus.Shipped)]
    [InlineData(OrderStatus.Delivered)]
    [InlineData(OrderStatus.Cancelled)]
    public void CanTransition_RejectsNoOpTransition(OrderStatus status) =>
        Assert.False(OrderStatusPolicy.CanTransition(status, status));
}
