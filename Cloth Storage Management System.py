import mysql.connector
from mysql.connector import Error

# Establish connection to MySQL database
def connect_to_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="nagasri@2004"
        )
    except Error as e:
        print(f"Error: {e}")
        return None

# Function to create the database and table if they do not exist
def initialize_db():
    db = connect_to_db()
    if db is None:
        return
    try:
        with db.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS cloth_storage")
            cursor.execute("USE cloth_storage")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clothes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    type VARCHAR(255),
                    quantity INT,
                    size VARCHAR(255)
                )
            """)
            db.commit()
    except Error as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Establish connection to the cloth_storage database
def connect_to_cloth_storage_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="nagasri@2004",
            database="cloth_storage"
        )
    except Error as e:
        print(f"Error: {e}")
        return None

# Function to add new cloth
def add_cloth(name, cloth_type, quantity, size):
    db = connect_to_cloth_storage_db()
    if db is None:
        return
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO clothes (name, type, quantity, size) VALUES (%s, %s, %s, %s)"
            values = (name, cloth_type, quantity, size)
            cursor.execute(sql, values)
            db.commit()
            print("## Cloth Added ##")
    except Error as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Function to view all clothes
def view_clothes():
    db = connect_to_cloth_storage_db()
    if db is None:
        return
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM clothes")
            results = cursor.fetchall()
            print(f"{'ID':<5} {'NAME':<20} {'TYPE':<10} {'QUANTITY':<10} {'SIZE':<5}")
            for cloth in results:
                print(f"{cloth[0]:<5} {cloth[1]:<20} {cloth[2]:<10} {cloth[3]:<10} {cloth[4]:<5}")
    except Error as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Function to update cloth quantity
def update_cloth_quantity(cloth_id, new_quantity):
    db = connect_to_cloth_storage_db()
    if db is None:
        return
    try:
        with db.cursor() as cursor:
            sql = "UPDATE clothes SET quantity = %s WHERE id = %s"
            values = (new_quantity, cloth_id)
            cursor.execute(sql, values)
            db.commit()
            print("## Cloth Quantity Updated ##")
    except Error as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Function to delete a cloth
def delete_cloth(cloth_id):
    db = connect_to_cloth_storage_db()
    if db is None:
        return
    try:
        with db.cursor() as cursor:
            sql = "DELETE FROM clothes WHERE id = %s"
            values = (cloth_id,)
            cursor.execute(sql, values)
            db.commit()
            print("## Cloth Deleted ##")
    except Error as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Interactive menu
def main():
    initialize_db()
    choice = None
    while choice != 0:
        print("1. ADD CLOTH")
        print("2. VIEW CLOTHES")
        print("3. UPDATE CLOTH QUANTITY")
        print("4. DELETE CLOTH")
        print("0. EXIT")
        try:
            choice = int(input("Enter Choice: "))
        except ValueError:
            print("## INVALID INPUT ## Please enter a number.")
            continue
        
        if choice == 1:
            name = input("Enter Cloth Name: ")
            cloth_type = input("Enter Cloth Type: ")
            try:
                quantity = int(input("Enter Quantity: "))
            except ValueError:
                print("## INVALID INPUT ## Please enter a valid quantity.")
                continue
            size = input("Enter Size: ")
            add_cloth(name, cloth_type, quantity, size)
        
        elif choice == 2:
            view_clothes()
        
        elif choice == 3:
            try:
                cloth_id = int(input("Enter Cloth ID: "))
                new_quantity = int(input("Enter New Quantity: "))
            except ValueError:
                print("## INVALID INPUT ## Please enter valid IDs and quantities.")
                continue
            update_cloth_quantity(cloth_id, new_quantity)
        
        elif choice == 4:
            try:
                cloth_id = int(input("Enter Cloth ID: "))
            except ValueError:
                print("## INVALID INPUT ## Please enter a valid ID.")
                continue
            delete_cloth(cloth_id)
        
        elif choice == 0:
            print("## Bye!! ##")
        
        else:
            print("## INVALID CHOICE ##")

if __name__ == "__main__":
    main()
