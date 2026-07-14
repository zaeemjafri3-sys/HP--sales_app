import requests

SUPABASE_URL = "https://szjpuockpucmukmtbqnn.supabase.co"

SUPABASE_KEY = "sb_publishable_ZvCtyaZORKn5sWJFJVPhIw_ubq3lFvj"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
from kivy.app import App
from plyer import gps
from kivy.uix.screenmanager import ScreenManager
import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
import math
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
import webbrowser
from kivy.uix.image import Image
from kivy.clock import Clock
from datetime import datetime, date
import uuid
from plyer import camera
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.effects.scroll import ScrollEffect
from kivy.uix.popup import Popup
import xml.etree.ElementTree as ET
import requests
import time
from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup, MapSource
import sqlite3
import io

from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.core.text import Label as CoreLabel
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.animation import Animation
import os
import mercantile
from kivy.core.window import Window
try:
    from android.permissions import (
        request_permissions,
        Permission
    )
except:
    pass
from jnius import autoclass

PythonActivity = autoclass("org.kivy.android.PythonActivity")
Context = autoclass("android.content.Context")
LocationManager = autoclass("android.location.LocationManager")

Window.clearcolor = (1, 1, 1, 1)

# ================= OFFLINE MAP =================

CACHE = "map"

MIN_LAT = 24.75
MAX_LAT = 25.25

MIN_LON = 66.80
MAX_LON = 67.55

# ================= DATABASE =================
        
def internet_available():

    try:

        requests.get(
            "https://www.google.com",
            timeout=3
        )

        return True

    except:

        return False

def get_battery_level():

    try:

        from plyer import battery

        info = battery.status()

        return info["percentage"]

    except:

        return 0
    
def get_db():

    return sqlite3.connect(
        "employees.db"
    )

def create_database():

    conn = get_db()
    cur = conn.cursor()

    # ==========================================================
    # PART 1A - BLOCK 2
    # EMPLOYEES
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_code TEXT UNIQUE NOT NULL,

        password_hash TEXT NOT NULL,

        full_name TEXT NOT NULL,

        phone TEXT UNIQUE,

        nic TEXT UNIQUE,

        age INTEGER
            CHECK(age >= 18),

        map_link TEXT,

        is_active INTEGER DEFAULT 1
            CHECK(is_active IN (0,1)),

        total_shops INTEGER DEFAULT 0,

        total_bills INTEGER DEFAULT 0,

        total_units_sold INTEGER DEFAULT 0,

        total_sale REAL DEFAULT 0,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # ==========================================================
    # EMPLOYEE INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_code
    ON employees(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_phone
    ON employees(phone)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_nic
    ON employees(nic)
    """)
    # ==========================================================
    # PART 2
    # LIVE LOCATIONS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_locations (

        employee_code TEXT NOT NULL,

        latitude REAL NOT NULL,

        longitude REAL NOT NULL,

        accuracy REAL,

        speed REAL,

        battery INTEGER,

        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        
        is_synced INTEGER DEFAULT 0,
                
        FOREIGN KEY(employee_code)
            REFERENCES employees(employee_code)
            ON DELETE CASCADE
    )
    """)

    # ==========================================================
    # LIVE LOCATION INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_live_employee
    ON live_locations(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_live_location_time
    ON live_locations(employee_code, updated_at DESC)
    """)
    
    # ==========================================================
    # PART 3
    # SHOPS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shops (

        shop_code TEXT PRIMARY KEY,

        shop_name TEXT NOT NULL,

        owner_name TEXT,

        phone TEXT,

        address TEXT,

        latitude REAL,

        longitude REAL,

        total_visits INTEGER DEFAULT 0,

        total_bills INTEGER DEFAULT 0,

        total_units_sold INTEGER DEFAULT 0,

        total_sale REAL DEFAULT 0,

        is_active INTEGER DEFAULT 1
            CHECK(is_active IN (0,1)),

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0
        
    )
    """)

    # ==========================================================
    # SHOP INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_shop_code
    ON shops(shop_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_shop_name
    ON shops(shop_name)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_shop_phone
    ON shops(phone)
    """)
    

    # ==========================================================
    # EMPLOYEE STOCK
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employee_stock (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_code TEXT NOT NULL,

        product_name TEXT NOT NULL,

        variant_name TEXT NOT NULL,

        assigned_units INTEGER DEFAULT 0
            CHECK(assigned_units >= 0),

        sold_units INTEGER DEFAULT 0
            CHECK(sold_units >= 0),

        remaining_units INTEGER DEFAULT 0
            CHECK(remaining_units >= 0),

        selling_price REAL DEFAULT 0
            CHECK(selling_price >= 0),

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0,
        
        FOREIGN KEY(employee_code)
            REFERENCES employees(employee_code)
            ON DELETE CASCADE
    )
    """)


    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_employee_stock_unique
    ON employee_stock(employee_code, product_name, variant_name);
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_stock_employee
    ON employee_stock(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_stock_product
    ON employee_stock(product_name)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_stock_variant
    ON employee_stock(variant_name)
    """)

    # ==========================================================
    # STOCK RETURNS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        return_code TEXT UNIQUE NOT NULL,

        employee_code INTEGER NOT NULL,

        product_name TEXT NOT NULL,

        variant_name TEXT NOT NULL,

        stock_issued INTEGER NOT NULL
            CHECK(stock_issued >= 0),

        stock_sold INTEGER NOT NULL
            CHECK(stock_sold >= 0),

        returned_units INTEGER NOT NULL
            CHECK(returned_units > 0),

        selling_price REAL DEFAULT 0,

        returned_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0,
        
        FOREIGN KEY(employee_code)
            REFERENCES employees(id)
            ON DELETE CASCADE
    )
    """)

        
    # ==========================================================
    # STOCK RETURN INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_stock_return_code
    ON stock_returns(return_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_stock_return_employee
    ON stock_returns(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_stock_product
    ON employee_stock(product_name)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_stock_variant
    ON employee_stock(variant_name)
    """)
        
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_stock_return_date
    ON stock_returns(returned_at)
    """)
        
    # ==========================================================
    # PART 5
    # SETTINGS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        low_stock_limit INTEGER DEFAULT 10,

        credit_limit REAL DEFAULT 0,

        login_status INTEGER DEFAULT 1
            CHECK(login_status IN (0,1)),

        app_status INTEGER DEFAULT 1
            CHECK(app_status IN (0,1)),

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # ==========================================================
    # DEFAULT SETTINGS ROW
    # ==========================================================

    cur.execute("""
    INSERT OR IGNORE INTO settings
    (
        id,
        low_stock_limit,
        credit_limit,
        login_status,
        app_status
    )
    VALUES
    (
        1,
        10,
        0,
        1,
        1
    )
    """)
    
    # ==========================================================
    # PART 6
    # SHOP VISITS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shop_visits (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_code TEXT NOT NULL,

        shop_code TEXT NOT NULL,

        visit_date TEXT DEFAULT CURRENT_TIMESTAMP,
        
        is_synced INTEGER DEFAULT 0,

        FOREIGN KEY(employee_code)
            REFERENCES employees(employee_code)
            ON DELETE CASCADE,

        FOREIGN KEY(shop_code)
            REFERENCES shops(shop_code)
            ON DELETE CASCADE

    )
    """)

    # ==========================================================
    # SHOP VISITS INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_visit_employee
    ON shop_visits(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_visit_shop
    ON shop_visits(shop_code)
    """)
    
    # ==========================================================
    # PART 7
    # BILLS
    # ==========================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        bill_no TEXT UNIQUE NOT NULL,

        employee_code TEXT NOT NULL,

        shop_code TEXT NOT NULL,

        total_products INTEGER DEFAULT 0,

        total_units INTEGER DEFAULT 0,

        total_amount REAL DEFAULT 0
            CHECK(total_amount >= 0),

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0,
        
        FOREIGN KEY(employee_code)
            REFERENCES employees(employee_code)
            ON DELETE RESTRICT,

        FOREIGN KEY(shop_code)
            REFERENCES shops(shop_code)
            ON DELETE CASCADE

    )
    """)

    # ==========================================================
    # BILL INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_no
    ON bills(bill_no)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_employee
    ON bills(employee_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_shop
    ON bills(shop_code)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_date
    ON bills(created_at)
    """)

    # ==========================================================
    # PART 8
    # BILL ITEMS
    # ==========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        bill_no TEXT NOT NULL,

        shop_code TEXT NOT NULL,

        inventory_id INTEGER NOT NULL,

        product_name TEXT NOT NULL,

        variant_name TEXT NOT NULL,

        units INTEGER NOT NULL
            CHECK(units > 0),

        unit_price REAL NOT NULL
            CHECK(unit_price >= 0),

        total REAL NOT NULL
            CHECK(total >= 0),

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0,
        
        FOREIGN KEY(bill_no)
            REFERENCES bills(bill_no)
            ON DELETE CASCADE,

        FOREIGN KEY(shop_code)
            REFERENCES shops(shop_code)
            ON DELETE CASCADE
    )
    """)

    # ==========================================================
    # BILL ITEMS INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_items_bill_no
    ON bill_items(bill_no);
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_items_shop
    ON bill_items(shop_code);
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_items_inventory
    ON bill_items(inventory_id);
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_bill_items_product
    ON bill_items(product_name);
    """)

    # ==========================================================
    # PART 9
    # DAILY SALES
    # ==========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_sales (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sale_date TEXT NOT NULL,

        employee_code TEXT NOT NULL,

        total_bills INTEGER DEFAULT 0,

        total_sale REAL DEFAULT 0,

        total_units INTEGER DEFAULT 0,

        total_products INTEGER DEFAULT 0,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        is_synced INTEGER DEFAULT 0,
        
        FOREIGN KEY(employee_code)
            REFERENCES employees(employee_code)
            ON DELETE CASCADE
    )
    """)

    # ==========================================================
    # DAILY SALES INDEXES
    # ==========================================================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_sales_date
    ON daily_sales(sale_date);
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_sales_employee
    ON daily_sales(employee_code);
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_sales_unique
    ON daily_sales(sale_date, employee_code);
    """)

    # ==========================================================
    # COMMIT & CLOSE
    # ==========================================================

    conn.commit()

    # ==========================================================
    # CLOSE DATABASE
    # ==========================================================

    conn.close()
    
def generate_bill_no():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT bill_no
        FROM bills
        ORDER BY id DESC
        LIMIT 1
    """)

    last = cur.fetchone()

    if last:

        try:
            number = int(last[0].replace("HPBN", "")) + 1
        except:
            number = 1

    else:

        number = 1

    conn.close()

    return f"HPBN{number:03d}"

def generate_shop_code():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT shop_code
    FROM shops
    ORDER BY shop_code DESC
    LIMIT 1
    """)

    row = cur.fetchone()

    conn.close()

    if row:

        last = int(row[0][3:])   # HPS001 -> 1

    else:

        last = 0

    return f"HPS{last + 1:03d}"

def generate_visit_key():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM shop_visits
        ORDER BY id DESC
        LIMIT 1
        """
    )

    last = cur.fetchone()

    if last:
        number = last[0] + 1
    else:
        number = 1

    visit_key = f"VIS{number:03d}"

    conn.close()

    return visit_key

def delete_local_kml():

    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{current_employee_id}.kml"
    )

    if os.path.exists(filename):
        os.remove(filename)

def sync_all_tables():

    print("Sync Started")
    if not internet_available():
        return
    sync_live_locations()
    sync_shops()
    sync_shop_visits()
    sync_bills()
    sync_bill_items()
    sync_daily_sales()
    sync_employee_stock()

    print("Sync Finished")

def sync_employee_stock():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            employee_code,
            product_name,
            variant_name,
            assigned_units,
            sold_units,
            remaining_units,
            selling_price
        FROM employee_stock
        WHERE is_synced = 0
        ORDER BY id
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/employee_stock",

                headers=HEADERS,

                json={
                    "employee_code": row[1],
                    "product_name": row[2],
                    "variant_name": row[3],
                    "assigned_units": row[4],
                    "sold_units": row[5],
                    "remaining_units": row[6],
                    "selling_price": row[7]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE employee_stock
                    SET is_synced = 1
                    WHERE id = ?
                """, (row[0],))

            else:

                print(
                    "Employee Stock Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Employee Stock Sync Error:", e)

    conn.commit()
    conn.close()
    
