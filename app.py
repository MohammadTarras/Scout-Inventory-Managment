import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import urllib.parse
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

# Set page config
st.set_page_config(
    page_title="Invoice Management System",
    page_icon="🧾",
    layout="wide"
)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
st.image("logo.jpg", width=150)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'customers' not in st.session_state:
    st.session_state.customers = []

if 'products' not in st.session_state:
    st.session_state.products = pd.DataFrame()

if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'invoices' not in st.session_state:
    st.session_state.invoices = []

if 'salesmen' not in st.session_state:
    st.session_state.salesmen = []

if 'show_payment_popup' not in st.session_state:
    st.session_state.show_payment_popup = False

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize default admin if no salesmen exist
def initialize_default_admin():
    if not st.session_state.salesmen:
        default_admin = {
            'id': 1,
            'username': ADMIN_USERNAME,
            'password': hash_password(ADMIN_PASSWORD),
            'role': 'admin',
            'name': 'Administrator',
            'created_date': datetime.now().isoformat(),
            'active': True
        }
        st.session_state.salesmen.append(default_admin)
        save_salesmen()

# Load and save functions for salesmen
def load_salesmen():
    if os.path.exists('salesmen.json'):
        try:
            with open('salesmen.json', 'r') as f:
                st.session_state.salesmen = json.load(f)
        except:
            st.session_state.salesmen = []
    initialize_default_admin()

def save_salesmen():
    with open('salesmen.json', 'w') as f:
        json.dump(st.session_state.salesmen, f)

