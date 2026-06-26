using System.Text.Json.Serialization;
using Contoso.Orders.Api.Data;
using Contoso.Orders.Api.Repositories;
using Contoso.Orders.Api.Services;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddControllers()
    .AddJsonOptions(options =>
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));

builder.Services.AddProblemDetails();
builder.Services.AddOpenApi();

// The Orders API uses the EF Core in-memory provider, so the container is fully stateless
// and ships with zero native dependencies (and therefore zero native CVE surface). The
// database name is configurable so parallel test runs stay isolated.
var databaseName = builder.Configuration["Orders:Database:Name"] ?? "orders";
builder.Services.AddDbContext<OrdersDbContext>(options =>
    options.UseInMemoryDatabase(databaseName));

builder.Services.AddScoped<IOrderRepository, OrderRepository>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services
    .AddHealthChecks()
    .AddCheck<DatabaseHealthCheck>("database", tags: ["ready"]);

var app = builder.Build();

app.MapOpenApi();
app.MapControllers();
app.MapHealthChecks("/health");

await DatabaseInitializer.InitializeAsync(app.Services);

await app.RunAsync();
