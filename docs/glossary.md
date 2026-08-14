# Glossary

Canonical names for domain terms. The point is not to define words for humans —
it is to stop one concept acquiring three spellings across twenty items.

An entry earns its place when it records a **canonical field name**, a
**closed set of values**, or a **distinction from a term it is easily confused
with**. A plain definition that adds nothing is noise; delete it.

Add an entry when a round FAILs because two agents meant different things.

## Template

```markdown
## <Term>
<One sentence: what it is.>
Fields: `<canonicalName>` (never `<wrong>`, never `<also wrong>`)
Values: <closed set, if any>
Test ID prefix: `<term>-`
Not to be confused with: <Term> (<item id>), which is <distinction>.
Status: <if the term is provisional or not yet a first-class entity>
```

## Product
A catalog entry describing something that can be stocked.
DB columns: `id` (UUID, PK), `name`, `description`, `created_at`, `updated_at`
JSON fields: `id`, `name`, `description`, `createdAt`, `updatedAt`
Test ID prefix: `product-`

## StockLevel
A quantity record tracking how much of a Product is available.
DB columns: `id` (UUID, PK), `product_id` (FK to `products.id`), `quantity` (integer), `measure`, `created_at`, `updated_at`
JSON fields: `id`, `productId`, `quantity`, `measure`, `createdAt`, `updatedAt`
Values: `measure` is one of `pieces`, `kilogram`, `gram`, `litre`. No other value exists.
Test ID prefix: `stock-level-`

## Product.stockLevel (the per-product scalar)
The single `StockLevel` shown for a Product wherever a list represents "the"
stock level as one value, not a list of rows — e.g. a product table cell.
A Product may have zero, one, or many `StockLevel` rows (one per restock
event or measure). The scalar is the row with the greatest `created_at`,
ties broken by the greatest `id`; `null` if the Product has no `StockLevel`
row. Quantities are never summed across rows or measures — `3 kilogram` and
`5 pieces` do not add to a meaningful `8`.
Fields: `stockLevel` (object `{ quantity, measure }` or `null`), never a
`quantities` array or a summed total.
Not to be confused with: `StockLevel`, which is the underlying entity — a
Product can own several of them; `Product.stockLevel` is a derived, single
value picked from among them.
Status: introduced by S8; first-class from the product list route onward.
