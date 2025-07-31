from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
import logging
from pydantic import BaseModel
import hashlib
from datetime import datetime

app = FastAPI()
inprogress_orders = {}

logging.basicConfig(level=logging.DEBUG)


class User(BaseModel):
    username: str
    email: str
    password: str


class Reservation(BaseModel):
    customer_name: str
    email: str
    phone: str
    reservation_datetime: str
    party_size: int


@app.post("/")
async def handle_request(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        logging.debug(f"Received request: {payload}")

        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        output_contexts = payload['queryResult'].get('outputContexts', [])

        if not output_contexts:
            return JSONResponse(content={"fulfillmentText": "Session not found. Please start a new order."})

        session_id = generic_helper.extract_session_id(output_contexts[0]["name"])
        print(session_id)

        intent_handler_dict = {
            'order.add - context: ongoing-order': add_to_order,
            'order.remove - context: ongoing-order': remove_from_order,
            'order.cancel - context: cancel-order': cancel_order,
            'track.order - context: ongoing-tracking': track_order,
            'book_reservation': handle_reservation_booking,
            'check_reservation': handle_reservation_check,
            'cancel_reservation': handle_reservation_cancel
        }

        if intent == 'order.complete - context: ongoing-order':
            return await complete_order(parameters, session_id, background_tasks)

        # if intent == 'order.cancel - context: cancel-order':
        #     return JSONResponse(content={"fulfillmentText": "I didn't understand that request."})

        if intent in intent_handler_dict:
            return intent_handler_dict[intent](parameters, session_id)

        logging.info(f"Intent not handled: {intent}, Parameters: {parameters}, Contexts: {output_contexts}")
        return JSONResponse(content={"fulfillmentText": "I 't understand that request."})

    except KeyError as e:
        logging.error(f"KeyError: {e}")
        return JSONResponse(content={"fulfillmentText": f"KeyError: {e}"})

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return JSONResponse(content={"fulfillmentText": "An unexpected error occurred. Please try again later."})


def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        return JSONResponse(content={"fulfillmentText": "Please specify food items and quantities clearly."})

    new_food_dict = dict(zip(food_items, quantities))

    if session_id in inprogress_orders:
        inprogress_orders[session_id].update(new_food_dict)
    else:
        inprogress_orders[session_id] = new_food_dict

    order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
    return JSONResponse(content={"fulfillmentText": f"So far, you have: {order_str}. Do you need anything else?"})


def cancel_order(parameters: dict, session_id: str):
    logging.info("Processing order cancellation")
    try:
        order_id = parameters.get("number")
        if not order_id:
            return JSONResponse(content={"fulfillmentText": "Please provide your order ID to cancel the order."})

        try:
            order_id = int(order_id)
        except ValueError:
            return JSONResponse(content={"fulfillmentText": "Invalid order ID. Please provide a valid number."})

        # Use the database function to cancel the order
        success = db_helper.cancel_order(order_id)

        if success:
            return JSONResponse(content={"fulfillmentText": f"✅ Order #{order_id} has been successfully canceled."})
        else:
            return JSONResponse(content={
                "fulfillmentText": f"Unable to cancel order #{order_id}. Order may not exist or has already been delivered/cancelled."})

    except Exception as e:
        logging.error(f"Error in cancel_order: {e}")
        return JSONResponse(content={"fulfillmentText": "An error occurred while trying to cancel your order."})
# def cancel_order(parameters: dict, session_id: str ):
#     logging.info("hello cancel")
#     try:
#         order_id = parameters.get("number")
#         if not order_id:
#             return JSONResponse(content={"fulfillmentText": "Please provide your order ID to cancel the order."})
#
#         try:
#             order_id = int(order_id)
#         except ValueError:
#             return JSONResponse(content={"fulfillmentText": "Invalid order ID. Please provide a valid number."})
#
#         # MOCKED RESPONSE: Always say it's canceled
#         return JSONResponse(content={"fulfillmentText": f"✅ Order #{order_id} has been successfully canceled."})
#
#     except Exception as e:
#         logging.error(f"Error in cancel_order: {e}")
#         return JSONResponse(content={"fulfillmentText": "An error occurred while trying to cancel your order (mocked)."})


def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(
            content={"fulfillmentText": "I'm having trouble finding your order. Please place a new order."})

    food_items = parameters.get("food-item", [])
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    fulfillment_text = ""
    if removed_items:
        fulfillment_text += f"Removed {', '.join(removed_items)} from your order!"
    if no_such_items:
        fulfillment_text += f" Your current order does not contain {', '.join(no_such_items)}."
    if not current_order:
        fulfillment_text += " Your order is now empty!"
        del inprogress_orders[session_id]
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what remains in your order: {order_str}."

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


async def complete_order(parameters: dict, session_id: str, background_tasks: BackgroundTasks):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having trouble finding your order. Please start a new one."
        })

    order = inprogress_orders[session_id]

    # Get next order ID
    order_id = db_helper.get_next_order_id()
    if order_id is None:
        return JSONResponse(content={
            "fulfillmentText": "Oops! Couldn't generate order ID. Please try again later."
        })

    # Calculate total price for this order
    total_price = db_helper.calculate_order_total(order)
    if total_price == 0:
        return JSONResponse(content={
            "fulfillmentText": "Error calculating order total. Please check your items and try again."
        })

    # Immediately return to Dialogflow
    response = JSONResponse(content={
        "fulfillmentText": f"Got it! Your order is being processed. Order ID: #{order_id}. Total: ${total_price:.2f}"
    })

    # Offload to background task
    background_tasks.add_task(process_order_background, order, order_id, session_id)
    return response


