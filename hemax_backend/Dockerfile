# =====================================================================
# HEMAX Backend — Dockerfile
# =====================================================================
# Multi-stage build for optimal image size

# ─── Build stage ──────────────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj files first for layer caching
COPY HEMAX.Domain/HEMAX.Domain.csproj             HEMAX.Domain/
COPY HEMAX.Application/HEMAX.Application.csproj   HEMAX.Application/
COPY HEMAX.Infrastructure/HEMAX.Infrastructure.csproj HEMAX.Infrastructure/
COPY HEMAX.Web/HEMAX.Web.csproj                   HEMAX.Web/
COPY HEMAX.sln                                     ./

RUN dotnet restore

# Copy everything else
COPY HEMAX.Domain/         HEMAX.Domain/
COPY HEMAX.Application/    HEMAX.Application/
COPY HEMAX.Infrastructure/ HEMAX.Infrastructure/
COPY HEMAX.Web/            HEMAX.Web/

# Build + publish
RUN dotnet publish HEMAX.Web/HEMAX.Web.csproj \
    -c Release \
    -o /app/publish \
    --no-restore \
    /p:UseAppHost=false

# ─── Runtime stage ────────────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# Required for Microsoft.Data.SqlClient on linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/publish .

# Create folders for uploads/logs (mounted as volumes in compose)
RUN mkdir -p /app/uploads /app/logs && \
    chmod 755 /app/uploads /app/logs

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/swagger/v1/swagger.json || exit 1

ENTRYPOINT ["dotnet", "HEMAX.Web.dll"]
