# syntax=docker/dockerfile:1
#
# Multi-stage build for the Contoso Orders API.
#
# Stage 1 (build) uses the .NET SDK image to restore and publish a framework-dependent app.
# Stage 2 (final) uses the Ubuntu "chiseled" ASP.NET runtime image: a minimal, shell-less,
# non-root base (runs as the unprivileged $APP_UID) with a small attack surface. This image
# is the recommended production base for container apps.
#
# Build context is the solution root (src/legacy-orders-api) so Central Package Management
# files (Directory.*.props) and global.json are available to the restore.

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Restore first, using only the manifest files, so the restore layer is cached until a
# dependency or the SDK pin actually changes.
COPY global.json Directory.Build.props Directory.Packages.props ./
COPY src/Contoso.Orders.Api/Contoso.Orders.Api.csproj src/Contoso.Orders.Api/
RUN dotnet restore src/Contoso.Orders.Api/Contoso.Orders.Api.csproj

# Copy the remaining source and publish a Release build.
COPY src/ src/
RUN dotnet publish src/Contoso.Orders.Api/Contoso.Orders.Api.csproj \
    --configuration Release \
    --no-restore \
    --output /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS final
WORKDIR /app

# Listen on 8080 (the non-privileged default for the chiseled images). Azure Container Apps
# routes ingress to this port and runs its own HTTP health probes against /health, so no
# Docker HEALTHCHECK is required here.
ENV ASPNETCORE_HTTP_PORTS=8080
EXPOSE 8080

# $APP_UID is a non-root user baked into the chiseled image.
USER $APP_UID

COPY --from=build /app .
ENTRYPOINT ["dotnet", "Contoso.Orders.Api.dll"]