def sync_daily_sales():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            sale_date,
            employee_code,
            total_bills,
            total_sale,
            total_units,
            total_products
        FROM daily_sales
        WHERE is_synced = 0
        ORDER BY id
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/daily_sales",

                headers=HEADERS,

                json={
                    "sale_date": row[1],
                    "employee_code": row[2],
                    "total_bills": row[3],
                    "total_sale": row[4],
                    "total_units": row[5],
                    "total_products": row[6]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE daily_sales
                    SET is_synced = 1
                    WHERE id = ?
                """, (row[0],))

            else:

                print(
                    "Daily Sales Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Daily Sales Sync Error:", e)

    conn.commit()
    conn.close()
    
def sync_bill_items():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            bill_no,
            shop_code,
            inventory_id,
            product_name,
            variant_name,
            units,
            unit_price,
            total,
            created_at
        FROM bill_items
        WHERE is_synced = 0
        ORDER BY id
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/bill_items",

                headers=HEADERS,

                json={
                    "bill_no": row[1],
                    "shop_code": row[2],
                    "inventory_id": row[3],
                    "product_name": row[4],
                    "variant_name": row[5],
                    "units": row[6],
                    "unit_price": row[7],
                    "total": row[8],
                    "created_at": row[9]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE bill_items
                    SET is_synced = 1
                    WHERE id = ?
                """, (row[0],))

            else:

                print(
                    "Bill Items Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Bill Items Sync Error:", e)

    conn.commit()
    conn.close()
    
def sync_live_locations():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            employee_code,
            latitude,
            longitude,
            accuracy,
            speed,
            battery,
            updated_at
        FROM live_locations
        WHERE is_synced = 0
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/live_locations?on_conflict=employee_code",
                headers={
                    **HEADERS,
                    "Prefer": "resolution=merge-duplicates"
                },
                json={
                    "employee_code": row[0],
                    "latitude": row[1],
                    "longitude": row[2],
                    "accuracy": row[3],
                    "speed": row[4],
                    "battery": row[5],
                    "updated_at": row[6]
                }
            )
            

            print(
                "Location Sync:",
                response.status_code,
                response.text
            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE live_locations
                    SET is_synced = 1
                    WHERE employee_code = ?
                    AND updated_at = ?
                """,
                (
                    row[0],
                    row[6]
                ))

            else:

                print(
                    "Location Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Location Sync Error:", e)

    conn.commit()
    conn.close()

def sync_shops():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            shop_code,
            shop_name,
            owner_name,
            phone,
            address,
            latitude,
            longitude,
            total_visits,
            total_bills,
            total_units_sold,
            total_sale,
            is_active,
            created_at,
            updated_at
        FROM shops
        WHERE is_synced = 0
        ORDER BY shop_code
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/shops",

                headers=HEADERS,

                json={
                    "shop_code": row[0],
                    "shop_name": row[1],
                    "owner_name": row[2],
                    "phone": row[3],
                    "address": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "total_visits": row[7],
                    "total_bills": row[8],
                    "total_units_sold": row[9],
                    "total_sale": row[10],
                    "is_active": row[11],
                    "created_at": row[12],
                    "updated_at": row[13]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE shops
                    SET is_synced = 1
                    WHERE shop_code = ?
                """, (row[0],))

            else:

                print(
                    "Shop Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Shop Sync Error:", e)

    conn.commit()
    conn.close()
    
def sync_shop_visits():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            employee_code,
            shop_code,
            visit_date
        FROM shop_visits
        WHERE is_synced = 0
        ORDER BY id
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/shop_visits",

                headers=HEADERS,

                json={
                    "employee_code": row[1],
                    "shop_code": row[2],
                    "visit_date": row[3]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE shop_visits
                    SET is_synced = 1
                    WHERE id = ?
                """, (row[0],))

            else:

                print(
                    "Shop Visit Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Shop Visit Sync Error:", e)

    conn.commit()
    conn.close()
    
def sync_bills():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            bill_no,
            employee_code,
            shop_code,
            total_products,
            total_units,
            total_amount,
            created_at
        FROM bills
        WHERE is_synced = 0
        ORDER BY id
    """)

    rows = cur.fetchall()

    for row in rows:

        try:

            response = requests.post(

                f"{SUPABASE_URL}/rest/v1/bills",

                headers=HEADERS,

                json={
                    "bill_no": row[1],
                    "employee_code": row[2],
                    "shop_code": row[3],
                    "total_products": row[4],
                    "total_units": row[5],
                    "total_amount": row[6],
                    "created_at": row[7]
                }

            )

            if response.status_code in (200, 201):

                cur.execute("""
                    UPDATE bills
                    SET is_synced = 1
                    WHERE id = ?
                """, (row[0],))

            else:

                print(
                    "Bill Sync Failed:",
                    response.status_code,
                    response.text
                )

        except Exception as e:

            print("Bill Sync Error:", e)

    conn.commit()
    conn.close()
    
def return_stock():

    try:

        # ---------------- Internet Check ----------------

        try:

            requests.get(
                "https://www.google.com",
                timeout=5
            )

        except:

            print("Internet connection required.")
            return False

        # ---------------- SQLITE ----------------

        conn = get_db()

        conn.row_factory = sqlite3.Row

        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM employee_stock
            WHERE employee_code = ?
        """, (
            current_employee_id,
        ))

        rows = cur.fetchall()

        if not rows:

            conn.close()

            print("No stock available.")
            return False

        # ---------------- Upload To Supabase ----------------

        for i, row in enumerate(rows):

            payload = {

                "return_code":
                    f"RET-{current_employee_id}-{int(time.time())}-{i}",

                "employee_code":
                    current_employee_id,

                "product_name":
                    row["product_name"],

                "variant_name":
                    row["variant_name"],

                "stock_issued":
                    int(row["assigned_units"]),

                "stock_sold":
                    int(row["sold_units"]),

                "returned_units":
                    int(row["remaining_units"]),

                "selling_price":
                    float(row["selling_price"])
            }

            r = requests.post(

                f"{SUPABASE_URL}/rest/v1/stock_returns",

                headers={
                    **HEADERS,
                    "Prefer": "return=minimal"
                },

                json=payload

            )

            if r.status_code not in (200, 201):

                conn.close()

                print(r.text)

                return False

        # ---------------- Delete Local Stock ----------------

        cur.execute("""
            DELETE FROM employee_stock
            WHERE employee_code = ?
        """, (
            current_employee_id,
        ))

        conn.commit()

        conn.close()

        # ---------------- Delete Supabase Employee Stock ----------------

        r = requests.delete(

            f"{SUPABASE_URL}/rest/v1/employee_stock"
            f"?employee_code=eq.{current_employee_id}",

            headers=HEADERS

        )

        if r.status_code not in (200, 204):

            print("Unable to clear employee stock from Supabase.")

            return False

        print("Stock returned successfully.")

        return True

    except Exception as e:

        print("Return Stock Error:", e)

        return False
# ================= CURRENT LOGGED EMPLOYEE =================

current_employee_db_id = None      # Database ID
current_employee_id = ""           # Employee Code
current_employee_name = ""
current_employee_map = ""

# ============================================================
# OFFLINE MBTILES MAP SOURCE
# ============================================================

class MBTilesMapSource(MapSource):

    MBTILES_FILE = "/storage/emulated/0/Z = programs/HP wholesale item suppliers/map.mbtiles"

    def __init__(self):

        super().__init__(
            cache_key="offline",
            min_zoom=11,
            max_zoom=16,
            image_ext="png"
        )

        self.conn = sqlite3.connect(
            self.MBTILES_FILE,
            check_same_thread=False
        )

        self.cur = self.conn.cursor()
        
    def load_tile(self, tile):

        cache_file = tile.cache_fn

        if os.path.exists(cache_file):
            tile.set_source(cache_file)
            return

        self.cur.execute(
            """
            SELECT tile_data
            FROM tiles
            WHERE zoom_level=?
            AND tile_column=?
            AND tile_row=?
            """,
            (
                tile.zoom,
                tile.tile_x,
                tile.tile_y
            )
        )

        row = self.cur.fetchone()

        if row is None:
            
            return
        
        with open(cache_file, "wb") as f:
            f.write(row[0])

        tile.set_source(cache_file)
        
    def fill_tile(self, tile):

        print("Loading tile:", tile.zoom, tile.tile_x, tile.tile_y)

        if tile.state == "done":
            return

        self.load_tile(tile)
# ================= BUTTON =================

class OutlineButton(Button):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.background_normal=""

        self.background_color=(
            0.9,0.9,0.9,1
        )

        self.color=(
            0,0,0,1
        )

        self.font_size=30
        
# ================= INPUT =================

class CenteredInput(TextInput):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.multiline=False

        self.font_size=30

        self.size_hint=(None,None)

        self.width=dp(300)

        self.height=dp(43)

        self.background_normal=""

        self.background_color=(
            0.9,0.9,0.9,1
        )

        self.foreground_color=(
            0,0,0,1
        )

        self.halign="center"
        self.valign="middle"

        self.padding=[
            0,10
        ]

class WhiteBox(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1,1,1,1)
            self.rect = Rectangle(
                size=self.size,
                pos=self.pos
            )

        self.bind(
            size=self.update_rect,
            pos=self.update_rect
        )

    def update_rect(self,*args):
        self.rect.size=self.size
        self.rect.pos=self.pos

# ================= LOGIN SCREEN =================

class LoginScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        scroll = ScrollView(
            do_scroll_x=False
        )

        root = FloatLayout()

        # ================= WHITE BACKGROUND =================

        with root.canvas.before:

            Color(1,1,1,1)

            self.rect = Rectangle(
                size=root.size,
                pos=root.pos
            )

        root.bind(
            size=lambda x,y:
            setattr(self.rect,"size",y),

            pos=lambda x,y:
            setattr(self.rect,"pos",y)
        )

        # ================= CENTER =================

        center = AnchorLayout(
            anchor_x="center",
            anchor_y="center"
        )

        self.card = WhiteBox(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(20),
            size_hint=(None,None),
            size=(dp(340),dp(320))
        )

        title = Label(
            text="Employee Login",
            font_size=40,
            color=(0,0,0,1),
            size_hint=(1,None),
            height=dp(50)
        )

        # ================= ID =================

        self.emp_id = CenteredInput(
            hint_text="Employee ID"
        )

    # ================= PASSWORD =================
        
        password_box = FloatLayout(
            size_hint=(None,None),
            size=(dp(300),dp(48))
        )

        self.password = CenteredInput(
            hint_text="Password",
            password=True
        )

        self.password.pos_hint={
            "center_x":0.5,
            "center_y":0.5
        }

        show = Button(
            text="Show",
            size_hint=(None,None),
            size=(dp(55),dp(30)),
            pos_hint={
                "right":0.98,
                "center_y":0.5
            },
            background_normal="",
            background_color=(0.7,0.7,0.7,1),
            color=(0,0,0,1)
        )

        def toggle(instance):

            self.password.password = (
                not self.password.password
            )

            instance.text = (
                "Hide"
                if self.password.password == False
                else "Show"
            )

        show.bind(
            on_press=toggle
        )

        password_box.add_widget(
            self.password
        )

        password_box.add_widget(
            show
        )

        # ================= LOGIN =================

        self.login_btn = OutlineButton(
            text="LOGIN",
            size_hint=(None,None),
            size=(dp(120),dp(40)),
            font_size=20
        )

        self.login_btn.bind(
            on_press=self.login_employee
        )

        login_box = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1,None),
            height=dp(50)
        )

        login_box.add_widget(
            self.login_btn
        )

        self.card.add_widget(title)

        self.card.add_widget(
            self.emp_id
        )

        self.card.add_widget(
            password_box
        )

        self.card.add_widget(
            login_box
        )

        center.add_widget(
            self.card
        )

        root.add_widget(
            center
        )

        scroll.add_widget(
            root
        )

        self.add_widget(
            scroll
        )

        # ================= ENTER + ANIMATION =================

        self.emp_id.bind(
            on_text_validate=self.focus_password
        )

        self.password.bind(
            on_text_validate=self.press_login
        )

        self.emp_id.bind(
            focus=self.animate_form
        )

        self.password.bind(
            focus=self.animate_form
        )

    def load_day_status(self):

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT app_status
            FROM settings
            WHERE id = 1
        """)

        row = cur.fetchone()

        conn.close()

        home = self.manager.get_screen("home")

        if row and row[0] == 1:

            home.day_started = True
            home.day_btn.text = "End Day"

        else:

            home.day_started = False
            home.day_btn.text = "Start Day"
            
    # ================= ANIMATION =================

    def animate_form(self,instance,value):

        if value:

            if instance == self.password:

                Animation(
                    y=dp(220),
                    duration=0.25
                ).start(
                    self.card
                )

            else:

                Animation(
                    y=dp(200),
                    duration=0.25
                ).start(
                    self.card
                )

        else:

            Animation(
                y=dp(210),
                duration=0.25
            ).start(
                self.card
            )

    # ================= ENTER FUNCTIONS =================

    def focus_password(self,instance):

        self.password.focus=True

    def press_login(self,instance):

        self.login_employee(instance)
        self.load_day_status()
        
    # ================= LOGIN CHECK =================

    def login_employee(self, instance):

        emp_id = self.emp_id.text.strip()
        password = self.password.text.strip()

        if not emp_id or not password:
            self.popup("Fill all fields")
            return

        try:

            url = (
                f"{SUPABASE_URL}/rest/v1/employees"
                f"?employee_code=eq.{emp_id}"
                f"&select=employee_code,full_name,password_hash,map_link"
            )

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:
            self.popup(str(e))
            return

        if not data:
            self.popup("Wrong Employee ID or Password")
            return

        employee = data[0]

        if employee["password_hash"] != password:
            self.popup("Wrong Employee ID or Password")
            return

        global current_employee_db_id
        global current_employee_id
        global current_employee_name
        global current_employee_map

        current_employee_db_id = None
        current_employee_id = employee["employee_code"]
        current_employee_name = employee["full_name"]
        current_employee_map = employee.get("map_link", "")

        try:

            # download_shops()
            # download_employee_stock(current_employee_id)
            # download_settings()
            # download_daily_sales()
            # download_shop_visits(current_employee_id)
            # download_bills(current_employee_id)
            # download_bill_items()

            self.manager.current = "home"

        except Exception as e:

            self.popup(f"Download Failed\n\n{e}")
            return

        self.popup(f"Welcome {current_employee_name}")

    def popup(self,msg):


        title = Label(
            text="Login",
            color=(0,0,0,1),
            bold=True,
            font_size=dp(18),
            size_hint=(1,None),
            height=dp(40),
            halign="center",
            valign="middle"
        )


        title.bind(
            size=lambda x,y:
            setattr(
                title,
                "text_size",
                y
            )
        )

        message = Label(
            text=msg,
            color=(0,0,0,1),
            halign="center",
            valign="middle"
        )

        message.bind(
            size=lambda x,y:
            setattr(
                message,
                "text_size",
                y
            )
        )

        box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(3)
        )

        box.add_widget(title)

        box.add_widget(message)

        Popup(
            content=box,
            size_hint=(0.7,0.3),
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        ).open()
            
