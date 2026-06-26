using Contoso.Orders.Api.Dtos;
using Contoso.Orders.Api.Models;
using Contoso.Orders.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Contoso.Orders.Api.Controllers;

/// <summary>CRUD and status-transition endpoints for customer orders.</summary>
[ApiController]
[Route("orders")]
[Produces("application/json")]
public sealed class OrdersController(IOrderService orderService) : ControllerBase
{
    private readonly IOrderService _orderService = orderService;

    /// <summary>Lists orders, optionally filtered by status.</summary>
    [HttpGet]
    [ProducesResponseType(typeof(IReadOnlyList<OrderResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IReadOnlyList<OrderResponse>>> ListAsync(
        [FromQuery] OrderStatus? status,
        CancellationToken cancellationToken)
    {
        var orders = await _orderService.ListOrdersAsync(status, cancellationToken);
        return Ok(orders);
    }

    /// <summary>Gets a single order by id.</summary>
    [HttpGet("{id:guid}", Name = nameof(GetByIdAsync))]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OrderResponse>> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken)
    {
        var order = await _orderService.GetOrderAsync(id, cancellationToken);
        return order is null ? NotFound() : Ok(order);
    }

    /// <summary>Creates a new order in the <c>Pending</c> state.</summary>
    [HttpPost]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<OrderResponse>> CreateAsync(
        [FromBody] CreateOrderRequest request,
        CancellationToken cancellationToken)
    {
        var created = await _orderService.CreateOrderAsync(request, cancellationToken);
        return CreatedAtRoute(nameof(GetByIdAsync), new { id = created.Id }, created);
    }

    /// <summary>Replaces the customer details and line items of an existing order.</summary>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OrderResponse>> UpdateAsync(
        Guid id,
        [FromBody] UpdateOrderRequest request,
        CancellationToken cancellationToken)
    {
        var updated = await _orderService.UpdateOrderAsync(id, request, cancellationToken);
        return updated is null ? NotFound() : Ok(updated);
    }

    /// <summary>Transitions an order to a new status, enforcing the lifecycle policy.</summary>
    [HttpPut("{id:guid}/status")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status409Conflict)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OrderResponse>> ChangeStatusAsync(
        Guid id,
        [FromBody] UpdateOrderStatusRequest request,
        CancellationToken cancellationToken)
    {
        var result = await _orderService.ChangeStatusAsync(id, request.Status, cancellationToken);

        return result.Outcome switch
        {
            OrderStatusChangeOutcome.NotFound => NotFound(),
            OrderStatusChangeOutcome.InvalidTransition => Conflict(new ProblemDetails
            {
                Title = "Invalid order status transition",
                Detail = $"An order cannot move to '{request.Status}' from its current status.",
                Status = StatusCodes.Status409Conflict,
            }),
            OrderStatusChangeOutcome.Updated => Ok(result.Order),
            _ => throw new InvalidOperationException(
                $"Unexpected status change outcome '{result.Outcome}'."),
        };
    }

    /// <summary>Deletes an order and its line items.</summary>
    [HttpDelete("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteAsync(Guid id, CancellationToken cancellationToken)
    {
        var removed = await _orderService.DeleteOrderAsync(id, cancellationToken);
        return removed ? NoContent() : NotFound();
    }
}
