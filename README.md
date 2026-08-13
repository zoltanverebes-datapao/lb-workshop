# Databricks Lakebase Workshop

This hands-on workshop walks you through building a full-stack application backed by **Databricks Lakebase** (managed Postgres), with bidirectional sync between the Lakehouse and Lakebase.

## Prerequisites

- A Databricks workspace on **AWS**
- Unity Catalog enabled
- Permissions to create Lakebase projects, Databricks Apps, and catalog objects
- Access to this GitHub repository

## Architecture Overview

```
┌─────────────┐    Lakehouse Sync     ┌─────────────┐
│  Lakehouse   │ ───────────────────▶  │  Lakebase    │
│ (Delta Lake) │                       │  (Postgres)  │
│              │ ◀───────────────────  │              │
└─────────────┘    CDF Sync           └──────┬───────┘
       ▲                                     │
       │ CSV ingest                          │ Lakebase connector
       │                                     ▼
  ┌─────────┐                         ┌─────────────┐
  │  Files   │                         │ Databricks  │
  │ (CSV)    │                         │    App      │
  └─────────┘                         └─────────────┘
```

---

## Step 1 — Create a Lakebase Project

Create a new Lakebase Postgres project in your Databricks workspace.

1. In the Databricks workspace sidebar, navigate to **Lakebase**.
2. Click **Create project**.
3. Give your project a name (e.g. `workshop-lakebase`).
4. Select the catalog and schema where the project should live.
5. Wait for the project to reach **Active** status.

> **Docs:** [Get started with Lakebase](https://docs.databricks.com/aws/en/oltp/projects/get-started) | [Lakebase overview](https://docs.databricks.com/aws/en/oltp/projects/)

---

## Step 2 — Create and Deploy a Databricks App

Deploy the workshop application as a Databricks App, connected to your Lakebase project via a Lakebase connector.

### 2.1 — Create the App

1. In the workspace sidebar, navigate to **Compute > Apps**.
2. Click **Create app**.
3. Under **Source**, select **GitHub repository** and point it to this repo's `main` branch.
4. Give the app a name (e.g. `workshop-app`).

### 2.2 — Add a Lakebase Connector

1. In the app configuration, go to **Resources**.
2. Click **Add resource** and select **Lakebase**.
3. Select the Lakebase project you created in Step 1.
4. The connector injects connection details (host, port, database, user, password) as environment variables into your app at runtime.

### 2.3 — Deploy

1. Ensure the source branch is set to `main`.
2. Click **Deploy**. The app will build and start automatically.
3. Subsequent pushes to `main` will trigger automatic redeployments.

> **Docs:** [Deploy a Databricks App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy) | [Lakebase connector for Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase) | [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)

---

## Step 3 — Ingest CSV Data into the Lakehouse

Upload the CSV files from the `dataset/` folder into the Lakehouse as Delta tables.

### Option A — UI Upload

1. In the workspace sidebar, navigate to your target catalog and schema.
2. Click **Create table**.
3. Upload `dataset/product.csv` — review the schema preview and click **Create table**.
4. Repeat for `dataset/stock_level.csv`.

### Option B — SQL with COPY INTO

If the files are in a Unity Catalog volume or cloud storage:

```sql
-- Upload files to a volume first, then:
COPY INTO catalog.schema.product
FROM '/Volumes/catalog/schema/volume_name/dataset/product.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');

COPY INTO catalog.schema.stock_level
FROM '/Volumes/catalog/schema/volume_name/dataset/stock_level.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
```

> **Docs:** [Create a table by uploading a file](https://docs.databricks.com/aws/en/ingestion/create-or-modify-table) | [Upload files to a volume](https://docs.databricks.com/aws/en/ingestion/file-upload/upload-data) | [COPY INTO](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/copy-into/)

---

## Step 4 — Sync Tables from Lakehouse to Lakebase

Set up continuous replication from your Lakehouse Delta tables into Lakebase so the application can query them with low latency.

> **TODO:** The synced tables land in a different Lakebase schema by default. You will need to copy the data into the application schema's `product` and `stock_level` tables so the app can read them.

1. Open your Lakebase project.
2. Navigate to **Synced tables**.
3. Click **Add synced table**.
4. Select the `product` Delta table from your catalog and click **Sync**.
5. Repeat for `stock_level`.
6. Monitor the sync status — initial sync may take a few minutes.

### Copy to the Application Schema

Because synced tables are created in a separate Lakebase schema, copy them into the application schema:

```sql
-- Run in the Lakebase SQL editor or from the app
INSERT INTO app_schema.product
SELECT * FROM synced_schema.product;

INSERT INTO app_schema.stock_level
SELECT * FROM synced_schema.stock_level;
```

> Adjust schema names to match your project configuration.

> **Docs:** [Sync tables from Lakehouse to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/sync-tables) | [Lakehouse Sync overview](https://docs.databricks.com/aws/en/oltp/projects/lakehouse-sync)

---

## Step 5 — Set Up CDF Sync from Lakebase to Lakehouse

Enable Change Data Feed (CDF) to capture changes made in Lakebase and write them back to the Lakehouse as Delta tables. This closes the loop — application writes flow back to the Lakehouse for analytics.

1. Open your Lakebase project.
2. Navigate to **Change Data Feed**.
3. Select the tables you want to track (e.g. `product`, `stock_level`).
4. Configure the target catalog and schema in Unity Catalog.
5. Enable the CDF sync.
6. Changes made via the app (INSERTs, UPDATEs, DELETEs) will now appear as Delta tables in your Lakehouse.

> **Docs:** [Lakebase Change Data Feed](https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf) | [CDF quickstart](https://docs.databricks.com/aws/en/oltp/projects/quickstart-lakebase-cdf)

---

## Summary

| Step | What | Result |
|------|------|--------|
| 1 | Create Lakebase project | Managed Postgres ready |
| 2 | Deploy Databricks App | Full-stack app connected to Lakebase |
| 3 | Ingest CSVs | `product` and `stock_level` in the Lakehouse |
| 4 | Lakehouse → Lakebase sync | Tables available for low-latency app queries |
| 5 | Lakebase → Lakehouse CDF | App changes flow back for analytics |
