from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
from pathlib import Path

# -----------------------------
# App configuration
# -----------------------------
APP_NAME = "Ingredient Inventory"

# Jupyter-friendly base directory
BASE_DIR = Path(__file__).resolve().parent

# Project paths
DB_PATH = BASE_DIR / "inventory.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)

app.secret_key = "dev-secret"


# -----------------------------
# Database schema
# -----------------------------
DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingredient_inventory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date          TEXT NOT NULL,
    material      TEXT NOT NULL,
    category      TEXT NOT NULL,
    quantity      INTEGER NOT NULL CHECK(quantity >= 0),
    unit_price    REAL NOT NULL CHECK(unit_price >= 0),
    quality_index INTEGER NOT NULL CHECK(quality_index BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_items_material ON ingredient_inventory(material);
CREATE INDEX IF NOT EXISTS idx_items_category ON ingredient_inventory(category);
CREATE INDEX IF NOT EXISTS idx_items_date ON ingredient_inventory(date);
"""


# -----------------------------
# Seed data
# -----------------------------
SEED_ROWS = [
    ("2025-09-01", "Whey Protein",  "Ingredient", 10, 18.49, 92),
    ("2025-09-02", "Arabic Gum",    "Ingredient",  5, 12.30, 85),
    ("2025-09-03", "Sugar",         "Ingredient", 25,  0.79, 88),
    ("2025-09-04", "Bottle 30 oz",  "Package",    20,  0.08, 80),
    ("2025-09-05", "Vanilla",       "Ingredient", 12,  3.40, 90),
    ("2025-09-06", "Cocoa Powder",  "Ingredient",  9,  4.10, 87),
    ("2025-09-07", "Citric Acid",   "Ingredient",  7,  2.30, 86),
    ("2025-09-08", "Labels (100x)", "Package",     3,  1.20, 78),
    ("2025-09-09", "Caps 30mm",     "Package",    50,  0.05, 75),
    ("2025-09-10", "Mixer Blade",   "Equipment",   2, 49.00, 93),
    ("2025-09-11", "Maltodextrin",  "Ingredient", 18,  1.85, 84),
    ("2025-09-12", "Salt",          "Ingredient", 30,  0.35, 89),
]


# -----------------------------
# Database helper functions
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed=True):
    db_exists = DB_PATH.exists()

    with get_conn() as conn:
        conn.executescript(DDL)

        if seed and not db_exists:
            conn.executemany(
                """
                INSERT INTO ingredient_inventory
                (date, material, category, quantity, unit_price, quality_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                SEED_ROWS
            )


# -----------------------------
# Template filters
# -----------------------------
@app.template_filter("money")
def money(value):
    try:
        return "${:,.2f}".format(float(value))
    except Exception:
        return value


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "date")
    order = request.args.get("order", "asc")

    valid_sort_columns = {
        "id", "date", "material", "category",
        "quantity", "unit_price", "quality_index"
    }

    if sort not in valid_sort_columns:
        sort = "date"

    direction = "ASC" if order == "asc" else "DESC"

    with get_conn() as conn:
        if q:
            like = f"%{q}%"
            rows = conn.execute(
                f"""
                SELECT * FROM ingredient_inventory
                WHERE material LIKE ? OR category LIKE ?
                ORDER BY {sort} {direction}, id ASC
                """,
                (like, like)
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT * FROM ingredient_inventory
                ORDER BY {sort} {direction}, id ASC
                """
            ).fetchall()

    return render_template(
        "index.html",
        rows=rows,
        q=q,
        sort=sort,
        order=order,
        app_name=APP_NAME
    )


@app.route("/item/<int:item_id>")
def get_item(item_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM ingredient_inventory WHERE id = ?",
            (item_id,)
        ).fetchone()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify(dict(row))


@app.route("/create", methods=["POST"])
def create():
    form = request.form
    required_fields = ["date", "material", "category", "quantity", "unit_price", "quality_index"]

    if not all(form.get(field) for field in required_fields):
        flash("All fields are required.", "danger")
        return redirect(url_for("index"))

    try:
        date = form["date"].strip()
        material = form["material"].strip()
        category = form["category"].strip()
        quantity = int(form["quantity"])
        unit_price = float(form["unit_price"])
        quality_index = int(form["quality_index"])
    except Exception:
        flash("Invalid field types.", "danger")
        return redirect(url_for("index"))

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ingredient_inventory
            (date, material, category, quantity, unit_price, quality_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, material, category, quantity, unit_price, quality_index)
        )

    flash("Item created.", "success")
    return redirect(url_for("index"))


@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    form = request.form

    try:
        date = form["date"].strip()
        material = form["material"].strip()
        category = form["category"].strip()
        quantity = int(form["quantity"])
        unit_price = float(form["unit_price"])
        quality_index = int(form["quality_index"])
    except Exception:
        flash("Invalid field types.", "danger")
        return redirect(url_for("index"))

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE ingredient_inventory
            SET date = ?, material = ?, category = ?, quantity = ?, unit_price = ?, quality_index = ?
            WHERE id = ?
            """,
            (date, material, category, quantity, unit_price, quality_index, item_id)
        )

    flash("Item updated.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM ingredient_inventory WHERE id = ?",
            (item_id,)
        )

    flash("Item deleted.", "warning")
    return redirect(url_for("index"))


@app.route("/reports")
def reports():
    with get_conn() as conn:
        by_category = conn.execute(
            """
            SELECT
                category,
                COUNT(*) AS item_count,
                ROUND(SUM(unit_price * quantity), 2) AS total_purchase,
                ROUND(AVG(unit_price), 2) AS avg_unit_price,
                ROUND(AVG(quality_index), 2) AS avg_quality
            FROM ingredient_inventory
            GROUP BY category
            ORDER BY total_purchase DESC
            """
        ).fetchall()

        ranked = conn.execute(
            """
            SELECT
                id,
                date,
                material,
                category,
                quantity,
                unit_price,
                quality_index,
                ROUND(unit_price * quantity, 2) AS total_value,
                RANK() OVER (
                    PARTITION BY category
                    ORDER BY quality_index DESC
                ) AS q_rank
            FROM ingredient_inventory
            ORDER BY category, q_rank, material
            """
        ).fetchall()

        cumulative = conn.execute(
            """
            SELECT
                date,
                ROUND(SUM(unit_price * quantity), 2) AS daily_purchase,
                ROUND(
                    SUM(unit_price * quantity) OVER (
                        ORDER BY date
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),
                    2
                ) AS cumulative_purchase
            FROM ingredient_inventory
            GROUP BY date
            ORDER BY date
            """
        ).fetchall()

    return render_template(
        "reports.html",
        app_name=APP_NAME,
        by_category=by_category,
        ranked=ranked,
        cumulative=cumulative
    )


# -----------------------------
# Initialize database
# -----------------------------
init_db(seed=True)

print("Database initialized at:", DB_PATH)
print("Templates folder:", TEMPLATES_DIR)
print("Static folder:", STATIC_DIR) 

if __name__ == "__main__":
    init_db(seed=True)
    app.run(debug=True)