# ================= HOME SCREEN =================

class HomeScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        main = FloatLayout()

        root = BoxLayout(
            orientation="vertical"
        )
        
        self.day_started = False
        self.drawer_open = False

        # ================= BACKGROUND =================

        with root.canvas.before:

            Color(1,1,1,1)

            self.rect = Rectangle(
                size=root.size,
                pos=root.pos
            )

        root.bind(
            size=self.update_rect,
            pos=self.update_rect
        )

        # ================= TOP BAR =================

        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1,None),
            height=dp(55),
            padding=[10,5],
            spacing=10
        )


        menu_btn = Button(
            text="Menu",
            size_hint=(None,1),
            width=dp(50),
            background_normal="",
            background_color=(0.9,0.9,0.9,1),
            color=(0,0,0,1),
            font_size=30
        )
        
        menu_btn.bind(
            on_press=self.toggle_drawer
        )

        # ================= EMPLOYEE LABEL =================

        self.employee_label = Label(
            text="",
            color=(0,0,0,1),
            font_size=30,
            halign="center",
            valign="middle",
            size_hint=(1,1)
        )


        self.employee_label.bind(
            size=lambda x,y:
            setattr(x,"text_size",y)
        )



        # ================= LOGOUT BUTTON =================

        logout_btn = Button(
            text="Logout",
            size_hint=(None,1),
            width=dp(50),
            background_normal="",
            background_color=(0.9,0.9,0.9,1),
            color=(0,0,0,1),
            font_size=30
        )


        logout_btn.bind(
            on_press=self.logout
        )



        # ================= TOP BAR ADD =================

        top_bar.add_widget(menu_btn)


        # this keeps employee text exactly center
        top_bar.add_widget(
            self.employee_label
        )


        top_bar.add_widget(logout_btn)



        root.add_widget(top_bar)



        # ================= CENTER BUTTONS =================

        center = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            padding=[0, 0, 0, 0]
        )



        button_box = GridLayout(
            cols=1,
            spacing=dp(25),
            size_hint=(None,None),
            width=dp(300),
            height=dp(450)
        )



        # ================= BUTTON 1 =================

        btn1 = OutlineButton(
            text="Stock",
            size_hint=(None,None),
            size=(dp(300),dp(225))
        )

        btn1.bind(
            on_press=self.open_stock_issue_return
        )



        # ================= BUTTON 3 =================

        btn3 = OutlineButton(
            text="Journey",
            size_hint=(None,None),
            size=(dp(300),dp(225))
        )

        btn3.bind(
            on_press=self.open_journey
        )



        button_box.add_widget(btn1)

        button_box.add_widget(btn3)



        center.add_widget(button_box)



        root.add_widget(center)
        
        main.add_widget(root)
        
        # ================= DRAWER =================

        self.drawer = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(180),
            pos=(-dp(260), 0),
            spacing=10,
            padding=10
        )

        with self.drawer.canvas.before:
            Color(0.95,0.95,0.95,1)
            self.drawer_rect = Rectangle(
                pos=self.drawer.pos,
                size=self.drawer.size
            )

        self.drawer.bind(
            pos=self.update_drawer_rect,
            size=self.update_drawer_rect
        )

        self.day_btn = Button(
            text="Start Day",
            size_hint=(1, None),
            height=dp(50)
        )

        self.day_btn.bind(
            on_press=self.toggle_day
        )

        password_btn = Button(
            text="Change Password",
            size_hint=(1, None),
            height=dp(50)
        )

        password_btn.bind(
            on_press=self.change_password_popup 
        )
    
        self.drawer.add_widget(self.day_btn)
        self.drawer.add_widget(password_btn)

        # Spacer pushes buttons to the top
        self.drawer.add_widget(Widget())
        main.add_widget(self.drawer)  
        self.add_widget(main)
        
    def custom_popup(self, title, message, size=(0.7, 0.3)):

        title_label = Label(
            text=title,
            color=(0,0,0,1),
            bold=True,
            font_size=dp(18),
            size_hint=(1,None),
            height=dp(40),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        message_label = Label(
            text=message,
            color=(0,0,0,1),
            halign="center",
            valign="middle"
        )

        message_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        popup_content.add_widget(title_label)
        popup_content.add_widget(message_label)

        Popup(
            content=popup_content,
            size_hint=size,
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        ).open()
        
    def is_mock_location_enabled(self):

        try:
            activity = PythonActivity.mActivity

            manager = activity.getSystemService(
                Context.LOCATION_SERVICE
            )

            providers = manager.getProviders(True)

            if providers is None:
                return False

            for i in range(providers.size()):

                provider = providers.get(i)

                location = manager.getLastKnownLocation(provider)

                if location and location.isFromMockProvider():
                    return True

            return False

        except Exception:
            return False
    # ================= UPDATE BG =================

    def update_rect(self,*args):

        self.rect.size = args[0].size

        self.rect.pos = args[0].pos

    def update_drawer_rect(self, *args):

        self.drawer_rect.pos = self.drawer.pos
        self.drawer_rect.size = self.drawer.size


    def toggle_drawer(self, *args):

        if self.drawer_open:

            Animation(
                x=-self.drawer.width,
                d=0.25
            ).start(self.drawer)

            self.drawer_open = False
        else:

            Animation(
                x=0,
                d=0.25
            ).start(self.drawer)

            self.drawer_open = True

    def on_touch_down(self, touch):

        if self.drawer_open:

            if touch.x > self.drawer.width:

                self.toggle_drawer()

                return True

        return super().on_touch_down(touch)

    def goto_dashboard(self, instance):

        self.toggle_drawer()

        self.manager.current = "home"
        
    def download_kml_and_shops(self):

        if not current_employee_map:

            self.custom_popup(
                "Error",
                "No map link found."
            )
            return False

        try:

            # ---------- Extract MID ----------

            if "mid=" not in current_employee_map:

                self.custom_popup(
                    "Error",
                    "Invalid Google My Maps link."
                )
                return False

            mid = current_employee_map.split("mid=")[1].split("&")[0]

            kml_url = (
                f"https://www.google.com/maps/d/kml?mid={mid}&forcekml=1"
            )

            # ---------- Download ----------

            response = requests.get(
                kml_url,
                timeout=30
            )

            response.raise_for_status()

            # ---------- Save beside this script ----------

            script_folder = os.path.dirname(
                os.path.abspath(__file__)
            )

            kml_file = os.path.join(
                script_folder,
                f"{current_employee_id}.kml"
            )

            with open(
                kml_file,
                "wb"
            ) as f:

                f.write(response.content)

            print("KML Saved:", kml_file)

            return True

        except Exception as e:

            print(e)

            self.custom_popup(
                "Error",
                f"KML download failed.\n\n{e}"
            )

            return False
        
    def sync_employee(self):

        try:

            url = (
                f"{SUPABASE_URL}/rest/v1/employees"
                f"?employee_code=eq.{current_employee_id}"
            )

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            employees = response.json()

            if not employees:
                print("Employee not found.")
                return

            conn = get_db()
            cur = conn.cursor()

            for emp in employees:

                cur.execute("""
                    DELETE FROM employees
                    WHERE employee_code=?
                """, (
                    emp["employee_code"],
                ))

                cur.execute("""
                    INSERT INTO employees
                    (
                        employee_code,
                        password_hash,
                        full_name,
                        phone,
                        nic,
                        age,
                        map_link,
                        is_active,
                        total_shops,
                        total_bills,
                        total_units_sold,
                        total_sale,
                        created_at,
                        updated_at
                    )
                    VALUES
                    (
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )
                """, (
                    emp.get("employee_code"),
                    emp.get("password_hash"),
                    emp.get("full_name"),
                    emp.get("phone"),
                    emp.get("nic"),
                    emp.get("age"),
                    emp.get("map_link"),
                    emp.get("is_active", 1),
                    emp.get("total_shops", 0),
                    emp.get("total_bills", 0),
                    emp.get("total_units_sold", 0),
                    emp.get("total_sale", 0),
                    emp.get("created_at"),
                    emp.get("updated_at")
                ))

            conn.commit()
            conn.close()

            print("Employee synced successfully.")

        except Exception as e:

            print("Employee Sync Error:", e)
       
    def download_employee_stock(self):

        try:

            # ================= DOWNLOAD EMPLOYEE STOCK =================

            url = (
                f"{SUPABASE_URL}/rest/v1/employee_stock"
                f"?employee_code=eq.{current_employee_id}"
                f"&select="
                f"employee_code,"
                f"product_name,"
                f"variant_name,"
                f"assigned_units,"
                f"sold_units,"
                f"remaining_units,"
                f"selling_price,"
                f"created_at,"
                f"updated_at"
            )

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            stock_rows = response.json()

            # ================= SQLITE =================

            conn = get_db()
            cur = conn.cursor()

            # Remove old stock
            cur.execute(
                """
                DELETE FROM employee_stock
                WHERE employee_code=?
                """,
                (current_employee_id,)
            )

            # Insert latest stock
            for row in stock_rows:

                assigned = int(row.get("assigned_units", 0))
                sold = int(row.get("sold_units", 0))

                remaining = int(
                    row.get(
                        "remaining_units",
                        assigned - sold
                    )
                )

                cur.execute(
                    """
                    INSERT INTO employee_stock
                    (
                        employee_code,
                        product_name,
                        variant_name,
                        assigned_units,
                        sold_units,
                        remaining_units,
                        selling_price,
                        created_at,
                        updated_at
                    )
                    VALUES
                    (
                        ?,?,?,?,?,?,?,?,?
                    )
                    """,
                    (
                        row.get("employee_code"),
                        row.get("product_name"),
                        row.get("variant_name"),
                        assigned,
                        sold,
                        remaining,
                        float(row.get("selling_price", 0)),
                        row.get("created_at"),
                        row.get("updated_at")
                    )
                )

            conn.commit()
            conn.close()

            print(
                f"Employee stock synced successfully ({len(stock_rows)} records)."
            )

        except Exception as e:

            print("Employee Stock Sync Error:", e)
    
    def verify_end_day(self, instance):

        box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10
        )

        box.add_widget(Label(
            text="Enter Employee Password",
            color=(0,0,0,1)
        ))

        password = CenteredInput(
            hint_text="Enter Password",
            password=True,
            multiline=False,
            size_hint=(None, None),
            size=(dp(280), dp(30))
        )

        box.add_widget(password)

        buttons = BoxLayout(
            size_hint_y=None,
            height=45,
            spacing=10
        )

        ok = OutlineButton(text="Confirm")
        cancel = OutlineButton(text="Cancel")

        buttons.add_widget(ok)
        buttons.add_widget(cancel)

        box.add_widget(buttons)

        popup = Popup(
            title="End Day",
            content=box,
            size_hint=(None,None),
            size=(dp(350), dp(180)),
            background="",
            background_color=(1,1,1,1)
        )

        def check_password(instance):

            try:

                url = (
                    f"{SUPABASE_URL}/rest/v1/employees"
                    f"?employee_code=eq.{current_employee_id}"
                    f"&select=password_hash"
                )

                response = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=10
                )

                response.raise_for_status()

                data = response.json()

                if not data:

                    self.custom_popup(
                        "Error",
                        "Employee not found."
                    )
                    return

                if password.text.strip() != str(data[0]["password_hash"]).strip():

                    self.custom_popup(
                        "Wrong Password",
                        "Incorrect employee password."
                    )
                    return

                popup.dismiss()

                self.end_day()

                self.day_started = False
                self.day_btn.text = "Start Day"

            except Exception as e:

                print(e)

                self.custom_popup(
                    "Error",
                    str(e)
                )

        ok.bind(on_press=check_password)
        cancel.bind(on_press=lambda x: popup.dismiss())

        popup.open()
        
    def end_day(self):

        if not internet_available():

            self.custom_popup(
                "No Internet",
                "Internet connection is required to end the day."
            )
            return

        try:

            self.custom_popup(
                "Please Wait",
                "Syncing data..."
            )

            # -----------------------------------------
            # 1. Sync everything
            # -----------------------------------------

            sync_live_locations()

            sync_shops()

            sync_shop_visits()

            sync_bills()

            sync_bill_items()

            sync_daily_sales()

            sync_employee_stock()

            return_stock()

            # -----------------------------------------
            # 2. Delete employee KML
            # -----------------------------------------

            delete_local_kml()

            # -----------------------------------------
            # 3. Mark day ended
            # -----------------------------------------

            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
                UPDATE settings
                SET
                    app_status = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """)

            conn.commit()
            conn.close()

            self.custom_popup(
                "Success",
                "Day ended successfully."
            )

        except Exception as e:

            print("End Day Error:", e)

            self.custom_popup(
                "Error",
                str(e)
            )
                         
    def start_day_download(self):

        try:

            # ==========================================
            # 1. DOWNLOAD EMPLOYEE KML & SAVE SHOPS
            # ==========================================

            self.download_kml_and_shops()

            # ==========================================
            # 2. SYNC EMPLOYEE TABLE
            # ==========================================

            self.sync_employee()

            # ==========================================
            # 3. SYNC EMPLOYEE STOCK
            # ==========================================

            self.download_employee_stock()

            # ==========================================
            # 4. MARK DAY AS STARTED
            # ==========================================

            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
                UPDATE settings
                SET
                    app_status = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """)

            conn.commit()
            conn.close()

            # ==========================================
            # 5. SUCCESS
            # ==========================================

            self.custom_popup(
                "Success",
                "Day Started Successfully."
            )

        except Exception as e:

            print("Start Day Error:", e)

            self.custom_popup(
                "Error",
                str(e)
            )

    def toggle_day(self, instance):

        if not self.day_started:

            try:

                self.start_day_download()

                self.day_started = True
                self.day_btn.text = "End Day"

            except Exception as e:

                self.custom_popup("Start Day Failed", str(e))

        else:

            self.verify_end_day(instance)

        self.toggle_drawer()

    def change_password_popup(self, instance):

        # ================= TITLE =================

        title_label = Label(
            text="Change Password",
            color=(0,0,0,1),
            bold=True,
            font_size=dp(18),
            size_hint=(1,None),
            height=dp(40),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda x,y: setattr(
                x,
                "text_size",
                y
            )
        )

        # ================= INPUTS =================

        current = CenteredInput(
            hint_text="Current Password",
            password=True,
            multiline=False,
            size_hint=(None,None),
            size=(dp(200),dp(45))
        )

        new = CenteredInput(
            hint_text="New Password",
            password=True,
            multiline=False,
            size_hint=(None,None),
            size=(dp(200),dp(45))
        )

        confirm = CenteredInput(
            hint_text="Re-enter New Password",
            password=True,
            multiline=False,
            size_hint=(None,None),
            size=(dp(200),dp(45))
        )

        # ================= INPUT BOX =================

        input_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        input_box.bind(
            minimum_height=input_box.setter("height")
        )

        for widget in (current, new, confirm):

            holder = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
                size_hint=(1,None),
                height=dp(50)
            )

            holder.add_widget(widget)

            input_box.add_widget(holder)

        # ================= BUTTONS =================

        buttons = BoxLayout(
            spacing=dp(10),
            size_hint=(1,None),
            height=dp(45)
        )

        change = OutlineButton(
            text="Change"
        )

        cancel = OutlineButton(
            text="Cancel"
        )

        buttons.add_widget(change)
        buttons.add_widget(cancel)

        # ================= POPUP CONTENT =================

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        popup_content.add_widget(title_label)
        popup_content.add_widget(input_box)
        popup_content.add_widget(buttons)

        popup = Popup(
            content=popup_content,
            size_hint=(None,None),
            size=(dp(330), dp(300)),
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        )

        cancel.bind(
            on_press=popup.dismiss
        )

        # ================= CHANGE PASSWORD =================

        def change_password(instance):

            if (
                not current.text.strip()
                or not new.text.strip()
                or not confirm.text.strip()
            ):

                self.custom_popup(
                    "Error",
                    "Fill all fields."
                )

                return

            if new.text != confirm.text:

                self.custom_popup(
                    "Error",
                    "New passwords do not match."
                )

                return

            try:

                url = (
                    f"{SUPABASE_URL}/rest/v1/employees"
                    f"?employee_code=eq.{current_employee_id}"
                    f"&select=password_hash"
                )

                r = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=10
                )

                r.raise_for_status()

                data = r.json()

                if not data:

                    self.custom_popup(
                        "Error",
                        "Employee not found."
                    )

                    return

                if current.text != data[0]["password_hash"]:

                    self.custom_popup(
                        "Error",
                        "Current password is incorrect."
                    )

                    return

                response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/employees?employee_code=eq.{current_employee_id}",
                    headers=HEADERS,
                    json={
                        "password_hash": new.text
                    },
                    timeout=10
                )

                response.raise_for_status()

                popup.dismiss()

                self.custom_popup(
                    "Success",
                    "Password changed successfully."
                )

            except Exception as e:

                self.custom_popup(
                    "Error",
                    str(e)
                )

        # ================= ENTER KEY NAVIGATION =================

        def focus_new(instance):
            new.focus = True

        def focus_confirm(instance):
            confirm.focus = True

        current.bind(
            on_text_validate=focus_new
        )

        new.bind(
            on_text_validate=focus_confirm
        )

        confirm.bind(
            on_text_validate=change_password
        )

        # ================= BUTTON =================

        change.bind(
            on_press=change_password
        )

        popup.open()
        
    # ================= LOAD EMPLOYEE =================

    def on_pre_enter(self):

        self.employee_label.text = (
            f"{current_employee_id}\n{current_employee_name}"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT app_status
            FROM settings
            WHERE id = 1
        """)

        row = cur.fetchone()

        conn.close()

        if row and row[0] == 1:

            self.day_started = True
            self.day_btn.text = "End Day"

        else:

            self.day_started = False
            self.day_btn.text = "Start Day"

    # ================= BUTTON FUNCTIONS =================

    def open_stock_issue_return(self, instance):
    
        self.manager.current = "stock_issue_return"

    def open_journey(self, instance):

        if self.is_mock_location_enabled():

            self.custom_popup(
                "Access Denied",
                "Fake GPS detected.\nDisable it before opening Journey.",
                (0.6,0.3)
            )

            return

        self.manager.current = "journey"
        
    # ================= LOGOUT =================

    def logout(self,instance):

        global current_employee_db_id
        global current_employee_id
        global current_employee_name

        current_employee_db_id = None
        current_employee_id = ""
        current_employee_name = ""


        self.manager.current = "login"   

# ================= Journey Screen =================

class StockViewScreen(Screen):
    
    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.headers = [
            "S.N",
            "ITEM",
            "VAR",
            "UNITS",
            "P/U",
            "SOLD",
            "LEFT"
        ]

        main = BoxLayout(
            orientation="vertical",
            spacing=dp(5),
            padding=dp(10)
        )

        # ================= TOP BAR =================

        top_bar = BoxLayout(
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10)
        )

        back_btn = OutlineButton(
            text="Back",
            size_hint=(None, 1),
            width=dp(80)
        )

        back_btn.bind(
            on_press=self.go_back
        )

        heading = Label(
            text="Issued Stock",
            color=(0, 0, 0, 1),
            bold=True,
            font_size=dp(16)
        )

        return_btn = OutlineButton(
            text="Refresh",
            size_hint=(None, 1),
            width=dp(80)
        )

        return_btn.bind(
            on_press=self.refresh_stock
        )

        top_bar.add_widget(back_btn)
        top_bar.add_widget(Widget())      # Left spacer
        top_bar.add_widget(heading)
        top_bar.add_widget(Widget())      # Right spacer
        top_bar.add_widget(return_btn)

        # ================= HEADER =================

        header = GridLayout(
            cols=7,
            size_hint=(1,None),
            height=dp(45),
            spacing=1
        )

        for h in self.headers:

            lbl = Label(
                text=h,
                color=(1,1,1,1),
                bold=True
            )

            with lbl.canvas.before:

                Color(.15,.45,.85,1)

                rect = Rectangle(
                    pos=lbl.pos,
                    size=lbl.size
                )

            lbl.bind(
                pos=lambda i,v,r=rect:
                setattr(r,"pos",i.pos)
            )

            lbl.bind(
                size=lambda i,v,r=rect:
                setattr(r,"size",i.size)
            )

            header.add_widget(lbl)

        # ================= TABLE =================

        scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=True,
            effect_cls=ScrollEffect
        )

        self.table = GridLayout(
            cols=7,
            size_hint_y=None,
            spacing=1
        )

        self.table.bind(
            minimum_height=self.table.setter("height")
        )

        self.stock_data = []
        self.expanded_products = set()
        
        scroll.add_widget(
            self.table
        )

        # ================= SUMMARY =================

        self.summary = Label(
            text="Products: 0 || Units: 0 || Sold: 0 || Left: 0",
            size_hint=(1,None),
            height=dp(50),
            color=(0,0,0,1),
            bold=True
        )

        main.add_widget(top_bar)
        main.add_widget(header)
        main.add_widget(scroll)
        main.add_widget(self.summary)

        self.add_widget(main)

    # ================= REFRESH WHEN SCREEN OPENS =================
    def custom_popup(self, title, message, size=(0.7, 0.3)):

        title_label = Label(
            text=title,
            color=(0,0,0,1),
            bold=True,
            font_size=dp(18),
            size_hint=(1,None),
            height=dp(40),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        message_label = Label(
            text=message,
            color=(0,0,0,1),
            halign="center",
            valign="middle"
        )

        message_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        popup_content.add_widget(title_label)
        popup_content.add_widget(message_label)

        Popup(
            content=popup_content,
            size_hint=size,
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        ).open()
        
    def on_pre_enter(self):

        self.load_table()
    
    def refresh_stock(self, instance):

        try:

            self.custom_popup(
                "Please Wait",
                "Refreshing Stock..."
            )

            sync_employee_stock()

            self.load_table()

            self.custom_popup(
                "Success",
                "Stock Refreshed."
            )

        except Exception as e:

            self.custom_popup(
                "Error",
                str(e)
            )
            
    def refresh_table(self):

        self.table.clear_widgets()

        # ================= GROUP PRODUCTS =================

        products = {}

        for row in self.stock_data:

            product = row.get("product_name", "")
            products.setdefault(product, []).append(row)

        total_products = 0
        total_units = 0
        total_sold = 0
        total_left = 0

        serial = 1

        # ================= LOOP PRODUCTS =================

        for product_name, variants in products.items():

            units = sum(int(v.get("assigned_units", 0)) for v in variants)
            sold = sum(int(v.get("sold_units", 0)) for v in variants)
            left = sum(int(v.get("remaining_units", 0)) for v in variants)

            # Skip products with no assigned stock
            if units <= 0:
                continue
            
            total_products += 1
            total_units += units
            total_sold += sold
            total_left += left

            # ---------- Count REAL variants ----------

            variant_count = 0

            for v in variants:

                variant = str(v.get("variant_name", "")).strip()

                if variant not in ("", "0") and variant.lower() not in (
                    "normal",
                    product_name.lower()
                ):
                    variant_count += 1

            variant_text = "0" if variant_count == 0 else str(variant_count)

            if variant_count == 0:
                price = float(variants[0].get("selling_price", 0))
                price_text = f"{price:.0f}"
            else:
                price_text = "0"

            values = [
                str(serial),
                product_name,
                variant_text,
                str(units),
                price_text,
                str(sold),
                str(left)
            ]

            serial += 1

            # ================= PRODUCT ROW =================

            for col, value in enumerate(values):

                if col == 2:

                    cell = Button(
                        text=value,
                        background_normal="",
                        background_down="",
                        background_color=(1,1,1,0),
                        color=(0,0,0,1),
                        size_hint_y=None,
                        height=dp(40),
                        halign="center",
                        valign="middle"

                    )

                    if variant_count > 0:
                        cell.bind(
                            on_release=lambda inst, p=product_name:
                            self.toggle_product(p)
                        )

                else:

                    cell = Label(
                        text=value,
                        color=(0, 0, 0, 1),
                        size_hint_y=None,
                        height=dp(40),
                        halign="center",
                        valign="middle"
                    )

                cell.bind(
                    size=lambda inst, val:
                    setattr(inst, "text_size", (inst.width, inst.height))
                )

                with cell.canvas.before:

                    Color(1, 1, 1, 1)

                    rect = Rectangle(
                        pos=cell.pos,
                        size=cell.size
                    )

                cell.bind(
                    pos=lambda inst, val, r=rect:
                    setattr(r, "pos", inst.pos)
                )

                cell.bind(
                    size=lambda inst, val, r=rect:
                    setattr(r, "size", inst.size)
                )

                self.table.add_widget(cell)

            # ================= VARIANT ROWS =================

            if product_name in self.expanded_products:

                for row in variants:

                    variant = str(row.get("variant_name", "")).strip()

                    if variant in ("", "0") or variant.lower() in (
                        "normal",
                        product_name.lower()
                    ):
                        continue

                    price = float(row.get("selling_price", 0))

                    units = int(row.get("assigned_units", 0))
                    sold = int(row.get("sold_units", 0))
                    left = int(row.get("remaining_units", 0))

                    values = [
                        "",
                        "",
                        variant,
                        str(units),
                        f"{price:.0f}",
                        str(sold),
                        str(left)
                    ]

                    for value in values:

                        cell = Label(
                            text=value,
                            color=(0.2, 0.2, 0.2, 1),
                            size_hint_y=None,
                            height=dp(34),
                            halign="center",
                            valign="middle"
                        )

                        cell.bind(
                            size=lambda inst, val:
                            setattr(inst, "text_size", (inst.width, inst.height))
                        )

                        with cell.canvas.before:

                            Color(0.93, 0.93, 0.93, 1)

                            rect = Rectangle(
                                pos=cell.pos,
                                size=cell.size
                            )

                        cell.bind(
                            pos=lambda inst, val, r=rect:
                            setattr(r, "pos", inst.pos)
                        )

                        cell.bind(
                            size=lambda inst, val, r=rect:
                            setattr(r, "size", inst.size)
                        )

                        self.table.add_widget(cell)

        self.summary.text = (
            f"Products: {total_products}   ||   "
            f"Units: {total_units}   ||   "
            f"Sold: {total_sold}   ||   "
            f"Left: {total_left}"
        )
    # ================= LOAD TABLE =================

    def load_table(self):

        try:

            conn = get_db()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    product_name,
                    variant_name,
                    assigned_units,
                    sold_units,
                    remaining_units,
                    selling_price
                FROM employee_stock
                WHERE employee_code = ?
                ORDER BY product_name, variant_name
            """, (current_employee_id,))

            self.stock_data = [
                dict(row)
                for row in cur.fetchall()
            ]

            conn.close()

            self.refresh_table()

        except Exception as e:

            print(e)
            self.summary.text = "Unable to load stock"

    def toggle_product(self, product):
        print(product)
        if product in self.expanded_products:
            self.expanded_products.remove(product)
        else:
            self.expanded_products.add(product)

        self.refresh_table()
                      
    # ================= BACK =================

    def go_back(self, instance):

        self.manager.current = "home"
            
