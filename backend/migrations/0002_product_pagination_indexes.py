"""
Composite indexes for keyset-paginated product listing.

`idx_products_created_at_id` serves `WHERE (created_at, id) > (?, ?) ORDER BY
created_at, id` as an index range scan. `idx_stock_levels_product_id_created_at`
serves the per-product "most recent stock level" lookup
(`ORDER BY created_at DESC, id DESC LIMIT 1`) used by the products list route.

The existing `idx_stock_levels_product_id` from migration 0001 is left in
place; it is redundant with the new composite index but dropping it is not
this migration's concern.
"""

from yoyo import step

__transactional__ = True

steps = [
    step(
        apply="""
        CREATE INDEX idx_products_created_at_id
            ON products (created_at, id);
        """,
        rollback="""
        DROP INDEX IF EXISTS idx_products_created_at_id;
        """,
    ),
    step(
        apply="""
        CREATE INDEX idx_stock_levels_product_id_created_at
            ON stock_levels (product_id, created_at DESC, id DESC);
        """,
        rollback="""
        DROP INDEX IF EXISTS idx_stock_levels_product_id_created_at;
        """,
    ),
]