# Login function
def login_page():
    st.title("🔐 Login to Invoice Management System")
    
    # Load salesmen data
    load_salesmen()
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        login_button = st.form_submit_button("Login", type="primary")
        
        if login_button:
            # Check against salesmen database
            hashed_password = hash_password(password)
            user = next((s for s in st.session_state.salesmen 
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

# Load customers from file
def load_customers():
    if os.path.exists('customers.json'):
        try:
            with open('customers.json', 'r') as f:
                st.session_state.customers = json.load(f)
        except:
            st.session_state.customers = []

# Save customers to file
def save_customers():
    with open('customers.json', 'w') as f:
        json.dump(st.session_state.customers, f)

# Load invoices from file
def load_invoices():
    if os.path.exists('invoices.json'):
        try:
            with open('invoices.json', 'r') as f:
                st.session_state.invoices = json.load(f)
        except:
            st.session_state.invoices = []

# Save invoices to file
def save_invoices():
    with open('invoices.json', 'w') as f:
        json.dump(st.session_state.invoices, f)

# Load products from CSV
def load_products():
    if os.path.exists('products.csv'):
        try:
            df = pd.read_csv('products.csv')
            if 'product' in df.columns and 'price' in df.columns:
                st.session_state.products = df
                return True
            else:
                st.error("CSV must contain 'product' and 'price' columns")
                return False
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return False
    return False

# Generate WhatsApp formatted invoice text
def generate_whatsapp_invoice_text(customer, cart_items, invoice_number, Paid):
        total_amount = sum(item['quantity'] * item['price'] for item in cart_items)

        # Create formatted invoice text
        # Create formatted invoice text in English (no emojis)
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

        total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
        invoice_text += f"TOTAL: ${total_amount:.2f}\n"
        invoice_text += "━━━━━━━━━━━━━━━━━━\n\n"
        invoice_text += f"*PAID: ${Paid:.2f}*\n"
        invoice_text += "━━━━━━━━━━━━━━━━━━\n\n"
        invoice_text += f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}\n\n"

        invoice_text += "Best regards,\n*The Muslim Scout - Bara ibn Malik Troop*"

        return invoice_text, total_amount

# Create WhatsApp link with formatted invoice text
def create_whatsapp_link(phone, invoice_text):
    # Clean phone number (remove non-digits)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Encode message for URL
    encoded_message = urllib.parse.quote(invoice_text)
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return whatsapp_url

def delete_invoice(invoice_number):
    """Delete an invoice from the records"""
    original_count = len(st.session_state.invoices)
    st.session_state.invoices = [inv for inv in st.session_state.invoices 
                                if inv['invoice_number'] != invoice_number]
    save_invoices()
    return len(st.session_state.invoices) < original_count

def determine_payment_status(total_amount, paid_amount):
    """Determine payment status based on amounts"""
    if paid_amount >= total_amount:
        return "مدفوعة"
    elif paid_amount > 0:
        return "مدفوعة جزئياً"
    else:
        return "غير مدفوعة"

# Save invoice record
def save_invoice_record(customer, cart_items, invoice_number, total_amount, paid_amount=None):
    if paid_amount is None:
        paid_amount = total_amount
    
    unpaid_amount = max(0, total_amount - paid_amount)
    status = determine_payment_status(total_amount, paid_amount)
    
    invoice_record = {
        'invoice_number': invoice_number,
        'customer': customer,
        'items': cart_items,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'unpaid_amount': unpaid_amount,
        'status': status,
        'date': datetime.now().isoformat(),
        'billing_date': datetime.now().isoformat(),
        'created_by': st.session_state.current_user,
        'salesman': st.session_state.current_user
    }
    
    st.session_state.invoices.append(invoice_record)
    save_invoices()
    return invoice_record

# Admin Panel Functions
def admin_panel():
    st.title("👑 Admin Panel")
    
    # Load data
    load_salesmen()
    load_invoices()
    
    # Admin tabs
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["👥 Manage Salesmen", "📊 Sales Reports", "📈 Analytics", "📥 Import Data"])
    
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
                        existing_user = next((s for s in st.session_state.salesmen 
                                            if s['username'] == new_username), None)
                        
                        if existing_user:
                            st.error("Username already exists!")
                        else:
                            new_salesman = {
                                'id': max([s['id'] for s in st.session_state.salesmen], default=0) + 1,
                                'username': new_username,
                                'password': hash_password(new_password),
                                'role': new_role,
                                'name': new_name,
                                'created_date': datetime.now().isoformat(),
                                'active': True
                            }
                            st.session_state.salesmen.append(new_salesman)
                            save_salesmen()
                            st.success(f"Salesman '{new_name}' added successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all fields")
        
        # Display existing salesmen
        st.subheader("Existing Salesmen")
        if st.session_state.salesmen:
            for salesman in st.session_state.salesmen:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{salesman['name']}**")
                        st.caption(f"Username: {salesman['username']}")
                    
                    with col2:
                        st.write(f"Role: {salesman['role'].title()}")
                        st.caption(f"Created: {datetime.fromisoformat(salesman['created_date']).strftime('%Y-%m-%d')}")
                    
                    with col3:
                        status = "🟢 Active" if salesman['active'] else "🔴 Inactive"
                        st.write(status)
                    
                    with col4:
                        if salesman['username'] != ADMIN_USERNAME:  # Can't deactivate main admin
                            action = "Deactivate" if salesman['active'] else "Activate"
                            if st.button(action, key=f"toggle_{salesman['id']}"):
                                salesman['active'] = not salesman['active']
                                save_salesmen()
                                st.rerun()
                    
                    with col5:
                        if salesman['username'] != ADMIN_USERNAME:  # Can't delete main admin
                            if st.button("🗑️", key=f"delete_{salesman['id']}"):
                                st.session_state.salesmen.remove(salesman)
                                save_salesmen()
                                st.success(f"Deleted {salesman['name']}")
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("No salesmen found.")
    
    # Tab 2: Sales Reports
    with admin_tab2:
        st.header("Sales Reports")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date())
        
        # Filter invoices by date range
        filtered_invoices = []
        for invoice in st.session_state.invoices:
            invoice_date = datetime.fromisoformat(invoice['date']).date()
            if start_date <= invoice_date <= end_date:
                filtered_invoices.append(invoice)
        
        if filtered_invoices:
            # Total sales summary
            total_sales = sum(inv['total_amount'] for inv in filtered_invoices)
            total_paid = sum(inv.get('paid_amount', inv['total_amount']) for inv in filtered_invoices)
            total_unpaid = sum(inv.get('unpaid_amount', 0) for inv in filtered_invoices)
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
            
            # Payment status breakdown
            status_counts = defaultdict(int)
            for invoice in filtered_invoices:
                status_counts[invoice.get('status', 'غير مدفوعة')] += 1
            
            if status_counts:
                st.subheader("Payment Status Breakdown")
                df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                fig_status = px.pie(df_status, values='Count', names='Status', title='Invoice Payment Status')
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Sales by day
            st.subheader("Daily Sales")
            daily_sales = defaultdict(float)
            for invoice in filtered_invoices:
                date = datetime.fromisoformat(invoice['date']).date()
                daily_sales[date] += invoice['total_amount']
            
            if daily_sales:
                df_daily = pd.DataFrame(list(daily_sales.items()), columns=['Date', 'Sales'])
                df_daily = df_daily.sort_values('Date')
                
                fig = px.line(df_daily, x='Date', y='Sales', title='Daily Sales Trend')
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig, use_container_width=True)
            
            # Sales by salesman
            st.subheader("Sales by Salesman")
            salesman_sales = defaultdict(lambda: {'total': 0, 'count': 0, 'paid': 0, 'unpaid': 0})
            for invoice in filtered_invoices:
                salesman = invoice.get('salesman', invoice.get('created_by', 'Unknown'))
                salesman_sales[salesman]['total'] += invoice['total_amount']
                salesman_sales[salesman]['paid'] += invoice.get('paid_amount', invoice['total_amount'])
                salesman_sales[salesman]['unpaid'] += invoice.get('unpaid_amount', 0)
                salesman_sales[salesman]['count'] += 1
            
            if salesman_sales:
                df_salesman = pd.DataFrame([
                    {
                        'Salesman': salesman,
                        'Total Sales': data['total'],
                        'Total Paid': data['paid'],
                        'Total Unpaid': data['unpaid'],
                        'Invoice Count': data['count'],
                        'Average Sale': data['total'] / data['count'] if data['count'] > 0 else 0
                    }
                    for salesman, data in salesman_sales.items()
                ])
                
                # Sort by total sales
                df_salesman = df_salesman.sort_values('Total Sales', ascending=False)
                
                # Display table
                st.dataframe(df_salesman, use_container_width=True)
                
                # Sales chart by salesman
                fig_bar = px.bar(df_salesman, x='Salesman', y='Total Sales', 
                               title='Sales by Salesman')
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Detailed invoice list
            st.subheader("Invoice Details")
            df_invoices = pd.DataFrame([
                {
                    'Invoice #': inv['invoice_number'],
                    'Date': datetime.fromisoformat(inv['date']).strftime('%Y-%m-%d'),
                    'Customer': inv['customer']['name'],
                    'Phone': inv['customer']['phone'],
                    'Total': f"${inv['total_amount']:.2f}",
                    'Paid': f"${inv.get('paid_amount', inv['total_amount']):.2f}",
                    'Unpaid': f"${inv.get('unpaid_amount', 0):.2f}",
                    'Status': inv.get('status', 'غير مدفوعة'),
                    'Salesman': inv.get('salesman', inv.get('created_by', 'Unknown'))
                }
                for inv in sorted(filtered_invoices, key=lambda x: x['date'], reverse=True)
            ])
            
            st.dataframe(df_invoices, use_container_width=True)
            
        else:
            st.info(f"No invoices found for the selected date range ({start_date} to {end_date})")
    
    # Tab 3: Analytics
    with admin_tab3:
        st.header("Sales Analytics")
        
        if st.session_state.invoices:
            # Top customers
            customer_sales = defaultdict(lambda: {'total': 0, 'count': 0, 'paid': 0, 'unpaid': 0})
            for invoice in st.session_state.invoices:
                customer_key = f"{invoice['customer']['name']} - {invoice['customer']['phone']}"
                customer_sales[customer_key]['total'] += invoice['total_amount']
                customer_sales[customer_key]['paid'] += invoice.get('paid_amount', invoice['total_amount'])
                customer_sales[customer_key]['unpaid'] += invoice.get('unpaid_amount', 0)
                customer_sales[customer_key]['count'] += 1
            
            # Top customers chart
            if customer_sales:
                top_customers = sorted(customer_sales.items(), 
                                     key=lambda x: x[1]['total'], reverse=True)[:10]
                
                df_top_customers = pd.DataFrame([
                    {
                        'Customer': customer,
                        'Total Sales': data['total'],
                        'Total Paid': data['paid'],
                        'Total Unpaid': data['unpaid'],
                        'Invoice Count': data['count']
                    }
                    for customer, data in top_customers
                ])
                
                st.subheader("Top 10 Customers by Sales")
                fig_customers = px.bar(df_top_customers, x='Customer', y='Total Sales',
                                     title='Top Customers by Total Sales')
                fig_customers.update_xaxes(tickangle=45)
                st.plotly_chart(fig_customers, use_container_width=True)
                
                # Customer details table
                st.dataframe(df_top_customers, use_container_width=True)
            
            # Payment analysis
            paid_invoices = [inv for inv in st.session_state.invoices if inv.get('status', '').startswith('مدفوعة')]
            unpaid_invoices = [inv for inv in st.session_state.invoices if inv.get('status', '') == 'غير مدفوعة']
            partial_invoices = [inv for inv in st.session_state.invoices if 'جزئياً' in inv.get('status', '')]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fully Paid Invoices", len(paid_invoices))
            with col2:
                st.metric("Unpaid Invoices", len(unpaid_invoices))
            with col3:
                st.metric("Partially Paid Invoices", len(partial_invoices))
        
        else:
            st.info("No sales data available for analytics")

