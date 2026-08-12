"""
Create products and stock_levels tables.
"""

from yoyo import step

__transactional__ = True

steps = [
    step(
        apply="""
        CREATE TABLE products (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        VARCHAR NOT NULL,
            description TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE stock_levels (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id  UUID NOT NULL REFERENCES products(id),
            quantity    INTEGER NOT NULL,
            measure     VARCHAR NOT NULL
                        CHECK (measure IN ('pieces', 'kilogram', 'gram', 'litre')),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_stock_levels_product_id ON stock_levels(product_id);
        """,
        rollback="""
        DROP TABLE IF EXISTS stock_levels;
        DROP TABLE IF EXISTS products;
        """,
    )
]