# ================= Journey Screen =================

class JourneyScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        
        self.mode = "map"
        self.shops = []
        self.current_lat = 0
        self.current_lon = 0

        self.map_view = None
        self.my_marker = None


        self.map_link = ""


        root = BoxLayout(
            orientation="vertical"
        )


        with root.canvas.before:

            Color(1,1,1,1)

            self.rect = Rectangle(
                size=root.size,
                pos=root.pos
            )


        root.bind(
            size=self.update_rect,
            pos=self.update_rect
        )



        top_bar = BoxLayout(
            size_hint=(1,None),
            height=dp(55),
            spacing=10,
            padding=10
        )


        back = OutlineButton(
            text="Back",
            size_hint=(None,1),
            width=90
        )

        back.bind(
            on_press=self.back_home
        )


        title = Label(
            text="Journey",
            color=(0,0,0,1),
            font_size=30,
            bold=True
        )


        top_bar.add_widget(back)
        top_bar.add_widget(title)


        root.add_widget(top_bar)



        self.switch_btn = OutlineButton(
            text="Map",
            size_hint=(None,1),
            width=90
        )

        self.switch_btn.bind(
            on_press=self.change_view
        )

        top_bar.add_widget(self.switch_btn)

        self.content = BoxLayout()

        root.add_widget(self.content)

        self.add_widget(root)
        
    def custom_popup(self, title, message, size=(0.7, 0.3)):

        title_label = Label(
            text=title,
            color=(0,0,0,1),
            bold=True,
            font_size=dp(18),
            size_hint=(1,None),
            height=dp(40),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        message_label = Label(
            text=message,
            color=(0,0,0,1),
            halign="center",
            valign="middle"
        )

        message_label.bind(
            size=lambda x, y: setattr(
                x,
                "text_size",
                y
            )
        )

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        popup_content.add_widget(title_label)
        popup_content.add_widget(message_label)

        Popup(
            content=popup_content,
            size_hint=size,
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        ).open()
    
    def load_employee_map(self):

        global current_employee_map

        self.map_link = current_employee_map

        print("Employee map:", self.map_link)

        if not self.map_link:

            self.custom_popup(
                "Map Error",
                "No map assigned to this employee",
                (0.6,0.3)
            )

            return False

        return True
    
    def on_location(self, **kwargs):

        self.current_lat = kwargs.get("lat", 0)
        self.current_lon = kwargs.get("lon", 0)

        accuracy = kwargs.get("accuracy", 0)
        speed = kwargs.get("speed", 0)

        battery = get_battery_level()     # we'll create this next

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO live_locations
            (
                employee_code,
                latitude,
                longitude,
                accuracy,
                speed,
                battery,
                updated_at,
                is_synced
            )
            VALUES
            (
                ?,?,?,?,?,?,CURRENT_TIMESTAMP,0
            )
        """,
        (
            str(current_employee_id),
            self.current_lat,
            self.current_lon,
            accuracy,
            speed,
            battery
        ))

        conn.commit()
        conn.close()

        if internet_available():
            sync_live_locations()
            
        if self.my_marker:
            self.my_marker.lat = self.current_lat
            self.my_marker.lon = self.current_lon

        if self.map_view:
            self.map_view.center_on(
                self.current_lat,
                self.current_lon
            )
            
    def start_gps(self):

        try:

            request_permissions([
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION
            ])

        except:
            pass

        try:

            gps.configure(
                on_location=self.on_location
            )

            gps.start(
                minTime=1000,
                minDistance=0
            )

        except Exception as e:

            print("GPS Error:", e)
            
    def on_pre_enter(self):

        global current_employee_map

        # refresh employee map every login
        self.map_link = current_employee_map

        self.start_gps()

        self.load_employee_map()
        
        if self.map_view:
            self.map_view.map_source = MBTilesMapSource()

        self.show_list()

    def update_rect(self,*args):

        self.rect.size=args[0].size
        self.rect.pos=args[0].pos
        
    def distance_in_meters(self, lat1, lon1, lat2, lon2):

        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dlambda / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return R * c

    def is_shop_done_today(self, shop_name):

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT shop_code
            FROM shops
            WHERE shop_name=?
            LIMIT 1
        """, (shop_name,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return False

        shop_code = row[0]

        cur.execute("""
            SELECT 1
            FROM shop_visits
            WHERE shop_code = ?
            AND DATE(visit_date)=DATE('now')
            LIMIT 1
        """, (shop_code,))

        done = cur.fetchone() is not None

        conn.close()

        return done
    
    def get_shop_visits(self, shop_name):

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT shop_code
            FROM shops
            WHERE shop_name=?
            LIMIT 1
        """, (shop_name,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return 0

        shop_code = row[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM shop_visits
            WHERE shop_code=?
        """, (shop_code,))

        total = cur.fetchone()[0]

        conn.close()

        return total
    
    # ================= MAP VIEW =================

    def show_map(self):
        
        global current_employee_map
        self.map_link = current_employee_map

        if not self.load_employee_map():
            return


        self.content.clear_widgets()

        self.mode = "map"

        self.switch_btn.text = "List"

        map_view = MapView(
            lat=24.8607,
            lon=67.0011,
            zoom=11
        )

        map_view.map_source = MBTilesMapSource()
                
        self.map_view = map_view
        
        self.my_marker = MapMarker(
            lat=self.current_lat if self.current_lat else 24.8607,
            lon=self.current_lon if self.current_lon else 67.0011,
            source="marker.png"
        )

        map_view.add_widget(
            self.my_marker
        )

        kml_data = self.get_local_kml()
        print("KML Loaded:", kml_data is not None)

        if kml_data:

            try:
                tree = ET.ElementTree(
                    ET.fromstring(kml_data)
                )
            except Exception as e:
                print("XML ERROR:", e)
                print(kml_data[:500])
                return

            root = tree.getroot()

            ns = {
                "kml":"http://www.opengis.net/kml/2.2"
            }

            count = 1

            for placemark in root.findall(
                ".//kml:Placemark",
                ns
            ):

                name = self.get_shop_name(
                    placemark,
                    ns
                )
                
                point = placemark.find(
                    ".//kml:Point/kml:coordinates",
                    ns
                )

                if point is None:
                    continue

                coords = point.text.strip().split(",")

                lon = float(coords[0])
                lat = float(coords[1])

                marker = MapMarker(
                    lat=lat,
                    lon=lon
                )



                # GREEN IF VISITED TODAY

                if self.is_shop_done_today(name):

                    with marker.canvas.before:

                        Color(
                            0,
                            1,
                            0,
                            1
                        )

                        marker.color = (
                            0,
                            1,
                            0,
                            1
                        )

                marker.bind(
                    on_release=lambda x,
                    n=name,
                    la=lat,
                    lo=lon:
                    self.shop_popup(
                        n,
                        la,
                        lo
                    )
                )

                map_view.add_widget(marker)

        self.content.add_widget(map_view)


    def get_local_kml(self):

        script_folder = os.path.dirname(os.path.abspath(__file__))

        filename = os.path.join(
            script_folder,
            f"{current_employee_id}.kml"
        )

        print("Looking for:", filename)

        if not os.path.isfile(filename):

            self.custom_popup(
                "Map Missing",
                "Please Start Day first."
            )

            return None

        try:

            with open(filename, "r", encoding="utf-8") as f:

                return f.read()

        except Exception as e:

            print(e)
            return None

    def get_shop_name(self, placemark, namespace):

        name = placemark.find(
            "kml:name",
            namespace
        )

        if name is not None and name.text:
            return name.text.strip()

        return "Unknown Shop"


    # ================= SHOP POPUP =================


    def shop_popup(self, name, lat, lon):

    # ================= CONTENT BOX =================

        box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )


        visits = self.get_shop_visits(name)


        # ================= VISITS =================

        visit_label = Label(
            text=f"Visits: {visits}",
            color=(0,0,0,1),
            font_size=18,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(35)
        )


        visit_label.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value
            )
        )



        # ================= BUTTONS =================

        direction = OutlineButton(
            text="Open Direction"
        )


        open_shop = OutlineButton(
            text="Open Shop"
        )


        shop_close = OutlineButton(
            text="Shop Close"
        )


        box.add_widget(visit_label)
        box.add_widget(direction)
        box.add_widget(open_shop)
        box.add_widget(shop_close)



        # ================= POPUP =================

        pop = Popup(
            title=name,
            content=box,
            title_align="center",     # CENTER TITLE
            size_hint=(0.7,0.38),
            background="",
            background_color=(1,1,1,1),
            title_size=dp(22),
            title_color=(0,0,0,1)
        )



        # ================= OPEN DIRECTION =================

        def open_direction(instance):

            url = (
                "https://www.google.com/maps/dir/?api=1&destination="
                + str(lat)
                + ","
                + str(lon)
            )

            webbrowser.open(url)


        direction.bind(
            on_press=open_direction
        )



        # ================= OPEN SHOP =================

        def open_shop_func(instance):
            
            distance = self.distance_in_meters(
                self.current_lat,
                self.current_lon,
                lat,
                lon
            )

            if distance > 30:

                self.custom_popup(
                    "Out of Range",
                    f"Shop is out of range.\n\nDistance: {distance:.1f} meters"
                )

                return

            if self.is_shop_done_today(name):

                self.custom_popup(
                    "Already Done",
                    "Shop already completed today.\nOpening saved bill for editing."
                )

            pop.dismiss()


            shop_screen = self.manager.get_screen(
                "shop"
            )

            shop_screen.open_shop(name)

            self.manager.current="shop"

        open_shop.bind(
            on_press=open_shop_func
        )



        shop_close.bind(
            on_press=pop.dismiss
        )



        pop.open()



    def show_list(self):
        
        global current_employee_map
        self.map_link = current_employee_map

        if not self.load_employee_map():
            return


        self.content.clear_widgets()

        self.mode = "list"

        self.switch_btn.text = "Map"

        scroll = ScrollView()

        self.rows = GridLayout(
            cols=1,
            spacing=10,
            padding=10,
            size_hint_y=None
        )

        self.rows.bind(
            minimum_height=self.rows.setter("height")
        )

        data = self.get_local_kml()

        if data:

            tree = ET.ElementTree(
                ET.fromstring(data)
            )

            root = tree.getroot()

            ns = {
                "kml":"http://www.opengis.net/kml/2.2"
            }

            count = 1

            for shop in root.findall(
                ".//kml:Placemark",
                ns
            ):

                name = self.get_shop_name(
                    shop,
                    ns
                )

                point = shop.find(
                    ".//kml:Point/kml:coordinates",
                    ns
                )

                if point is None:
                    continue

                coords = point.text.strip().split(",")

                lon = float(coords[0])
                lat = float(coords[1])

                btn = OutlineButton(
                    text=f"{count}. {name}",
                    size_hint_y=None,
                    height=dp(60)
                )


                # GREEN BUTTON IF DONE

                if self.is_shop_done_today(name):

                    btn.background_color = (
                        0,
                        1,
                        0,
                        1
                    )

                btn.bind(
                    on_press=lambda x,
                    n=name,
                    la=lat,
                    lo=lon:
                    self.shop_popup(
                        n,
                        la,
                        lo
                    )
                )

                self.rows.add_widget(btn)

                count += 1

        scroll.add_widget(self.rows)

        self.content.add_widget(scroll)
        
    def change_view(self, instance):

        if self.mode == "list":

            self.show_map()

        else:

            self.show_list()


    def back_home(self,instance):

        self.manager.current="home"
        
