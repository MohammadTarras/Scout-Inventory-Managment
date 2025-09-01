import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from fpdf import FPDF
import urllib.parse
import tempfile
import shutil
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
def generate_whatsapp_invoice_text(customer, cart_items, invoice_number):
    total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
    
    # Create formatted invoice text
    invoice_text = f"""🧾 *INVOICE #{invoice_number}*
📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

👤 *BILL TO:*
📋 Name: {customer['name']}
📞 Phone: {customer['phone']}"""
    
    if customer.get('email'):
        invoice_text += f"\n📧 Email: {customer['email']}"
    
    if customer.get('address'):
        invoice_text += f"\n📍 Address: {customer['address']}"
    
    invoice_text += "\n\n📦 *ITEMS:*\n"
    invoice_text += "─" * 40 + "\n"
    
    for i, item in enumerate(cart_items, 1):
        item_total = item['quantity'] * item['price']
        invoice_text += f"{i}. {item['product']}\n"
        invoice_text += f"   Qty: {item['quantity']} × ${item['price']:.2f} = ${item_total:.2f}\n\n"
    
    invoice_text += "─" * 40 + "\n"
    invoice_text += f"💰 *TOTAL AMOUNT: ${total_amount:.2f}*\n"
    invoice_text += "─" * 40 + "\n\n"
    invoice_text += "🙏 Thank you for your business!\n"
    invoice_text += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
    
    return invoice_text, total_amount

