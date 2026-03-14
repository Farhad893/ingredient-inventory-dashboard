# Ingredient Inventory — Flask + SQLite (CRUD + Analytics)

A clean, well-documented web app that demonstrates full **Create, Read, Update, Delete (CRUD)** operations with **SQLite**, plus analytical **SQL reports** (GROUP BY, window functions like **RANK** and **running average**). Built with **Flask** and Bootstrap for a simple, responsive UI.

---

##  What you’ll see

- **CRUD UI**: Add, view, edit (modal), and delete inventory items
- **Search & Sort**: Quick filtering and column sorting on the main table
- **Reports**:
  - Aggregates by category (count, average unit price, average quality, total purchase)
  - Rank materials by quality within category (`RANK() OVER (PARTITION BY ...)`)
  - Daily totals + **cumulative purchase** and **running average** (±1 day window)


> **Why Flask & SQLite?**  
> Flask provides just-what-you-need building blocks (routes, templates, forms) without heavy ceremony.  
> SQLite avoids database setup overhead; great for demos while preserving SQL features (window functions supported in modern versions).

---
Architecture

Flask (backend)
SQLite (database)
Jinja2 templates
Bootstrap UI

### Install & run
```bash
git clone https://github.com/Farhad893/ingredient-inventory-dashboard
cd ingredient-inventory-dashboard
pip install -r requirements.txt
python app.py

pip install flask
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

> The app auto-creates the SQLite DB and **seeds 12 rows** on first run.

---

## Database Schema

**Table:** `ingredient_inventory`

| Column         | Type    | Constraints                                        |
|----------------|---------|----------------------------------------------------|
| id             | INTEGER | PK AUTOINCREMENT                                   |
| date           | TEXT    | NOT NULL (ISO `YYYY-MM-DD`)                        |
| material       | TEXT    | NOT NULL                                           |
| category       | TEXT    | NOT NULL                                           |
| quantity       | INTEGER | NOT NULL, `CHECK(quantity >= 0)`                   |
| unit_price     | REAL    | NOT NULL, `CHECK(unit_price >= 0)`                 |
| quality_index  | INTEGER | NOT NULL, `CHECK(quality_index BETWEEN 0 AND 100)` |

**Indexes**
- `idx_items_material(material)`
- `idx_items_category(category)`
- `idx_items_date(date)`

**Seed data**: 12 items covering Ingredient / Package / Equipment.

---

## Application Logic (Routes)

**`GET /`** — Main table  
Search + sort:
- `q` (search in `material` or `category`)
- `sort` one of: `id,date,material,category,quantity,unit_price,quality_index`
- `order`: `asc` or `desc`

**`GET /item/<id>`** — Fetch one item (JSON)  
Used to populate the Edit modal.

**`POST /create`** — Create an item  
Fields: `date, material, category, quantity, unit_price, quality_index`

**`POST /update/<id>`** — Update an item  
Same fields as create. The Edit modal sets the form’s action dynamically via JS.

**`POST /delete/<id>`** — Delete an item

**`GET /reports`** — Analytics page  
- Aggregates by category  
- Quality ranking per category  
- Daily totals with cumulative & running average

---

##  SQL advanced queries (Reports)

### 1) Aggregates by Category
```sql
SELECT category,
       COUNT(*) AS item_count,
       ROUND(SUM(unit_price * quantity), 2) AS total_purchase,
       ROUND(AVG(unit_price), 2) AS avg_unit_price,
       ROUND(AVG(quality_index), 2) AS avg_quality
FROM ingredient_inventory
GROUP BY category
ORDER BY total_purchase DESC;
```

### 2) Rank by Quality (per Category)
```sql
SELECT id, date, material, category, quantity, unit_price, quality_index,
       ROUND(unit_price * quantity, 2) AS total_value,
       RANK() OVER (PARTITION BY category ORDER BY quality_index DESC) AS q_rank
FROM ingredient_inventory
ORDER BY category, q_rank, material;
```

### 3) Daily Totals + Cumulative + Running Average
```sql
SELECT 
    date,
    ROUND(SUM(unit_price * quantity), 2) AS daily_purchase,
    ROUND(SUM(unit_price * quantity)
          OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_purchase,
    ROUND(AVG(unit_price * quantity)
          OVER (ORDER BY date ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING), 2) AS running_average
FROM ingredient_inventory
GROUP BY date
ORDER BY date;
```

---

##  UI & Interaction Guide

- **Top search bar**: Filter by `material` or `category` (contains search).
- **Sortable headers**: Click a column header to sort; click again to toggle asc/desc.
- **Add Item**: Modal form with required/typed fields.
- **Edit Item**: Pencil button → fetch `/item/<id>` → pre-fill modal → submit to `/update/<id>`.
- **Delete**: Trash button with confirmation → `POST /delete/<id>`.
- **Reports**: Three tables with high-contrast styling and aligned numeric columns.


---

## Quick Testing Checklist

- First run shows 12 seeded rows.
- Create → visible in main table.
- Edit → updated values persist.
- Delete → row removed.
- Search → try terms like “Ingredient” or “Package”.
- Sort → by `unit_price` or `quality_index`.
- Reports → totals and averages match expectations.



