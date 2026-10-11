using Contoso.Orders.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace Contoso.Orders.Api.Data;

/// <summary>EF Core unit of work for the Orders domain.</summary>
public sealed class OrdersDbContext(DbContextOptions<OrdersDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();

    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        ArgumentNullException.ThrowIfNull(modelBuilder);
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Order>(order =>
        {
            order.HasKey(o => o.Id);
            order.Property(o => o.CustomerName).HasMaxLength(200).IsRequired();
            order.Property(o => o.CustomerEmail).HasMaxLength(320).IsRequired();
            order.Property(o => o.Status).HasConversion<string>().HasMaxLength(32).IsRequired();
            order.Property(o => o.CreatedAtUtc).IsRequired();
            order
                .HasMany(o => o.Items)
                .WithOne()
                .HasForeignKey(i => i.OrderId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<OrderItem>(item =>
        {
            item.HasKey(i => i.Id);
            item.Property(i => i.Sku).HasMaxLength(64).IsRequired();
            item.Property(i => i.Description).HasMaxLength(512).IsRequired();
            item.Property(i => i.Quantity).IsRequired();
            item.Property(i => i.UnitPrice).HasPrecision(18, 2).IsRequired();
        });
    }
}