# Main app logic
def main_app():
    # Initialize data
    load_customers()
    load_invoices()
    load_products()
    load_salesmen()
    
    # Header with user info and logout button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("🧾 Invoice Management System")
        if st.session_state.current_user:
            current_user_info = next((s for s in st.session_state.salesmen 
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
                        existing_customer = next((c for c in st.session_state.customers 
                                                if c['name'].lower() == name.lower() or c['phone'] == phone), None)
                        
                        if existing_customer:
                            st.warning("Customer with this name or phone number already exists!")
                        else:
                            customer = {
                                'id': len(st.session_state.customers) + 1,
                                'name': name,
                                'phone': phone,
                                'email': email,
                                'address': address,
                                'created_date': datetime.now().isoformat(),
                                'created_by': st.session_state.current_user
                            }
                            st.session_state.customers.append(customer)
                            save_customers()
                            st.success(f"Customer '{name}' added successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all mandatory fields (Name and Phone Number)")
            
            # Display existing customers
            if st.session_state.customers:
                st.header("Existing Customers")
                df_customers = pd.DataFrame(st.session_state.customers)
                # Display with search functionality
                search_term = st.text_input("🔍 Search customers", placeholder="Search by name or phone...")
                
                if search_term:
                    filtered_customers = [c for c in st.session_state.customers 
                                        if search_term.lower() in c['name'].lower() or 
                                           search_term in c['phone']]
                    df_customers = pd.DataFrame(filtered_customers)
                
                if not df_customers.empty:
                    st.dataframe(df_customers[['name', 'phone', 'email']], use_container_width=True)
                else:
                    st.info("No customers found matching your search.")
        
        # Tab 2: Create Invoice
        with tab2:
            st.header("Create Invoice")
            
            if st.session_state.products.empty:
                st.warning("⚠️ No products loaded. Please ensure 'products.csv' exists with 'product' and 'price' columns.")
                
                # File uploader for products
                uploaded_file = st.file_uploader("Upload Products CSV", type=['csv'])
                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        if 'product' in df.columns and 'price' in df.columns:
                            # Save uploaded file
                            df.to_csv('products.csv', index=False)
                            st.session_state.products = df
                            st.success("Products loaded successfully!")
                            st.rerun()
                        else:
                            st.error("CSV must contain 'product' and 'price' columns")
                    except Exception as e:
                        st.error(f"Error loading CSV: {str(e)}")
                
            elif not st.session_state.customers:
                st.warning("Please add at least one customer first.")
            else:
                # Select customer with search
                st.subheader("Select Customer")
                customer_search = st.text_input("🔍 Search customer", placeholder="Type name or phone...")
                
                if customer_search:
                    filtered_customers = [c for c in st.session_state.customers 
                                        if customer_search.lower() in c['name'].lower() or 
                                           customer_search in c['phone']]
                else:
                    filtered_customers = st.session_state.customers
                
                if filtered_customers:
                    customer_options = [f"{c['name']} - {c['phone']}" for c in filtered_customers]
                    selected_customer_idx = st.selectbox("Select Customer", range(len(customer_options)), 
                                                       format_func=lambda x: customer_options[x])
                    selected_customer = filtered_customers[selected_customer_idx]
                    
                    st.info(f"Creating invoice for: {selected_customer['name']} ({selected_customer['phone']})")
                    
                    # Product selection
                    st.subheader("Add Products to Invoice")
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        product_options = st.session_state.products['product'].tolist()
                        selected_product = st.selectbox("Select Product", product_options)
                    
                    with col2:
                        quantity = st.number_input("Quantity", min_value=1, value=1)
                    
                    with col3:
                        if st.button("Add to Cart"):
                            product_info = st.session_state.products[st.session_state.products['product'] == selected_product].iloc[0]
                            cart_item = {
                                'product': selected_product,
                                'price': float(product_info['price']),
                                'quantity': quantity
                            }
                            st.session_state.cart.append(cart_item)
                            st.success(f"Added {quantity}x {selected_product} to cart")
                            st.rerun()
                    
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
                                # Show payment popup
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
                                            invoice_text, amount = generate_whatsapp_invoice_text(selected_customer, st.session_state.cart, invoice_number,paid_amount)
                                            
                                            # Save invoice record with payment info
                                            invoice_record = save_invoice_record(selected_customer, st.session_state.cart, invoice_number, amount, paid_amount)
                                            
                                            st.success(f"✅ Invoice {invoice_number} created successfully!")
                                            st.success(f"💰 Payment Status: {payment_status}")
                                            
                                            
                                            # WhatsApp sharing
                                            st.markdown("### 📱 Send Invoice via WhatsApp")
                                            
                                            whatsapp_link = create_whatsapp_link(selected_customer['phone'], invoice_text)
                                            
                                            st.markdown(f"**[📱 Send via WhatsApp]({whatsapp_link})**")
                                            st.caption("Click to open WhatsApp with the formatted invoice")
                                            
                
                    
                                                
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
                display_invoices = st.session_state.invoices
            else:
                st.header("My Invoices")
                # Filter invoices for current salesman
                display_invoices = [inv for inv in st.session_state.invoices 
                                  if inv.get('created_by') == st.session_state.current_user or 
                                     inv.get('salesman') == st.session_state.current_user]
            
            if display_invoices:
                # Summary for current user/all
                total_sales = sum(inv['total_amount'] for inv in display_invoices)
                total_paid = sum(inv.get('paid_amount', inv['total_amount']) for inv in display_invoices)
                total_unpaid = sum(inv.get('unpaid_amount', 0) for inv in display_invoices)
                total_count = len(display_invoices)
                
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
                filtered_display = display_invoices
                if status_filter != "All":
                    filtered_display = [inv for inv in filtered_display 
                                      if status_filter in inv.get('status', '')]
                
                if search_invoice:
                    filtered_display = [inv for inv in filtered_display 
                                      if search_invoice.lower() in inv['customer']['name'].lower() or 
                                         search_invoice.lower() in inv['invoice_number'].lower()]
                
                for invoice in reversed(filtered_display):  # Show newest first
                    status_icon = "✅" if invoice.get('status', '').startswith('مدفوعة') else "❌" if invoice.get('status') == 'غير مدفوعة' else "⚠️"
                    
                    with st.expander(f"{status_icon} Invoice {invoice['invoice_number']} - {invoice['customer']['name']} - ${invoice['total_amount']:.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Customer:** {invoice['customer']['name']}")
                            st.write(f"**Phone:** {invoice['customer']['phone']}")
                            st.write(f"**Date:** {datetime.fromisoformat(invoice['date']).strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**Total:** ${invoice['total_amount']:.2f}")
                            st.write(f"**Paid:** ${invoice.get('paid_amount', invoice['total_amount']):.2f}")
                            st.write(f"**Unpaid:** ${invoice.get('unpaid_amount', 0):.2f}")
                            st.write(f"**Status:** {invoice.get('status', 'غير مدفوعة')}")
                            if st.session_state.user_role == 'admin':
                                st.write(f"**Salesman:** {invoice.get('salesman', invoice.get('created_by', 'Unknown'))}")
                        
                        with col2:
                            st.write("**Items:**")
                            for item in invoice['items']:
                                st.write(f"- {item['product']}: {item['quantity']} × ${item['price']:.2f} = ${item['quantity'] * item['price']:.2f}")
                        
                        # Delete invoice button (Admin only or own invoices)
                        can_delete = (st.session_state.user_role == 'admin' or 
                                      invoice.get('created_by') == st.session_state.current_user or 
                                      invoice.get('salesman') == st.session_state.current_user)

                        if can_delete:
                            col_resend, col_delete = st.columns(2)
                            
                            with col_resend:
                                if st.button(f"📱 Resend via WhatsApp", key=f"resend_{invoice['invoice_number']}"):
                                    invoice_text, _ = generate_whatsapp_invoice_text(
                                        invoice['customer'], 
                                        invoice['items'], 
                                        invoice['invoice_number'],
                                        invoice['paid_amount']
                                    )
                                    whatsapp_link = create_whatsapp_link(invoice['customer']['phone'], invoice_text)
                                    st.markdown(f"[📱 Open WhatsApp]({whatsapp_link})")
                            
                            with col_delete:
                                if st.button(f"🗑️ Delete Invoice", key=f"delete_{invoice['invoice_number']}", type="secondary"):
                                    if st.session_state.get(f"confirm_delete_{invoice['invoice_number']}", False):
                                        if delete_invoice(invoice['invoice_number']):
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
                                invoice_text, _ = generate_whatsapp_invoice_text(
                                    invoice['customer'], 
                                    invoice['items'], 
                                    invoice['invoice_number']
                                )
                                whatsapp_link = create_whatsapp_link(invoice['customer']['phone'], invoice_text)
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