import mysql.connector
import logging
from datetime import datetime
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    try:
        logger.info("Establishing new database connection")
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="mr_ray",
            autocommit=False
        )
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        raise


def insert_order_item(order_id, food_item, quantity):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        # Add your actual insertion logic here
        cursor.close()
        cnx.close()
        return order_id
    except mysql.connector.Error as err:
        if 'cnx' in locals(): cnx.close()
        return -1


def insert_order_tracking(order_id, status):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)", (order_id, status))
        cnx.commit()
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        logger.error(f"Insert order tracking failed: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()


def get_total_order_price(order_id):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()[0]
        cursor.close()
        cnx.close()
        return result or 0
    except mysql.connector.Error as err:
        logger.error(f"Error fetching total order price: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def calculate_order_total(order_dict):
    """Calculate total price for an order dictionary"""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        total_price = 0

        for food_item, quantity in order_dict.items():
            cursor.execute("SELECT price FROM food_items WHERE LOWER(name) = LOWER(%s)", (food_item,))
            result = cursor.fetchone()
            if result:
                item_price = result[0]
                total_price += item_price * int(quantity)
            else:
                logger.warning(f"Item not found in menu: {food_item}")

        cursor.close()
        cnx.close()
        return total_price
    except mysql.connector.Error as err:
        logger.error(f"Error calculating order total: {err}")
        if 'cnx' in locals(): cnx.close()
        return 0


def get_next_order_id():
    """Get the next available order ID"""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT IFNULL(MAX(order_id), 0) + 1 FROM orders")
        result = cursor.fetchone()
        cursor.close()
        cnx.close()

        if result:
            next_order_id = result[0]
            logger.info(f"Next order ID: {next_order_id}")
            return next_order_id
        else:
            logger.info("Starting with order ID: 1")
            return 1

    except mysql.connector.Error as err:
        logger.error(f"Error in get_next_order_id: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def get_order_status(order_id):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        # First check if order exists in orders table
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_id = %s", (order_id,))
        order_exists = cursor.fetchone()[0] > 0

        if not order_exists:
            logger.info(f"Order {order_id} not found in orders table")
            cursor.close()
            cnx.close()
            return None

        # Then check order_tracking table
        cursor.execute("SELECT status FROM order_tracking WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()
        cursor.close()
        cnx.close()

        if result:
            return result[0]
        else:
            # If order exists but no tracking record, return default status
            logger.info(f"Order {order_id} exists but no tracking record found")
            return "in progress"

    except mysql.connector.Error as err:
        logger.error(f"Error fetching order status: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def cancel_order(order_id: int):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        # Check current status from order_tracking
        cursor.execute("SELECT status FROM order_tracking WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()

        if result:
            current_status = result[0].lower()
            if current_status in ['cancelled', 'delivered']:
                cursor.close()
                cnx.close()
                return False
            # Delete tracking first
            cursor.execute("DELETE FROM order_tracking WHERE order_id = %s", (order_id,))
        else:
            # If no tracking exists, still proceed to delete order
            pass

        # Now delete from orders table (safe after deleting tracking)
        cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        cnx.commit()

        success = cursor.rowcount > 0
        cursor.close()
        cnx.close()
        return success

    except mysql.connector.Error as err:
        logger.error(f"Cancel order error: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()
        return False

def debug_order_tables(order_id):
    """Debug function to check what's in both tables"""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        # Check orders table
        cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        orders_result = cursor.fetchall()

        # Check order_tracking table
        cursor.execute("SELECT * FROM order_tracking WHERE order_id = %s", (order_id,))
        tracking_result = cursor.fetchall()

        # Get all recent orders for debugging
        cursor.execute("SELECT DISTINCT order_id FROM orders ORDER BY order_id DESC LIMIT 10")
        recent_orders = cursor.fetchall()

        cursor.close()
        cnx.close()

        logger.info(f"Orders table for order_id {order_id}: {orders_result}")
        logger.info(f"Order_tracking table for order_id {order_id}: {tracking_result}")
        logger.info(f"Recent order IDs: {recent_orders}")

        return {
            "orders": orders_result,
            "tracking": tracking_result,
            "recent_orders": recent_orders
        }

    except mysql.connector.Error as err:
        logger.error(f"Debug query failed: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def update_menu_item(food_name, price):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("UPDATE food_items SET price = %s WHERE name = %s", (price, food_name))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except mysql.connector.Error as err:
        logger.error(f"Error updating menu item: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()
        return False


def get_next_item_id():
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT IFNULL(MAX(item_id), 0) + 1 FROM food_items")
        result = cursor.fetchone()[0]
        cursor.close()
        cnx.close()
        return result
    except mysql.connector.Error as err:
        logger.error(f"Error fetching next item ID: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def get_item_id(food_item):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT item_id FROM food_items WHERE LOWER(name) = LOWER(%s)", (food_item,))
        result = cursor.fetchone()
        cursor.close()
        cnx.close()
        if result:
            logger.info(f"Found item_id for {food_item}: {result[0]}")
            return result[0]
        else:
            logger.warning(f"No item_id found for {food_item}")
            return None
    except mysql.connector.Error as err:
        logger.error(f"Error fetching item_id: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def register_user(username, email, password):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            cnx.close()
            return -1  # Email exists
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        cnx.commit()
        cursor.close()
        cnx.close()
        return 1
    except mysql.connector.Error as err:
        logger.error(f"Registration error: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()
        return -1


def insert_reservation(customer_name, reservation_date, time):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("""
            INSERT INTO reservations (customer_name, reservation_date, time)
            VALUES (%s, %s, %s)
        """, (customer_name, reservation_date, time))
        cnx.commit()
        last_id = cursor.lastrowid
        cursor.close()
        cnx.close()
        return last_id
    except mysql.connector.Error as err:
        logger.error(f"Insert reservation error: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()
        return -1


def get_reservation(reservation_id):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)
        if reservation_id:
            cursor.execute("SELECT * FROM reservations WHERE reservation_id = %s", (reservation_id,))
        result = cursor.fetchone()
        cursor.close()
        cnx.close()
        return result
    except mysql.connector.Error as err:
        logger.error(f"Get reservation error: {err}")
        if 'cnx' in locals(): cnx.close()
        return None


def cancel_reservation(reservation_id: int):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM reservations WHERE reservation_id = %s", (reservation_id,))
        cnx.commit()
        success = cursor.rowcount > 0
        cursor.close()
        cnx.close()
        return success
    except mysql.connector.Error as err:
        logger.error(f"Cancel reservation error: {err}")
        if 'cnx' in locals():
            cnx.rollback()
            cnx.close()
        return False


if __name__ == "__main__":
    print(f"Next available order ID: {get_next_order_id()}")