async def process_order_background(order: dict, order_id: int, session_id: str):
    try:

        # Save order to database
        save_result = save_to_db(order, order_id)

        # Insert order tracking first
        db_helper.insert_order_tracking(order_id, "in progress")



        if "error" in save_result:
            logging.error(f"Failed to save order {order_id}: {save_result['error']}")
        else:
            logging.info(f"Order #{order_id} saved successfully")

    except Exception as e:
        logging.error(f"Background task failed for order {order_id}: {str(e)}")
    finally:
        # Clean up session
        if session_id in inprogress_orders:
            del inprogress_orders[session_id]


def save_to_db(order: dict, order_id: int):
    cnx = None
    cursor = None
    try:
        cnx = db_helper.get_db_connection()
        cursor = cnx.cursor()

        for food_item, quantity in order.items():
            cursor.execute("SELECT item_id, price FROM food_items WHERE LOWER(name) = LOWER(%s)", (food_item,))
            result = cursor.fetchone()

            if not result:
                logging.error(f"Item not found: {food_item}")
                return {"error": f"Item {food_item} not found"}

            item_id, price = result
            total_price = price * int(quantity)
            cursor.execute("INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                           (order_id, item_id, quantity, total_price))

        cnx.commit()
        return {"success": True}

    except Exception as e:
        logging.error(f"Database save failed: {str(e)}")
        if cnx:
            cnx.rollback()
        return {"error": str(e)}
    finally:
        if cursor: cursor.close()
        if cnx: cnx.close()


def track_order(parameters: dict, session_id: str):
    # Try different parameter names that Dialogflow might use
    order_id = parameters.get('order_id') or parameters.get('number') or parameters.get('item_id')

    if not order_id:
        return JSONResponse(content={"fulfillmentText": "Please provide your order ID to track your order."})

    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return JSONResponse(content={"fulfillmentText": "Invalid order ID provided. Please provide a valid number."})

    # Debug: Check what's in the database
    debug_info = db_helper.debug_order_tables(order_id)
    logging.info(f"Debug info for order {order_id}: {debug_info}")

    order_status = db_helper.get_order_status(order_id)
    if order_status:
        return JSONResponse(
            content={"fulfillmentText": f"The order status for order ID #{order_id} is: {order_status}."})

    return JSONResponse(content={
        "fulfillmentText": f"No order found with order ID #{order_id}. Please check your order ID and try again."})


def handle_reservation_booking(parameters: dict, session_id: str):
    try:
        customer_name = parameters.get("given-name")
        time_str = parameters.get("time")
        time = datetime.fromisoformat(time_str.replace("Z", "")).time()
        date = parameters.get("date")
        reservation_date = datetime.fromisoformat(date.replace("Z", "")).date()

        if not all([customer_name, reservation_date, time]):
            print(customer_name, reservation_date, time)
            return JSONResponse(content={
                "fulfillmentText": "Missing reservation details. Please provide customer_name, email, phone, reservation_datetime, party_size ."})

        reservation_id = db_helper.insert_reservation(customer_name, reservation_date, time)

        if reservation_id == -1:
            return JSONResponse(content={"fulfillmentText": "Failed to book reservation. Please try again."})
        return JSONResponse(
            content={"fulfillmentText": f"Reservation confirmed! Your reservation ID is {reservation_id}."})
    except Exception as e:
        logging.error(f"Error booking reservation: {e}")
        return JSONResponse(content={"fulfillmentText": "An error occurred while booking the reservation."})


def handle_reservation_check(parameters: dict, session_id: str):
    try:
        ID = parameters.get("id")
        if not ID:
            return JSONResponse(content={"fulfillmentText": "Please provide your id to check reservation."})

        reservation = db_helper.get_reservation(ID)
        if not reservation:
            return JSONResponse(content={"fulfillmentText": "No reservation found for the provided id."})

        res_date = reservation['reservation_date']
        time = reservation['time']
        customer_name = reservation['customer_name']

        return JSONResponse(content={
            "fulfillmentText": f"Your reservation is on {res_date} at {time}, under the name {customer_name}."
        })
    except Exception as e:
        logging.error(f"Error checking reservation: {e}")
        return JSONResponse(content={"fulfillmentText": "An error occurred while checking your reservation."})


def handle_reservation_cancel(parameters: dict, session_id: str):
    try:
        reservation_id = parameters.get("id")
        if not reservation_id:
            return JSONResponse(content={"fulfillmentText": "Please provide your reservation ID to cancel it."})

        success = db_helper.cancel_reservation(int(reservation_id))
        if success:
            return JSONResponse(content={"fulfillmentText": "Your reservation has been canceled successfully."})
        return JSONResponse(content={"fulfillmentText": "No reservation found with the provided ID."})
    except Exception as e:
        logging.error(f"Error canceling reservation: {e}")
        return JSONResponse(content={"fulfillmentText": "An error occurred while canceling your reservation."})


@app.post("/register")
async def register_user(user: User):
    try:
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        result = db_helper.register_user(user.username, user.email, hashed_password)
        if result == 1:
            return {"message": "User registered successfully"}
        return {"error": "Email already exists or failed to register"}
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return {"error": "Something went wrong during registration"}


@app.get("/")
async def root():
    return {"message": "Welcome to the chatbot API!"}