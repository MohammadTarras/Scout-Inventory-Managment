
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib
import plotly.express as px
from collections import defaultdict
from supabase import create_client, Client
import json

# Set page config
st.set_page_config(
    page_title="Invoice Management System",
    page_icon="🧾",
    layout="wide"
)

# Supabase configuration
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    # You need to set these in Streamlit secrets or environment variables
    SUPABASE_URL = 'https://jwuzkrrmbzglhigaabqj.supabase.co' # Your Supabase project URL
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3dXprcnJtYnpnbGhpZ2FhYnFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY3ODUzMjUsImV4cCI6MjA3MjM2MTMyNX0.aH6eHn6QsNr-laZ4NCPLocm-quGAfPAnyuqSHi8CDiw"

    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Supabase client
supabase: Client = init_supabase()

# Add logo if exists
try:
    st.image("logo.jpg", width=150)
except:
    pass

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'show_payment_popup' not in st.session_state:
    st.session_state.show_payment_popup = False

# Database Functions
class DatabaseManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    # Salesmen operations
    def get_salesmen(self):
        """Get all salesmen from database"""
        try:
            response = self.supabase.table('salesmen').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching salesmen: {e}")
            return []
    
    def add_salesman(self, salesman_data):
        """Add new salesman to database"""
        try:
            response = self.supabase.table('salesmen').insert(salesman_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error adding salesman: {e}")
            return None
    
    def update_salesman(self, salesman_id, updates):
        """Update salesman in database"""
        try:
            response = self.supabase.table('salesmen').update(updates).eq('id', salesman_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error updating salesman: {e}")
            return None
    
    def delete_salesman(self, salesman_id):
        """Delete salesman from database"""
        try:
            response = self.supabase.table('salesmen').delete().eq('id', salesman_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting salesman: {e}")
            return False
    
    # Customer operations
    def get_customers(self):
        """Get all customers from database"""
        try:
            response = self.supabase.table('customers').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching customers: {e}")
            return []
    
    def add_customer(self, customer_data):
        """Add new customer to database"""
        try:
            response = self.supabase.table('customers').insert(customer_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error adding customer: {e}")
            return None
    
    def get_customer_by_id(self, customer_id):
        """Get customer by ID"""
        try:
            response = self.supabase.table('customers').select('*').eq('id', customer_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error fetching customer: {e}")
            return None
    
    # Invoice operations
    def get_invoices(self, created_by=None):
        """Get invoices from database with optional filter by creator"""
        try:
            query = self.supabase.table('invoices').select('*, customers(*)')
            if created_by:
                query = query.eq('created_by', created_by)
            response = query.execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching invoices: {e}")
            return []
    
    def add_invoice(self, invoice_data):
        """Add new invoice to database"""
        try:
            response = self.supabase.table('invoices').insert(invoice_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error adding invoice: {e}")
            return None
    
    def delete_invoice(self, invoice_number):
        """Delete invoice from database"""
        try:
            response = self.supabase.table('invoices').delete().eq('invoice_number', invoice_number).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting invoice: {e}")
            return False
    
    # Invoice items operations
    def get_invoice_items(self, invoice_id):
        """Get items for a specific invoice"""
        try:
            response = self.supabase.table('invoice_items').select('*').eq('invoice_id', invoice_id).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching invoice items: {e}")
            return []
    
    def add_invoice_items(self, items_data):
        """Add multiple invoice items"""
        try:
            response = self.supabase.table('invoice_items').insert(items_data).execute()
            return response.data
        except Exception as e:
            st.error(f"Error adding invoice items: {e}")
            return []
    
    # Products operations
    def get_products(self, active_only=True):
        """Get products from database"""
        try:
            query = self.supabase.table('products').select('*')
            if active_only:
                query = query.eq('active', True)
            response = query.order('product').execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching products: {e}")
            return []
    
    def add_product(self, product_data):
        """Add new product to database"""
        try:
            response = self.supabase.table('products').insert(product_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error adding product: {e}")
            return None
    
    def update_product(self, product_id, updates):
        """Update product in database"""
        try:
            updates['updated_date'] = datetime.now().isoformat()
            response = self.supabase.table('products').update(updates).eq('id', product_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error updating product: {e}")
            return None
    
    def delete_product(self, product_id):
        """Soft delete product (set active=false)"""
        try:
            response = self.supabase.table('products').update({
                'active': False,
                'updated_date': datetime.now().isoformat()
            }).eq('id', product_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting product: {e}")
            return False
    
    def bulk_add_products(self, products_list):
        """Add multiple products at once"""
        try:
            response = self.supabase.table('products').insert(products_list).execute()
            return response.data
        except Exception as e:
            st.error(f"Error bulk adding products: {e}")
            return []

# Initialize database manager
db = DatabaseManager(supabase)

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize default admin if no salesmen exist
def initialize_default_admin():
    salesmen = db.get_salesmen()
    if not salesmen:
        default_admin = {
            'username': ADMIN_USERNAME,
            'password': hash_password(ADMIN_PASSWORD),
            'role': 'admin',
            'name': 'Administrator',
            'created_date': datetime.now().isoformat(),
            'active': True
        }
        db.add_salesman(default_admin)

# Login function
def login_page():
    st.title("🔐 Login to Invoice Management System")
    
    # Initialize default admin
    initialize_default_admin()
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        login_button = st.form_submit_button("Login", type="primary")
        
        if login_button:
            # Check against salesmen database
            hashed_password = hash_password(password)
            salesmen = db.get_salesmen()
            user = next((s for s in salesmen 
                        if s['username'] == username and s['password'] == hashed_password and s['active']), None)
            
            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = user['username']
                st.session_state.user_role = user['role']
                st.success(f"Login successful! Welcome {user['name']}")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
    
    st.markdown("---")
    st.markdown("*Secure Invoice Management System*")

# Load products from database
def load_products():
    """Load products from database"""
    try:
        products = db.get_products()
        if products:
            df = pd.DataFrame(products)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading products: {e}")
        return pd.DataFrame()

# Load products from CSV and save to database
def load_products_from_csv(csv_file_path=None, uploaded_file=None):
    """Load products from CSV file and save to database"""
    try:
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
        elif csv_file_path:
            df = pd.read_csv(csv_file_path)
        else:
            return False, "No file provided"
        
        if 'product' not in df.columns or 'price' not in df.columns:
            return False, "CSV must contain 'product' and 'price' columns"
        
        # Prepare products for database insertion
        products_to_add = []
        existing_products = db.get_products(active_only=False)
        existing_product_names = [p['product'].lower() for p in existing_products]
        
        added_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            product_name = str(row['product']).strip()
            
            # Skip if product already exists
            if product_name.lower() in existing_product_names:
                skipped_count += 1
                continue
            
            product_data = {
                'product': product_name,
                'price': float(row['price'])
            }
            products_to_add.append(product_data)
            added_count += 1
        
        if products_to_add:
            result = db.bulk_add_products(products_to_add)
            if result:
                return True, f"Successfully added {added_count} products. Skipped {skipped_count} duplicates."
            else:
                return False, "Failed to add products to database"
        else:
            return True, f"No new products to add. Skipped {skipped_count} existing products."
            
    except Exception as e:
        return False, f"Error processing CSV: {str(e)}"

# Generate WhatsApp formatted invoice text
def generate_whatsapp_invoice_text(customer, cart_items, invoice_number, paid):
    total_amount = sum(item['quantity'] * item['price'] for item in cart_items)

    # Create formatted invoice text
    invoice_text = f"""*Thank you for visiting the Third Stationery Exhibition*

*INVOICE #{invoice_number}*
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

*BILL TO*
━━━━━━━━━━━━━━━━━━
Name: {customer['name']}
Phone: {customer['phone']}"""

    if customer.get('email'):
        invoice_text += f"\nEmail: {customer['email']}"
    if customer.get('address'):
        invoice_text += f"\nAddress: {customer['address']}"

    invoice_text += "\n\n*ITEMS*\n━━━━━━━━━━━━━━━━━━\n"

    for i, item in enumerate(cart_items, 1):
        item_total = item['quantity'] * item['price']
        invoice_text += f"{i}. {item['product']}\n"
        invoice_text += f"   Qty: {item['quantity']} × ${item['price']:.2f}\n"
        invoice_text += f"   Subtotal: ${item_total:.2f}\n\n"

    invoice_text += "━━━━━━━━━━━━━━━━━━\n"
    invoice_text += f"TOTAL: ${total_amount:.2f}\n"
    invoice_text += "━━━━━━━━━━━━━━━━━━\n\n"
    invoice_text += f"*PAID: ${paid:.2f}*\n"
    invoice_text += "━━━━━━━━━━━━━━━━━━\n\n"
    invoice_text += f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}\n\n"
    invoice_text += "Best regards,\n*The Muslim Scout - Bara ibn Malik Troop*"

    return invoice_text, total_amount

# Create WhatsApp link with formatted invoice text
def create_whatsapp_link(phone, invoice_text):
    clean_phone = ''.join(filter(str.isdigit, phone))
    encoded_message = urllib.parse.quote(invoice_text)
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    return whatsapp_url

def determine_payment_status(total_amount, paid_amount):
    """Determine payment status based on amounts"""
    if paid_amount >= total_amount:
        return "مدفوعة"
    elif paid_amount > 0:
        return "مدفوعة جزئياً"
    else:
        return "غير مدفوعة"

# Save invoice record to database
def save_invoice_record(customer, cart_items, invoice_number, total_amount, paid_amount=None):
    if paid_amount is None:
        paid_amount = total_amount
    
    unpaid_amount = max(0, total_amount - paid_amount)
    status = determine_payment_status(total_amount, paid_amount)
    
    # Prepare invoice data
    invoice_data = {
        'invoice_number': invoice_number,
        'customer_id': customer['id'],
        'total_amount': float(total_amount),
        'paid_amount': float(paid_amount),
        'unpaid_amount': float(unpaid_amount),
        'status': status,
        'date': datetime.now().date().isoformat(),
        'billing_date': datetime.now().date().isoformat(),
        'created_by': st.session_state.current_user,
        'salesman': st.session_state.current_user
    }
    
    # Add invoice to database
    invoice_record = db.add_invoice(invoice_data)
    
    if invoice_record:
        # Add invoice items
        invoice_items = []
        for item in cart_items:
            item_data = {
                'invoice_id': invoice_record['id'],
                'product': item['product'],
                'price': float(item['price']),
                'quantity': int(item['quantity'])
            }
            invoice_items.append(item_data)
        
        db.add_invoice_items(invoice_items)
    
    return invoice_record

# Admin Panel Functions
def admin_panel():
    st.title("👑 Admin Panel")
    
    # Admin tabs
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["👥 Manage Salesmen", "📦 Manage Products", "📊 Sales Reports", "📈 Analytics"])
    
    # Tab 1: Manage Salesmen
    with admin_tab1:
        st.header("Salesmen Management")
        
        # Add new salesman
        with st.expander("➕ Add New Salesman", expanded=False):
            with st.form("add_salesman_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username", placeholder="Enter username")
                    new_name = st.text_input("Full Name", placeholder="Enter full name")
                
                with col2:
                    new_password = st.text_input("Password", type="password", placeholder="Enter password")
                    new_role = st.selectbox("Role", ["salesman", "admin"])
                
                submitted = st.form_submit_button("Add Salesman")
                
                if submitted:
                    if new_username and new_password and new_name:
                        # Check if username already exists
                        salesmen = db.get_salesmen()
                        existing_user = next((s for s in salesmen if s['username'] == new_username), None)
                        
                        if existing_user:
                            st.error("Username already exists!")
                        else:
                            new_salesman = {
                                'username': new_username,
                                'password': hash_password(new_password),
                                'role': new_role,
                                'name': new_name,
                                'created_date': datetime.now().isoformat(),
                                'active': True
                            }
                            result = db.add_salesman(new_salesman)
                            if result:
                                st.success(f"Salesman '{new_name}' added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add salesman")
                    else:
                        st.error("Please fill in all fields")
        
        # Display existing salesmen
        st.subheader("Existing Salesmen")
        salesmen = db.get_salesmen()
        
        if salesmen:
            for salesman in salesmen:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{salesman['name']}**")
                        st.caption(f"Username: {salesman['username']}")
                    
                    with col2:
                        st.write(f"Role: {salesman['role'].title()}")
                        created_date = datetime.fromisoformat(salesman['created_date']).strftime('%Y-%m-%d')
                        st.caption(f"Created: {created_date}")
                    
                    with col3:
                        status = "🟢 Active" if salesman['active'] else "🔴 Inactive"
                        st.write(status)
                    
                    with col4:
                        if salesman['username'] != ADMIN_USERNAME:
                            action = "Deactivate" if salesman['active'] else "Activate"
                            if st.button(action, key=f"toggle_{salesman['id']}"):
                                updates = {'active': not salesman['active']}
                                if db.update_salesman(salesman['id'], updates):
                                    st.rerun()
                    
                    with col5:
                        if salesman['username'] != ADMIN_USERNAME:
                            if st.button("🗑️", key=f"delete_{salesman['id']}"):
                                if db.delete_salesman(salesman['id']):
                                    st.success(f"Deleted {salesman['name']}")
                                    st.rerun()
                    
                    st.divider()
        else:
            st.info("No salesmen found.")
    
    # Tab 2: Manage Products
    with admin_tab2:
        st.header("Products Management")
        
        # Upload CSV section
        with st.expander("📤 Upload Products from CSV", expanded=False):
            st.markdown("""
            **CSV Format Requirements:**
            - Required columns: `product`, `price`
            - Optional columns: `category`, `description`
            - Products with duplicate names will be skipped
            """)
            
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file is not None:
                # Preview uploaded data
                try:
                    preview_df = pd.read_csv(uploaded_file)
                    st.subheader("Preview of uploaded data:")
                    st.dataframe(preview_df.head(), use_container_width=True)
                    
                    if st.button("Import Products to Database", type="primary"):
                        success, message = load_products_from_csv(uploaded_file=uploaded_file)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}")
        
        # Add single product section
        with st.expander("➕ Add Single Product", expanded=False):
            with st.form("add_product_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_product_name = st.text_input("Product Name *", placeholder="Enter product name")
                    new_product_price = st.number_input("Price *", min_value=0.01, step=0.01, format="%.2f")
                
                with col2:
                    new_product_category = st.text_input("Category (Optional)", placeholder="Enter category")
                    new_product_description = st.text_area("Description (Optional)", placeholder="Enter description")
                
                submitted = st.form_submit_button("Add Product")
                
                if submitted:
                    if new_product_name and new_product_price:
                        # Check if product already exists
                        existing_products = db.get_products(active_only=False)
                        existing_product = next((p for p in existing_products 
                                              if p['product'].lower() == new_product_name.lower()), None)
                        
                        if existing_product:
                            st.error("Product with this name already exists!")
                        else:
                            product_data = {
                                'product': new_product_name.strip(),
                                'price': float(new_product_price),
                                'category': new_product_category.strip() if new_product_category.strip() else None,
                                'description': new_product_description.strip() if new_product_description.strip() else None,
                                'active': True,
                                'created_date': datetime.now().isoformat()
                            }
                            
                            result = db.add_product(product_data)
                            if result:
                                st.success(f"Product '{new_product_name}' added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add product")
                    else:
                        st.error("Please fill in product name and price")
        
        # Display and manage existing products
        st.subheader("Existing Products")
        products = db.get_products(active_only=False)
        
        if products:
            # Search and filter
            col1, col2 = st.columns(2)
            with col1:
                search_product = st.text_input("🔍 Search products", placeholder="Search by name or category...")
            with col2:
                show_inactive = st.checkbox("Show inactive products", value=False)
            
            # Apply filters
            filtered_products = products
            if not show_inactive:
                filtered_products = [p for p in filtered_products if p['active']]
            
            if search_product:
                filtered_products = [p for p in filtered_products 
                                   if search_product.lower() in p['product'].lower() or 
                                      (p['category'] and search_product.lower() in p['category'].lower())]
            
            if filtered_products:
                # Summary stats
                total_products = len(filtered_products)
                active_products = len([p for p in filtered_products if p['active']])
                avg_price = sum(p['price'] for p in filtered_products) / len(filtered_products) if filtered_products else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Products", total_products)
                with col2:
                    st.metric("Active Products", active_products)
                with col3:
                    st.metric("Average Price", f"${avg_price:.2f}")
                
                st.divider()
                
                # Products table with actions
                for product in sorted(filtered_products, key=lambda x: x['product']):
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 2, 1, 1, 1])
                        
                        with col1:
                            status_icon = "✅" if product['active'] else "❌"
                            st.write(f"{status_icon} **{product['product']}**")
                            if product['category']:
                                st.caption(f"Category: {product['category']}")
                        
                        with col2:
                            st.write(f"${product['price']:.2f}")
                        
                        with col3:
                            if product['description']:
                                st.caption(product['description'][:50] + "..." if len(product['description']) > 50 else product['description'])
                        
                        with col4:
                            # Edit price button
                            edit_key = f"edit_{product['id']}"
                            if st.button("✏️", key=edit_key, help="Edit price"):
                                st.session_state[f"editing_{product['id']}"] = True
                        
                        with col5:
                            # Toggle active/inactive
                            action = "Deactivate" if product['active'] else "Activate"
                            if st.button(action, key=f"toggle_{product['id']}"):
                                updates = {'active': not product['active']}
                                if db.update_product(product['id'], updates):
                                    st.rerun()
                        
                        with col6:
                            # Delete button (soft delete)
                            if product['active']:
                                if st.button("🗑️", key=f"delete_{product['id']}"):
                                    if db.delete_product(product['id']):
                                        st.success(f"Product '{product['product']}' deactivated")
                                        st.rerun()
                        
                        # Inline edit form
                        if st.session_state.get(f"editing_{product['id']}", False):
                            with st.form(f"edit_form_{product['id']}"):
                                col_price, col_category, col_desc, col_save, col_cancel = st.columns([1, 2, 2, 1, 1])
                                
                                with col_price:
                                    new_price = st.number_input("Price", 
                                                              value=float(product['price']), 
                                                              min_value=0.01, 
                                                              step=0.01, 
                                                              format="%.2f",
                                                              key=f"price_{product['id']}")
                                
                                with col_category:
                                    new_category = st.text_input("Category", 
                                                               value=product['category'] or '', 
                                                               key=f"cat_{product['id']}")
                                
                                with col_desc:
                                    new_description = st.text_input("Description", 
                                                                   value=product['description'] or '', 
                                                                   key=f"desc_{product['id']}")
                                
                                with col_save:
                                    save_changes = st.form_submit_button("💾")
                                
                                with col_cancel:
                                    cancel_edit = st.form_submit_button("❌")
                                
                                if save_changes:
                                    updates = {
                                        'price': float(new_price),
                                        'category': new_category.strip() if new_category.strip() else None,
                                        'description': new_description.strip() if new_description.strip() else None
                                    }
                                    
                                    if db.update_product(product['id'], updates):
                                        st.success("Product updated successfully!")
                                        del st.session_state[f"editing_{product['id']}"]
                                        st.rerun()
                                    else:
                                        st.error("Failed to update product")
                                
                                elif cancel_edit:
                                    del st.session_state[f"editing_{product['id']}"]
                                    st.rerun()
                        
                        st.divider()
            else:
                st.info("No products found matching your search criteria.")
        else:
            st.info("No products found. Upload a CSV file or add products manually.")
    
    # Tab 3: Sales Reports
    with admin_tab3:
        st.header("Sales Reports")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date())
        
        # Get invoices from database
        invoices = db.get_invoices()
        
        # Filter invoices by date range
        filtered_invoices = []
        for invoice in invoices:
            invoice_date = datetime.fromisoformat(invoice['date']).date()
            if start_date <= invoice_date <= end_date:
                filtered_invoices.append(invoice)
        
        if filtered_invoices:
            # Total sales summary
            total_sales = sum(inv['total_amount'] for inv in filtered_invoices)
            total_paid = sum(inv['paid_amount'] for inv in filtered_invoices)
            total_unpaid = sum(inv['unpaid_amount'] for inv in filtered_invoices)
            total_invoices = len(filtered_invoices)
            avg_sale = total_sales / total_invoices if total_invoices > 0 else 0
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sales", f"${total_sales:.2f}")
            with col2:
                st.metric("Total Paid", f"${total_paid:.2f}")
            with col3:
                st.metric("Total Unpaid", f"${total_unpaid:.2f}")
            with col4:
                st.metric("Average Sale", f"${avg_sale:.2f}")
            
            # Display invoice details
            st.subheader("Invoice Details")
            df_invoices = pd.DataFrame([
                {
                    'Invoice #': inv['invoice_number'],
                    'Date': inv['date'],
                    'Customer': inv['customers']['name'],
                    'Phone': inv['customers']['phone'],
                    'Total': f"${inv['total_amount']:.2f}",
                    'Paid': f"${inv['paid_amount']:.2f}",
                    'Unpaid': f"${inv['unpaid_amount']:.2f}",
                    'Status': inv['status'],
                    'Salesman': inv['salesman']
                }
                for inv in sorted(filtered_invoices, key=lambda x: x['date'], reverse=True)
            ])
            
            st.dataframe(df_invoices, use_container_width=True)
            
        else:
            st.info(f"No invoices found for the selected date range ({start_date} to {end_date})")

# Main app logic
def main_app():
    products = load_products()
    
    # Header with user info and logout button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("🧾 Invoice Management System")
        if st.session_state.current_user:
            salesmen = db.get_salesmen()
            current_user_info = next((s for s in salesmen 
                                    if s['username'] == st.session_state.current_user), None)
            if current_user_info:
                st.caption(f"Logged in as: {current_user_info['name']} ({st.session_state.user_role.title()})")
    
    with col2:
        if st.session_state.user_role == 'admin':
            if st.button("👑 Admin Panel"):
                st.session_state.show_admin = not st.session_state.get('show_admin', False)
                st.rerun()
    
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.user_role = None
            st.session_state.show_admin = False
            st.rerun()
    
    # Show admin panel if admin and requested
    if st.session_state.user_role == 'admin' and st.session_state.get('show_admin', False):
        admin_panel()
    else:
        # Regular app tabs
        if st.session_state.user_role == 'admin':
            tab1, tab2, tab3 = st.tabs(["👥 Add Customer", "🛒 Create Invoice", "📋 Invoice History"])
        else:
            tab1, tab2, tab3 = st.tabs(["👥 Add Customer", "🛒 Create Invoice", "📋 My Invoices"])
        
        # Tab 1: Add Customer
        with tab1:
            st.header("Add New Customer")
            
            with st.form("customer_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Customer Name *", placeholder="Enter customer name")
                
                with col2:
                    phone = st.text_input("Phone Number *", placeholder="Enter phone number")
                
                email = st.text_input("Email (Optional)", placeholder="Enter email address")
                address = st.text_area("Address (Optional)", placeholder="Enter customer address")
                
                submitted = st.form_submit_button("Add Customer")
                
                if submitted:
                    if name and phone:
                        # Check if customer already exists
                        customers = db.get_customers()
                        existing_customer = next((c for c in customers 
                                                if c['name'].lower() == name.lower() or c['phone'] == phone), None)
                        
                        if existing_customer:
                            st.warning("Customer with this name or phone number already exists!")
                        else:
                            # Get next ID
                            customer_ids = [c['id'] for c in customers] if customers else [0]
                            next_id = max(customer_ids) + 1
                            
                            customer = {
                                'id': next_id,
                                'name': name,
                                'phone': phone,
                                'email': email,
                                'address': address,
                                'created_date': datetime.now().isoformat(),
                                'created_by': st.session_state.current_user
                            }
                            result = db.add_customer(customer)
                            if result:
                                st.success(f"Customer '{name}' added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add customer")
                    else:
                        st.error("Please fill in all mandatory fields (Name and Phone Number)")
            
            # Display existing customers
            customers = db.get_customers()
            if customers:
                st.header("Existing Customers")
                
                # Search functionality
                search_term = st.text_input("🔍 Search customers", placeholder="Search by name or phone...")
                
                if search_term:
                    filtered_customers = [c for c in customers 
                                        if search_term.lower() in c['name'].lower() or 
                                           search_term in c['phone']]
                else:
                    filtered_customers = customers
                
                if filtered_customers:
                    df_customers = pd.DataFrame(filtered_customers)
                    st.dataframe(df_customers[['name', 'phone', 'email']], use_container_width=True)
                else:
                    st.info("No customers found matching your search.")
        
        # Tab 2: Create Invoice
        with tab2:
            st.header("Create Invoice")
            
            # Load products from database
            products = db.get_products()
            
            if not products:
                st.warning("⚠️ No products found in database.")
                
                if st.session_state.user_role == 'admin':
                    st.info("👑 Go to Admin Panel > Manage Products to add products.")
                else:
                    st.info("Please contact your administrator to add products.")
                
                # File uploader for products (admin only)
                if st.session_state.user_role == 'admin':
                    st.markdown("### Quick Upload")
                    uploaded_file = st.file_uploader("Upload Products CSV", type=['csv'])
                    if uploaded_file is not None:
                        success, message = load_products_from_csv(uploaded_file=uploaded_file)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                customers = db.get_customers()
                
                if not customers:
                    st.warning("Please add at least one customer first.")
                else:
                    # Select customer with search
                    st.subheader("Select Customer")
                    customer_search = st.text_input("🔍 Search customer", placeholder="Type name or phone...")
                    
                    if customer_search:
                        filtered_customers = [c for c in customers 
                                            if customer_search.lower() in c['name'].lower() or 
                                               customer_search in c['phone']]
                    else:
                        filtered_customers = customers
                    
                    if filtered_customers:
                        customer_options = [f"{c['name']} - {c['phone']}" for c in filtered_customers]
                        selected_customer_idx = st.selectbox("Select Customer", range(len(customer_options)), 
                                                           format_func=lambda x: customer_options[x])
                        selected_customer = filtered_customers[selected_customer_idx]
                        
                        st.info(f"Creating invoice for: {selected_customer['name']} ({selected_customer['phone']})")
                        
                        # Product selection
                        st.subheader("Add Products to Invoice")
                        
                        # Search products
                        product_search = st.text_input("🔍 Search products", placeholder="Search by name or category...")
                        
                        if product_search:
                            filtered_products = [p for p in products 
                                               if product_search.lower() in p['product'].lower() or 
                                                  (p['category'] and product_search.lower() in p['category'].lower())]
                        else:
                            filtered_products = products
                        
                        if filtered_products:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                # Show product with category if available
                                product_options = []
                                for p in filtered_products:
                                    display_name = f"{p['product']}"
                                    if p['category']:
                                        display_name += f" ({p['category']})"
                                    product_options.append(display_name)
                                
                                selected_product_idx = st.selectbox("Select Product", range(len(product_options)), 
                                                                   format_func=lambda x: product_options[x])
                                selected_product_data = filtered_products[selected_product_idx]
                            
                            with col2:
                                quantity = st.number_input("Quantity", min_value=1, value=1)
                            
                            with col3:
                                st.write(f"Price: ${selected_product_data['price']:.2f}")
                                if st.button("Add to Cart"):
                                    cart_item = {
                                        'product': selected_product_data['product'],
                                        'price': float(selected_product_data['price']),
                                        'quantity': quantity
                                    }
                                    st.session_state.cart.append(cart_item)
                                    st.success(f"Added {quantity}x {selected_product_data['product']} to cart")
                                    st.rerun()
                        else:
                            st.info("No products found matching your search.")
                        
                        # Display cart
                        if st.session_state.cart:
                            st.subheader("Invoice Items")
                            
                            # Display cart with remove option
                            for i, item in enumerate(st.session_state.cart):
                                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                                
                                with col1:
                                    st.text(item['product'])
                                with col2:
                                    st.text(f"${item['price']:.2f}")
                                with col3:
                                    st.text(str(item['quantity']))
                                with col4:
                                    st.text(f"${item['price'] * item['quantity']:.2f}")
                                with col5:
                                    if st.button("Remove", key=f"remove_{i}"):
                                        st.session_state.cart.pop(i)
                                        st.rerun()
                            
                            # Total
                            total_amount = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
                            st.subheader(f"Total: ${total_amount:.2f}")
                            
                            # Generate invoice
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("🧾 Create Invoice", type="primary"):
                                    st.session_state.show_payment_popup = True

                            with col2:
                                if st.button("🗑️ Clear Cart"):
                                    st.session_state.cart = []
                                    st.rerun()

                            # Payment popup
                            if st.session_state.get('show_payment_popup', False):
                                with st.container():
                                    st.markdown("### 💰 Set Payment Amount")
                                    with st.form("payment_form"):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.write(f"**Total Amount: ${total_amount:.2f}**")
                                            paid_amount = st.number_input(
                                                "Amount Paid", 
                                                min_value=0.0, 
                                                max_value=float(total_amount), 
                                                value=float(total_amount),
                                                step=0.01,
                                                format="%.2f"
                                            )
                                        
                                        with col2:
                                            payment_status = determine_payment_status(total_amount, paid_amount)
                                            st.write(f"**Status:** {payment_status}")
                                            if paid_amount < total_amount:
                                                st.write(f"**Remaining:** ${total_amount - paid_amount:.2f}")
                                        
                                        col_confirm, col_cancel = st.columns(2)
                                        
                                        with col_confirm:
                                            confirm_create = st.form_submit_button("✅ Confirm & Create Invoice", type="primary")
                                        
                                        with col_cancel:
                                            cancel_create = st.form_submit_button("❌ Cancel")
                                        
                                        if confirm_create:
                                            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                            
                                            try:
                                                # Generate WhatsApp formatted invoice text
                                                invoice_text, amount = generate_whatsapp_invoice_text(selected_customer, st.session_state.cart, invoice_number, paid_amount)
                                                
                                                # Save invoice record with payment info
                                                invoice_record = save_invoice_record(selected_customer, st.session_state.cart, invoice_number, amount, paid_amount)
                                                
                                                if invoice_record:
                                                    st.success(f"✅ Invoice {invoice_number} created successfully!")
                                                    st.success(f"💰 Payment Status: {payment_status}")
                                                    
                                                    # WhatsApp sharing
                                                    st.markdown("### 📱 Send Invoice via WhatsApp")
                                                    whatsapp_link = create_whatsapp_link(selected_customer['phone'], invoice_text)
                                                    st.markdown(f"**[📱 Send via WhatsApp]({whatsapp_link})**")
                                                    st.caption("Click to open WhatsApp with the formatted invoice")
                                                    
                                                    # Clear cart and popup
                                                    st.session_state.cart = []
                                                    st.session_state.show_payment_popup = False
                                                    st.rerun()
                                                else:
                                                    st.error("Failed to create invoice")
                                                    
                                            except Exception as e:
                                                st.error(f"Error creating invoice: {str(e)}")
                                        
                                        elif cancel_create:
                                            st.session_state.show_payment_popup = False
                                            st.rerun()
                        
                        else:
                            st.info("Cart is empty. Add some products to create an invoice.")
                    else:
                        st.info("No customers found. Please add customers first.")
        
        # Tab 3: Invoice History
        with tab3:
            if st.session_state.user_role == 'admin':
                st.header("All Invoices History")
                invoices = db.get_invoices()
            else:
                st.header("My Invoices")
                invoices = db.get_invoices(created_by=st.session_state.current_user)
            
            if invoices:
                # Summary for current user/all
                total_sales = sum(inv['total_amount'] for inv in invoices)
                total_paid = sum(inv['paid_amount'] for inv in invoices)
                total_unpaid = sum(inv['unpaid_amount'] for inv in invoices)
                total_count = len(invoices)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Sales", f"${total_sales:.2f}")
                with col2:
                    st.metric("Total Paid", f"${total_paid:.2f}")
                with col3:
                    st.metric("Total Unpaid", f"${total_unpaid:.2f}")
                with col4:
                    st.metric("Total Invoices", total_count)
                
                st.divider()
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.selectbox("Filter by Status", 
                                               ["All", "مدفوعة", "غير مدفوعة", "مدفوعة جزئياً"])
                with col2:
                    search_invoice = st.text_input("🔍 Search invoices", 
                                                 placeholder="Search by customer name or invoice number...")
                
                # Apply filters
                filtered_invoices = invoices
                if status_filter != "All":
                    filtered_invoices = [inv for inv in filtered_invoices 
                                      if status_filter in inv['status']]
                
                if search_invoice:
                    filtered_invoices = [inv for inv in filtered_invoices 
                                      if search_invoice.lower() in inv['customers']['name'].lower() or 
                                         search_invoice.lower() in inv['invoice_number'].lower()]
                
                for invoice in reversed(filtered_invoices):  # Show newest first
                    status_icon = "✅" if invoice['status'].startswith('مدفوعة') else "❌" if invoice['status'] == 'غير مدفوعة' else "⚠️"
                    
                    with st.expander(f"{status_icon} Invoice {invoice['invoice_number']} - {invoice['customers']['name']} - ${invoice['total_amount']:.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Customer:** {invoice['customers']['name']}")
                            st.write(f"**Phone:** {invoice['customers']['phone']}")
                            st.write(f"**Date:** {invoice['date']}")
                            st.write(f"**Total:** ${invoice['total_amount']:.2f}")
                            st.write(f"**Paid:** ${invoice['paid_amount']:.2f}")
                            st.write(f"**Unpaid:** ${invoice['unpaid_amount']:.2f}")
                            st.write(f"**Status:** {invoice['status']}")
                            if st.session_state.user_role == 'admin':
                                st.write(f"**Salesman:** {invoice['salesman']}")
                        
                        with col2:
                            st.write("**Items:**")
                            # Get invoice items from database
                            invoice_items = db.get_invoice_items(invoice['id'])
                            for item in invoice_items:
                                st.write(f"- {item['product']}: {item['quantity']} × ${item['price']:.2f} = ${item['quantity'] * item['price']:.2f}")
                        
                        # Action buttons
                        can_delete = (st.session_state.user_role == 'admin' or 
                                     invoice['created_by'] == st.session_state.current_user or 
                                     invoice['salesman'] == st.session_state.current_user)

                        if can_delete:
                            col_resend, col_delete = st.columns(2)
                            
                            with col_resend:
                                if st.button(f"📱 Resend via WhatsApp", key=f"resend_{invoice['invoice_number']}"):
                                    # Reconstruct cart items for WhatsApp message
                                    cart_items = []
                                    for item in invoice_items:
                                        cart_items.append({
                                            'product': item['product'],
                                            'price': item['price'],
                                            'quantity': item['quantity']
                                        })
                                    
                                    invoice_text, _ = generate_whatsapp_invoice_text(
                                        invoice['customers'], 
                                        cart_items, 
                                        invoice['invoice_number'],
                                        invoice['paid_amount']
                                    )
                                    whatsapp_link = create_whatsapp_link(invoice['customers']['phone'], invoice_text)
                                    st.markdown(f"[📱 Open WhatsApp]({whatsapp_link})")
                            
                            with col_delete:
                                if st.button(f"🗑️ Delete Invoice", key=f"delete_{invoice['invoice_number']}", type="secondary"):
                                    if st.session_state.get(f"confirm_delete_{invoice['invoice_number']}", False):
                                        if db.delete_invoice(invoice['invoice_number']):
                                            st.success(f"Invoice {invoice['invoice_number']} deleted successfully!")
                                            # Clear confirmation state
                                            if f"confirm_delete_{invoice['invoice_number']}" in st.session_state:
                                                del st.session_state[f"confirm_delete_{invoice['invoice_number']}"]
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete invoice")
                                    else:
                                        st.session_state[f"confirm_delete_{invoice['invoice_number']}"] = True
                                        st.rerun()
                                
                                # Show confirmation message
                                if st.session_state.get(f"confirm_delete_{invoice['invoice_number']}", False):
                                    st.warning("⚠️ Click Delete Invoice again to confirm deletion")
                        else:
                            # Original resend button for non-deletable invoices
                            if st.button(f"📱 Resend via WhatsApp", key=f"resend_{invoice['invoice_number']}"):
                                # Reconstruct cart items for WhatsApp message
                                cart_items = []
                                invoice_items = db.get_invoice_items(invoice['id'])
                                for item in invoice_items:
                                    cart_items.append({
                                        'product': item['product'],
                                        'price': item['price'],
                                        'quantity': item['quantity']
                                    })
                                
                                invoice_text, _ = generate_whatsapp_invoice_text(
                                    invoice['customers'], 
                                    cart_items, 
                                    invoice['invoice_number'],
                                    invoice['paid_amount']
                                )
                                whatsapp_link = create_whatsapp_link(invoice['customers']['phone'], invoice_text)
                                st.markdown(f"[📱 Open WhatsApp]({whatsapp_link})")
            else:
                if st.session_state.user_role == 'admin':
                    st.info("No invoices created yet.")
                else:
                    st.info("You haven't created any invoices yet.")
        
        # Footer
        st.markdown("---")
        st.markdown("*Invoice Management System - Secure & Professional*")

# Main application entry point
if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()