# ================= Shop Screen =================

class ShopScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        main = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )


        # ================= TOP BAR =================

        top_bar = BoxLayout(
            size_hint=(1,None),
            height=dp(60),
            spacing=dp(10)
        )


        back = OutlineButton(
            text="Back",
            size_hint=(None,1),
            width=dp(80)
        )


        back.bind(
            on_press=self.go_back
        )



        title = Label(
            text="Shop Visit Form",
            color=(0,0,0,1),
            bold=True,
            font_size=dp(22)
        )



        save = OutlineButton(
            text="Sell",
            size_hint=(None,1),
            width=dp(80)
        )


        save.bind(
            on_press=self.sell_bill
        )



        top_bar.add_widget(back)

        top_bar.add_widget(title)

        top_bar.add_widget(save)


        main.add_widget(top_bar)



        # ================= FORM =================


        form = BoxLayout(
            orientation="vertical",
            spacing=dp(13),
            size_hint=(1,None),
            height=dp(180)
        )


        self.shop_name = self.make_input(
            "Shop Name"
        )


        self.owner = self.make_input(
            "Owner Name"
        )
        self.owner.bind(
            on_text_validate=lambda *a: setattr(self.phone, "focus", True)
        )


        self.phone = self.make_input(
            "Phone Number",
            True
        )
        self.phone.bind(on_text_validate=self.start_navigation)



        form.add_widget(self.shop_name)
        form.add_widget(self.owner)
        form.add_widget(self.phone)


        main.add_widget(form)




        # ================= HEADER =================


        header = GridLayout(
            cols=6,
            size_hint=(1,None),
            height=dp(45),
            spacing=1
        )


        for h in [
            "SR",
            "ITEM",
            "VAR",
            "PRICE",
            "SOLD",
            "TOTAL"
        ]:


            lbl=Label(
                text=h,
                color=(1,1,1,1),
                bold=True
            )


            with lbl.canvas.before:

                Color(.15,.45,.85,1)

                rect=Rectangle(
                    pos=lbl.pos,
                    size=lbl.size
                )


            lbl.bind(
                pos=lambda i,v,r=rect:setattr(r,"pos",i.pos)
            )

            lbl.bind(
                size=lambda i,v,r=rect:setattr(r,"size",i.size)
            )


            header.add_widget(lbl)



        main.add_widget(header)




        # ================= TABLE =================


        scroll=ScrollView(
            do_scroll_x=False
        )


        self.table=GridLayout(
            cols=6,
            size_hint_y=None,
            spacing=1
        )


        self.table.bind(
            minimum_height=self.table.setter("height")
        )


        scroll.add_widget(
            self.table
        )


        main.add_widget(scroll)




        # ================= SUMMARY =================


        self.summary = Label(
            text="Entries: 0 || Units: 0",
            size_hint=(1,None),
            height=dp(50),
            color=(0,0,0,1),
            bold=True,
            halign="center",
            valign="middle"
        )

        self.summary.bind(
            size=lambda inst, val:
            setattr(
                inst,
                "text_size",
                inst.size
            )
        )


        main.add_widget(
            self.summary
        )




        # ================= SAVE =================


        self.add_widget(main)

        self.products = []
        
        self.expanded = {}

        self.shop_code = ""
        self.shop_name_value = ""

        self.edit_mode = False
        self.current_bill_id = None
        self.current_bill_no = None
        
        self.load_products()
    
        self.edit_mode = False
        self.current_bill_no = None
        self.nav_items = []
        self.current_nav = 0    
    
    def stop_gps(self):

        try:
            gps.stop()
        except:
            pass
        
    def start_navigation(self, *args):

        self.current_nav = 0

        self.refresh_table()

        self.open_next_sold()
        
    def open_next_sold(self):

        if self.current_nav >= len(self.nav_items):
            return

        product, index = self.nav_items[self.current_nav]

        row = self.products[product][index]

        # fake touch so collide_point succeeds
        class Dummy:
            pass

        touch = Dummy()
        touch.pos = (1, 1)

        class DummyWidget:
            def collide_point(self, *args):
                return True
            text = str(row[4])

        self.edit_sold(DummyWidget(), touch, product, row)
        
    def on_location(self, **kwargs):

        self.current_lat = kwargs.get("lat", 0)
        self.current_lon = kwargs.get("lon", 0)

        accuracy = kwargs.get("accuracy", 0)
        speed = kwargs.get("speed", 0)

        battery = get_battery_level()     # we'll create this next

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO live_locations
            (
                employee_code,
                latitude,
                longitude,
                accuracy,
                speed,
                battery,
                updated_at,
                is_synced
            )
            VALUES
            (
                ?,?,?,?,?,?,CURRENT_TIMESTAMP,0
            )
        """,
        (
            str(current_employee_id),
            self.current_lat,
            self.current_lon,
            accuracy,
            speed,
            battery
        ))

        conn.commit()
        conn.close()


    def start_gps(self):

        try:

            request_permissions([
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION
            ])

        except:
            pass

        try:

            gps.configure(
                on_location=self.on_location
            )

            gps.start(
                minTime=1000,
                minDistance=0
            )

        except Exception as e:

            print("GPS Error:", e)
            
    def on_pre_enter(self):
        
        self.start_gps()

        if not self.edit_mode:

            self.products = []

            self.load_products()
        
    def show_bill_preview(self, bill_no, items, total):

        # ================= TITLE =================

        title_label = Label(
            text="Bill Preview",
            color=(0,0,0,1),
            bold=True,
            font_size=dp(20),
            size_hint=(1,None),
            height=dp(45),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda inst, val:
            setattr(inst, "text_size", inst.size)
        )

        # ================= BILL TEXT =================

        shop = self.shop_name.text.strip()
        owner = self.owner.text.strip()

        text = (
            f"Shop Name: {shop}\n"
            f"Owner Name: {owner}\n"
            f"Bill No: {bill_no}\n\n\n"
        )

        for item in items:

            inventory_id = item[0]
            product = item[1]
            variant = str(item[2]).strip()
            qty = item[3]
            price = item[4]
            line_total = item[5]

            if variant and variant != "0":
                product_name = f"{product} ( {variant} )"
            else:
                product_name = product

            text += (
                f"{product_name}  {price:.0f} × {qty} = {line_total:.0f}\n"
            )

        text += f"\n\n\nTOTAL  Rs {total:.0f}"

        # ================= MESSAGE =================

        message_label = Label(
            text=text,
            color=(0,0,0,1),
            halign="center",
            valign="top"
        )

        message_label.bind(
            width=lambda inst, val:
            setattr(inst, "text_size", (val, None))
        )

        message_label.bind(
            texture_size=lambda inst, val:
            setattr(inst, "height", val[1])
        )

        # ================= CONTENT =================

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(3),
            padding=dp(10)
        )

        popup_content.add_widget(title_label)
        popup_content.add_widget(message_label)

        # ================= POPUP =================

        popup = Popup(
            content=popup_content,
            size_hint=(0.8, None),
            height=(dp(600)),
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        )

        popup.open()

    def is_shop_done_today(self, shop_name):

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT shop_code
            FROM shops
            WHERE shop_name=?
            LIMIT 1
        """, (shop_name,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return False

        shop_code = row[0]

        cur.execute("""
            SELECT 1
            FROM shop_visits
            WHERE shop_code=?
            AND DATE(created_at)=DATE('now')
            LIMIT 1
        """, (shop_code,))

        done = cur.fetchone() is not None

        conn.close()

        return done

    # ================= INPUT =================


    def make_input(self,text,phone=False):

        box=TextInput(
            hint_text=text,
            multiline=False,
            size_hint=(None,None),
            width=dp(250),
            height=dp(45),
            pos_hint={"center_x":0.5},
            font_size=30
        )


        if phone:

            box.input_filter="int"


        box.halign="center"

        box.padding=[
            0,
            dp(10)
        ]


        return box

    
    def refresh_table(self):

        self.table.clear_widgets()
        self.nav_items = []

        # Build navigation list first
        for product, variants in self.products.items():

            has_variants = any(
                v[2] and str(v[2]).strip() != "0"
                for v in variants
            )

            if has_variants:

                for i in range(len(variants)):
                    self.nav_items.append((product, i))

            else:

                self.nav_items.append((product, 0))

        total_entries = 0
        total_units = 0
        sr = 1

        for product, variants in self.products.items():

            # ================= PRODUCT ROW =================

            variant_names = [
                v[2].strip()
                for v in variants
                if v[2] and v[2].strip() != "0"
            ]

            has_variants = len(variant_names) > 0
            variant_count = len(variant_names)
            price = sum(float(v[3]) for v in variants)
            sold = sum(int(v[4]) for v in variants)
            total = sum(float(v[5]) for v in variants)

            values = [

                str(sr),

                product,

                "0" if not has_variants else str(variant_count),

                f"{price:.0f}",

                str(sold),

                f"{total:.0f}"

            ]

            for col, value in enumerate(values):

                # Variant Column
                if col == 2:

                    cell = Button(
                        text=value,
                        background_normal="",
                        background_down="",
                        background_color=(1,1,1,0),
                        color=(0,0,0,1),
                        size_hint_y=None,
                        height=dp(42)
                    )

                    if has_variants:
                        cell.bind(
                            on_release=lambda inst, p=product:
                            self.toggle_product(p)
                        )

                # SOLD column on main row (NOT editable)
                elif col == 4:

                    # Product has variants -> total only, don't edit
                    if has_variants:

                        cell = Label(
                            text=value,
                            color=(0,0,0,1),
                            size_hint_y=None,
                            height=dp(42)
                        )

                    # Product has NO variants -> allow editing here
                    else:

                        cell = Button(
                            text=value,
                            background_normal="",
                            background_down="",
                            background_color=(1,1,1,0),
                            color=(0,0,0,1),
                            size_hint_y=None,
                            height=dp(42)
                        )

                        cell.bind(
                            on_touch_down=lambda inst, touch, p=product:
                            self.edit_variant_qty(inst, touch, p, 0)
                        )
            
                else:

                    cell = Label(
                        text=value,
                        color=(0,0,0,1),
                        size_hint_y=None,
                        height=dp(42)
                    )

                with cell.canvas.before:

                    Color(1,1,1,1)

                    rect = Rectangle(
                        pos=cell.pos,
                        size=cell.size
                    )

                cell.bind(
                    pos=lambda inst, val, r=rect:
                    setattr(r, "pos", inst.pos)
                )

                cell.bind(
                    size=lambda inst, val, r=rect:
                    setattr(r, "size", inst.size)
                )

                self.table.add_widget(cell)

            total_entries += 1
            total_units += sold
            sr += 1

            # ================= VARIANT ROWS =================

            if has_variants and self.expanded[product]:

                for i, row in enumerate(variants):

                    inventory_id = row[0]
                    variant = row[2]
                    price = float(row[3])
                    sold = int(row[4])
                    total = float(row[5])

                    values = [

                        "",

                        "",

                        variant,

                        f"{price:.0f}",

                        str(sold),

                        f"{total:.0f}"

                    ]

                    for col, value in enumerate(values):

                        # Editable SOLD column
                        if col == 4:

                            cell = Button(
                                text=value,
                                background_normal="",
                                background_down="",
                                background_color=(1,1,1,0),
                                color=(0,0,0,1),
                                size_hint_y=None,
                                height=dp(38)
                            )

                            cell.bind(
                                on_touch_down=lambda inst, touch, p=product, idx=i:
                                self.edit_variant_qty(inst, touch, p, idx),
                            )                

                        else:

                            cell = Label(
                                text=value,
                                color=(0,0,0,1),
                                size_hint_y=None,
                                height=dp(38)
                            )

                        with cell.canvas.before:

                            Color(.95, .95, .95, 1)

                            rect = Rectangle(
                                pos=cell.pos,
                                size=cell.size
                            )

                        cell.bind(
                            pos=lambda inst, val, r=rect:
                            setattr(r, "pos", inst.pos)
                        )

                        cell.bind(
                            size=lambda inst, val, r=rect:
                            setattr(r, "size", inst.size)
                        )

                        self.table.add_widget(cell)

        self.summary.text = (
            f"Entries: {total_entries}   ||   Units: {total_units}"
        )
    
    def toggle_product(self, product):

        self.expanded[product] = not self.expanded[product]
        self.refresh_table()
        
    def edit_variant_qty(self, widget, touch, product, index):

        if not widget.collide_point(*touch.pos):
            return

        row = self.products[product][index]

        self.edit_sold(widget, touch, product, row)
        
    # ================= LOAD PRODUCTS =================

    def load_products(self):

        self.table.clear_widgets()

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            product_name,
            variant_name,
            selling_price,
            remaining_units
        FROM employee_stock
        WHERE employee_code=?
        AND remaining_units > 0
        """,
        (
            str(current_employee_id),
        ))

        data = cur.fetchall()
        print(data)
        conn.close()

        self.products = {}
        self.expanded = {}

        for row in data:

            inventory_id, product, variant, price, stock = row

            if product not in self.products:

                self.products[product] = []

                self.expanded[product] = False

            self.products[product].append([
                inventory_id,   # 0
                product,        # 1
                variant,        # 2
                price,          # 3
                0,              # 4 sold
                0,              # 5 total
                stock           # 6 stock
            ])

        self.refresh_table()

    def load_existing_bill(self, shop_code):

        conn = get_db()
        cur = conn.cursor()

        # ================= FIND TODAY'S BILL =================

        cur.execute("""
            SELECT
                b.id,
                b.bill_no,
                s.shop_name,
                s.owner_name,
                s.phone
            FROM bills b
            JOIN shops s
                ON b.shop_code = s.shop_code
            WHERE b.shop_code = ?
            AND DATE(b.created_at) = DATE('now')
            ORDER BY b.id DESC
            LIMIT 1
        """, (shop_code,))

        bill = cur.fetchone()

        if not bill:

            print("No bill found for shop:", shop_code)

            conn.close()
            return

        bill_id, bill_no, shop_name, owner_name, phone = bill

        print("Loading Today's Bill:", bill_no)

        self.edit_mode = True
        self.current_bill_id = bill_id
        self.current_bill_no = bill_no
        self.shop_code = shop_code

        # ================= LOAD SHOP DETAILS =================

        self.shop_name.text = shop_name
        self.owner.text = owner_name or ""
        self.phone.text = phone or ""

        # ================= LOAD PRODUCTS =================

        self.load_products()

        # ================= LOAD BILL ITEMS =================

        cur.execute("""
            SELECT
                inventory_id,
                units
            FROM bill_items
            WHERE bill_no = ?
        """, (bill_no,))

        sold_items = cur.fetchall()

        print("Bill Items:", sold_items)

        # ================= APPLY SOLD QUANTITIES =================

        for inventory_id, sold_qty in sold_items:

            found = False

            for product, variants in self.products.items():

                for row in variants:

                    if int(row[0]) == int(inventory_id):

                        row[4] = int(sold_qty)
                        row[5] = float(row[3]) * int(sold_qty)

                        print(
                            "Matched:",
                            inventory_id,
                            row[1],
                            row[2],
                            sold_qty
                        )

                        found = True
                        break

                if found:
                    break

            if not found:

                print(
                    "Inventory not found:",
                    inventory_id
                )

        conn.close()

        self.refresh_table()
    
    def get_or_create_shop(self):

        conn = get_db()
        cur = conn.cursor()

        shop_name = self.shop_name.text.strip()
        owner = self.owner.text.strip()
        phone = self.phone.text.strip()

        # Search by phone first
        if phone:

            cur.execute("""
                SELECT
                    shop_code,
                    shop_name,
                    owner_name,
                    phone
                FROM shops
                WHERE phone=?
                LIMIT 1
            """, (phone,))

            row = cur.fetchone()

            if row:

                self.shop_code = row[0]
                self.shop_name.text = row[1]
                self.owner.text = row[2] or ""
                self.phone.text = row[3] or ""
                conn.close()
                return

        # Search by shop name

        cur.execute("""
        SELECT
            shop_code,
            shop_name,
            owner_name,
            phone
        FROM shops
        WHERE shop_name=?
        LIMIT 1
        """, (shop_name,))

        row = cur.fetchone()

        if row:

            self.shop_code = row[0]

            self.shop_name.text = row[1]
            self.owner.text = row[2] or ""
            self.phone.text = row[3] or ""

            conn.close()
            return

        # Create new shop

        self.shop_code = generate_shop_code()

        cur.execute("""
        INSERT INTO shops
        (
            shop_code,
            shop_name,
            owner_name,
            phone
        )
        VALUES
        (
            ?,?,?,?
        )
        """,
        (
            self.shop_code,
            shop_name,
            owner,
            phone
        ))

        conn.commit()
        conn.close()
        
    def open_shop(self, shop_name):

        self.shop_name_value = shop_name

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT shop_code
            FROM shops
            WHERE shop_name=?
            LIMIT 1
        """, (shop_name,))

        row = cur.fetchone()

        if row:
            self.shop_code = row[0]
        else:
            self.shop_code = ""

        if self.shop_code:

            cur.execute("""
                SELECT id
                FROM bills
                WHERE shop_code=?
                AND DATE(created_at)=DATE('now')
                ORDER BY id DESC
                LIMIT 1
            """, (self.shop_code,))

            bill = cur.fetchone()

        else:

            bill = None

        conn.close()

        if bill:

            self.load_existing_bill(self.shop_code)

        else:

            self.edit_mode = False
            self.current_bill_no = None
            self.current_bill_id = None

            self.shop_name.text = shop_name
            self.owner.text = ""
            self.phone.text = ""

            self.load_products()
        
    def edit_sold(self, widget, touch, product, row):

        if not widget.collide_point(*touch.pos):
            return


        box = TextInput(
            text="" if widget.text == "0" else widget.text,
            multiline=False,
            background_color=(0.85,0.85,0.85,1),
            foreground_color=(0,0,0,1),
            cursor_color=(0,0,0,1),
            hint_text="Enter quantity",
            hint_text_color=(0.3,0.3,0.3,1),
            halign="center",
            input_filter="int",
            size_hint=(1,None),
            height=dp(30)
        )


        product = row[1]
        variant = str(row[2]).strip()

        if variant and variant != "0":
            heading = f"{product}\n{variant}"
        else:
            heading = product

        title_label = Label(
            text=f"{heading}\n\nSold Quantity",
            color=(0,0,0,1),
            bold=True,
            font_size=dp(13),
            size_hint=(1,None),
            height=dp(90),
            halign="center",
            valign="middle"
        )

        title_label.bind(
            size=lambda inst, val:
            setattr(inst, "text_size", inst.size)
        )

        popup_content = BoxLayout(
            orientation="vertical",
            spacing=dp(3),
            padding=dp(5)
        )


        popup_content.add_widget(title_label)
        popup_content.add_widget(box)



        pop = Popup(
            content=popup_content,
            size_hint=(None,None),
            size=(dp(250), dp(150)),
            background="",
            background_color=(1,1,1,1),
            separator_color=(1,1,1,1)
        )


        # auto keyboard focus
        pop.bind(
            on_open=lambda *args:
            Clock.schedule_once(
                lambda dt: setattr(box,"focus",True),
                0.1
            )
        )


        def save(instance):

            try:

                qty = int(box.text)

                stock = int(row[6])

                if qty > stock:

                    Popup(
                        title="Stock Error",
                        content=Label(
                            text=f"Only {stock} units available",
                            color=(0,0,0,1)
                        ),
                        size_hint=(0.6,0.25)
                    ).open()

                    return

                row[4] = qty

                price = float(row[3])

                row[5] = qty * price

                pop.dismiss()

                self.refresh_table()
                self.current_nav += 1
                Clock.schedule_once(lambda dt: self.open_next_sold(), 0.1)
            except:

                pass

        box.bind(
            on_text_validate=save
        )

        pop.open()

    # ================= SAVE SHOP =================

    def sell_bill(self, instance):

        shop = self.shop_name.text.strip()
        # Make sure shop exists
        self.get_or_create_shop()

        if not shop:

            Popup(
                title="Error",
                content=Label(
                    text="Enter Shop Name",
                    color=(0,0,0,1)
                ),
                size_hint=(0.6,0.25)
            ).open()

            return

        # ====================================================
        # BILL NUMBER
        # ====================================================

        if self.edit_mode:

            bill_no = self.current_bill_no

        else:

            bill_no = generate_bill_no()

        total_units = 0
        total_amount = 0

        items = []

        # ====================================================
        # COLLECT SOLD ITEMS
        # ====================================================

        for product, variants in self.products.items():

            for row in variants:

                inventory_id = row[0]
                product_name = row[1]
                variant_name = row[2]
                price = float(row[3])
                sold = int(row[4])
                total = float(row[5])

                if sold > 0:

                    items.append(
                        (
                            inventory_id,
                            product_name,
                            variant_name,
                            sold,
                            price,
                            total
                        )
                    )

                    total_units += sold
                    total_amount += total

        if not items:

            Popup(
                title="Error",
                content=Label(
                    text="No items sold",
                    color=(0,0,0,1)
                ),
                size_hint=(0.6,0.25)
            ).open()

            return

        conn = get_db()
        cur = conn.cursor()

        # ====================================================
        # EDIT EXISTING BILL
        # ====================================================

        if self.edit_mode:

            cur.execute("""
            SELECT
                inventory_id,
                units
            FROM bill_items
            WHERE bill_no=?
            """,
            (
                self.current_bill_no,
            ))

            old_items = cur.fetchall()

            # RETURN STOCK

            for inventory_id, qty in old_items:

                cur.execute("""
                UPDATE employee_stock
                SET
                    remaining_units = remaining_units + ?,
                    sold_units = sold_units - ?
                WHERE employee_code=?
                AND id=?
                """,
                (
                    qty,
                    qty,
                    str(current_employee_id),
                    inventory_id
                ))

            cur.execute("""
            DELETE FROM bill_items
            WHERE bill_no=?
            """,
            (
                self.current_bill_no,
            ))

            cur.execute("""
            DELETE FROM bills
            WHERE bill_no=?
            """,
            (
                self.current_bill_no,
            ))

        # ====================================================
        # SAVE BILL
        # ====================================================

        cur.execute("""
        INSERT INTO bills
        (
            bill_no,
            employee_code,
            shop_code,
            total_products,
            total_units,
            total_amount
        )
        VALUES
        (
            ?,?,?,?,?,?
        )
        """,
        (
            bill_no,
            str(current_employee_id),
            self.shop_code,
            len(items),
            total_units,
            total_amount
        ))

        # ====================================================
        # PART 2 STARTS HERE
        # SAVE BILL ITEMS + UPDATE STOCK
        # ====================================================

        # ====================================================
        # SAVE BILL ITEMS
        # ====================================================

        for item in items:

            inventory_id, product, variant, qty, price, total = item

            cur.execute("""
            INSERT INTO bill_items
            (
                bill_no,
                shop_code,
                inventory_id,
                product_name,
                variant_name,
                units,
                unit_price,
                total
            )
            VALUES
            (
                ?,?,?,?,?,?,?,?
            )
            """,
            (
                bill_no,
                self.shop_code,
                inventory_id,
                product,
                variant,
                qty,
                price,
                total
            ))

            # UPDATE EMPLOYEE STOCK

            cur.execute("""
            UPDATE employee_stock
            SET
                remaining_units = remaining_units - ?,
                sold_units = sold_units + ?
            WHERE employee_code = ?
            AND id = ?
            """,
            (
                qty,
                qty,
                str(current_employee_id),
                inventory_id
            ))
        
        # ====================================================
        # SAVE SHOP VISIT (ONLY NEW BILL)
        # ====================================================

        if not self.edit_mode:

            cur.execute("""
            INSERT INTO shop_visits
            (
                employee_code,
                shop_code
            )
            VALUES
            (
                ?,?
            )
            """,
            (
                str(current_employee_id),
                self.shop_code
            ))
        
        cur.execute("""
        UPDATE shops
        SET
            total_visits = (
                SELECT COUNT(*)
                FROM shop_visits
                WHERE shop_code = ?
            ),

            total_bills = (
                SELECT COUNT(*)
                FROM bills
                WHERE shop_code = ?
            ),

            total_units_sold = (
                SELECT COALESCE(SUM(units),0)
                FROM bill_items
                WHERE shop_code = ?
            ),

            total_sale = (
                SELECT COALESCE(SUM(total),0)
                FROM bill_items
                WHERE shop_code = ?
            ),

            updated_at = CURRENT_TIMESTAMP

        WHERE shop_code = ?
        """,
        (
            self.shop_code,
            self.shop_code,
            self.shop_code,
            self.shop_code,
            self.shop_code
        ))
        
        # ====================================================
        # RECALCULATE DAILY SALES
        # ====================================================

        today = datetime.now().strftime("%Y-%m-%d")

        cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(total_amount),0),
            COALESCE(SUM(total_units),0),
            COALESCE(SUM(total_products),0)
        FROM bills
        WHERE employee_code=?
        AND DATE(created_at)=?
        """,
        (
            str(current_employee_id),
            today
        ))

        daily = cur.fetchone()

        total_bills = daily[0]
        total_sale = daily[1]
        total_units = daily[2]
        total_products = daily[3]

        cur.execute("""
        INSERT INTO daily_sales
        (
            sale_date,
            employee_code,
            total_bills,
            total_sale,
            total_units,
            total_products
        )
        VALUES
        (
            ?,?,?,?,?,?
        )
        ON CONFLICT(sale_date, employee_code)
        DO UPDATE SET
            total_bills=?,
            total_sale=?,
            total_units=?,
            total_products=?
        """,
        (
            today,
            str(current_employee_id),
            total_bills,
            total_sale,
            total_units,
            total_products,

            total_bills,
            total_sale,
            total_units,
            total_products
        ))

        # ====================================================
        # COMMIT DATABASE
        # ====================================================

        conn.commit()
        conn.close()

        # ====================================================
        # SHOW BILL PREVIEW
        # ====================================================

        self.show_bill_preview(
            bill_no,
            items,
            total_amount
        )

        # ====================================================
        # RESET SCREEN
        # ====================================================

        self.edit_mode = False
        self.current_bill_no = None
        self.current_bill_id = None

        self.products = {}
        self.expanded = {}

        self.load_products()

        self.shop_code = ""
        self.shop_name_value = ""

        self.shop_name.text = ""
        self.owner.text = ""
        self.phone.text = ""

        self.summary.text = "Entries: 0   ||   Units: 0"

        self.nav_items = []
        self.current_nav = 0

        # ====================================================
        # RETURN TO JOURNEY SCREEN
        # ====================================================

        self.manager.current = "journey"
        
    def go_back(self, instance):

        self.stop_gps()

        self.manager.current = "journey"
        
# ================= APP =================


class EmployeeApp(App):

    def build(self):

        create_database()

        sm = ScreenManager()

        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(StockViewScreen(name="stock_issue_return"))
        sm.add_widget(JourneyScreen(name="journey"))
        sm.add_widget(ShopScreen(name="shop"))

        return sm


    def on_start(self):

        # every 30 seconds
        Clock.schedule_interval(self.sync_background, 60)


    def sync_background(self, dt):

        try:

            sync_all_tables()

        except Exception as e:

            print("Background Sync Error:", e)
            
if __name__=="__main__":

    EmployeeApp().run()