# Generate PDF invoice
def generate_pdf_invoice(customer, cart_items, invoice_number):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'INVOICE', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    
    # Invoice header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Invoice #: {invoice_number}', 0, 1)
    pdf.cell(0, 10, f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
    pdf.ln(10)
    
    # Customer details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Bill To:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Name: {customer["name"]}', 0, 1)
    pdf.cell(0, 10, f'Phone: {customer["phone"]}', 0, 1)
    if customer.get('email'):
        pdf.cell(0, 10, f'Email: {customer["email"]}', 0, 1)
    if customer.get('address'):
        pdf.cell(0, 10, f'Address: {customer["address"]}', 0, 1)
    pdf.ln(10)
    
    # Items header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(80, 10, 'Product', 1, 0, 'C')
    pdf.cell(30, 10, 'Quantity', 1, 0, 'C')
    pdf.cell(30, 10, 'Price', 1, 0, 'C')
    pdf.cell(30, 10, 'Total', 1, 1, 'C')
    
    # Items
    pdf.set_font('Arial', '', 10)
    total_amount = 0
    for item in cart_items:
        item_total = item['quantity'] * item['price']
        total_amount += item_total
        pdf.cell(80, 10, item['product'][:30], 1, 0)
        pdf.cell(30, 10, str(item['quantity']), 1, 0, 'C')
        pdf.cell(30, 10, f"${item['price']:.2f}", 1, 0, 'C')
        pdf.cell(30, 10, f"${item_total:.2f}", 1, 1, 'C')
    
    # Total
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(140, 10, 'TOTAL:', 1, 0, 'R')
    pdf.cell(30, 10, f"${total_amount:.2f}", 1, 1, 'C')
    
    # Save PDF
    os.makedirs("invoices", exist_ok=True)
    pdf_path = f"invoices/invoice_{invoice_number}.pdf"
    pdf.output(pdf_path)
    return pdf_path, total_amount

# Create WhatsApp link with formatted invoice text
def create_whatsapp_link(phone, invoice_text):
    # Clean phone number (remove non-digits)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Encode message for URL
    encoded_message = urllib.parse.quote(invoice_text)
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return whatsapp_url

# Save invoice record
def save_invoice_record(customer, cart_items, invoice_number, total_amount):
    invoice_record = {
        'invoice_number': invoice_number,
        'customer': customer,
        'items': cart_items,
        'total_amount': total_amount,
        'date': datetime.now().isoformat(),
        'status': 'created',
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
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👥 Manage Salesmen", "📊 Sales Reports", "📈 Analytics"])
    
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
            total_invoices = len(filtered_invoices)
            avg_sale = total_sales / total_invoices if total_invoices > 0 else 0
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sales", f"${total_sales:.2f}")
            with col2:
                st.metric("Total Invoices", total_invoices)
            with col3:
                st.metric("Average Sale", f"${avg_sale:.2f}")
            
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
            salesman_sales = defaultdict(lambda: {'total': 0, 'count': 0})
            for invoice in filtered_invoices:
                salesman = invoice.get('salesman', invoice.get('created_by', 'Unknown'))
                salesman_sales[salesman]['total'] += invoice['total_amount']
                salesman_sales[salesman]['count'] += 1
            
            if salesman_sales:
                df_salesman = pd.DataFrame([
                    {
                        'Salesman': salesman,
                        'Total Sales': data['total'],
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
                    'Date': datetime.fromisoformat(inv['date']).strftime('%Y-%m-%d %H:%M'),
                    'Customer': inv['customer']['name'],
                    'Total': f"${inv['total_amount']:.2f}",
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
            customer_sales = defaultdict(lambda: {'total': 0, 'count': 0})
            for invoice in st.session_state.invoices:
                customer = invoice['customer']['name']
                customer_sales[customer]['total'] += invoice['total_amount']
                customer_sales[customer]['count'] += 1
            
            # Top customers chart
            if customer_sales:
                top_customers = sorted(customer_sales.items(), 
                                     key=lambda x: x[1]['total'], reverse=True)[:10]
                
                df_top_customers = pd.DataFrame([
                    {
                        'Customer': customer,
                        'Total Sales': data['total'],
                        'Invoice Count': data['count']
                    }
                    for customer, data in top_customers
                ])
                
                st.subheader("Top 10 Customers by Sales")
                fig_customers = px.bar(df_top_customers, x='Customer', y='Total Sales',
                                     title='Top Customers by Total Sales')
                fig_customers.update_xaxes(tickangle=45)
                st.plotly_chart(fig_customers, use_container_width=True)
            
            # Product analysis
            product_sales = defaultdict(lambda: {'total': 0, 'quantity': 0})
            for invoice in st.session_state.invoices:
                for item in invoice['items']:
                    product = item['product']
                    product_sales[product]['total'] += item['price'] * item['quantity']
                    product_sales[product]['quantity'] += item['quantity']
            
            if product_sales:
                top_products = sorted(product_sales.items(), 
                                    key=lambda x: x[1]['total'], reverse=True)[:10]
                
                df_top_products = pd.DataFrame([
                    {
                        'Product': product,
                        'Total Sales': data['total'],
                        'Quantity Sold': data['quantity']
                    }
                    for product, data in top_products
                ])
                
                st.subheader("Top 10 Products by Sales")
                fig_products = px.bar(df_top_products, x='Product', y='Total Sales',
                                    title='Top Products by Total Sales')
                fig_products.update_xaxes(tickangle=45)
                st.plotly_chart(fig_products, use_container_width=True)
                
                # Product quantity chart
                fig_quantity = px.bar(df_top_products, x='Product', y='Quantity Sold',
                                    title='Top Products by Quantity Sold')
                fig_quantity.update_xaxes(tickangle=45)
                st.plotly_chart(fig_quantity, use_container_width=True)
        
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
                st.dataframe(df_customers[['name', 'phone', 'email']], use_container_width=True)
        
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
                # Select customer
                customer_options = [f"{c['name']} - {c['phone']}" for c in st.session_state.customers]
                selected_customer_idx = st.selectbox("Select Customer", range(len(customer_options)), 
                                                   format_func=lambda x: customer_options[x])
                selected_customer = st.session_state.customers[selected_customer_idx]
                
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
                            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            
                            try:
                                # Generate WhatsApp formatted invoice text
                                invoice_text, amount = generate_whatsapp_invoice_text(selected_customer, st.session_state.cart, invoice_number)
                                
                                # Generate PDF invoice
                                pdf_path, _ = generate_pdf_invoice(selected_customer, st.session_state.cart, invoice_number)
                                
                                # Save invoice record
                                invoice_record = save_invoice_record(selected_customer, st.session_state.cart, invoice_number, amount)
                                
                                st.success(f"✅ Invoice {invoice_number} created successfully!")
                                
                                # Display invoice text
                                with st.expander("📄 Invoice Text Preview", expanded=True):
                                    st.text(invoice_text)
                                
                                # WhatsApp sharing
                                st.markdown("### 📱 Send Invoice via WhatsApp")
                                
                                whatsapp_link = create_whatsapp_link(selected_customer['phone'], invoice_text)
                                
                                col_wa, col_pdf = st.columns(2)
                                
                                with col_wa:
                                    st.markdown(f"**[📱 Send via WhatsApp]({whatsapp_link})**")
                                    st.caption("Click to open WhatsApp with the formatted invoice")
                                
                                with col_pdf:
                                    # Download PDF
                                    with open(pdf_path, "rb") as pdf_file:
                                        pdf_bytes = pdf_file.read()
                                        st.download_button(
                                            label="📥 Download PDF",
                                            data=pdf_bytes,
                                            file_name=f"invoice_{invoice_number}.pdf",
                                            mime="application/pdf"
                                        )
                                
                               
                                # Clear cart option
                                if st.button("🗑️ Clear Cart & Create New Invoice"):
                                    st.session_state.cart = []
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"Error creating invoice: {str(e)}")
                    
                    with col2:
                        if st.button("🗑️ Clear Cart"):
                            st.session_state.cart = []
                            st.rerun()
                
                else:
                    st.info("Cart is empty. Add some products to create an invoice.")
        
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
                total_count = len(display_invoices)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Sales", f"${total_sales:.2f}")
                with col2:
                    st.metric("Total Invoices", total_count)
                
                st.divider()
                
                for invoice in reversed(display_invoices):  # Show newest first
                    with st.expander(f"Invoice {invoice['invoice_number']} - {invoice['customer']['name']} - ${invoice['total_amount']:.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Customer:** {invoice['customer']['name']}")
                            st.write(f"**Phone:** {invoice['customer']['phone']}")
                            st.write(f"**Date:** {datetime.fromisoformat(invoice['date']).strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**Total:** ${invoice['total_amount']:.2f}")
                            if st.session_state.user_role == 'admin':
                                st.write(f"**Salesman:** {invoice.get('salesman', invoice.get('created_by', 'Unknown'))}")
                        
                        with col2:
                            st.write("**Items:**")
                            for item in invoice['items']:
                                st.write(f"- {item['product']}: {item['quantity']} × ${item['price']:.2f} = ${item['quantity'] * item['price']:.2f}")
                        
                        # Regenerate WhatsApp link
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