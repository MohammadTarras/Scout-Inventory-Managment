import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from fpdf import FPDF
import base64
import urllib.parse
import tempfile
import shutil

# Set page config
st.set_page_config(
    page_title="Invoice Management System",
    page_icon="🧾",
    layout="wide"
)

# Initialize session state
if 'customers' not in st.session_state:
    st.session_state.customers = []

if 'products' not in st.session_state:
    st.session_state.products = pd.DataFrame()

if 'cart' not in st.session_state:
    st.session_state.cart = []

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

# Load products from CSV
def load_products():
    uploaded_file = 'products.csv'
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if 'product' in df.columns and 'price' in df.columns:
                st.session_state.products = df
                st.success("Products loaded successfully!")
                return True
            else:
                st.error("CSV must contain 'product' and 'price' columns")
                return False
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return False
    return False

# Generate HTML invoice for web viewing
def generate_html_invoice(customer, cart_items, invoice_number):
    total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice #{invoice_number}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .invoice-container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                color: #333;
            }}
            .invoice-info {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }}
            .customer-info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #007bff;
                color: white;
            }}
            .total-row {{
                background-color: #f8f9fa;
                font-weight: bold;
                font-size: 18px;
            }}
            .download-btn {{
                background: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                margin-top: 20px;
            }}
            .download-btn:hover {{
                background: #0056b3;
            }}
        </style>
    </head>
    <body>
        <div class="invoice-container">
            <div class="header">
                <h1>INVOICE</h1>
                <div class="invoice-info">
                    <div>
                        <strong>Invoice #:</strong> {invoice_number}<br>
                        <strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}
                    </div>
                </div>
            </div>
            
            <div class="customer-info">
                <h3>Bill To:</h3>
                <strong>Name:</strong> {customer['name']}<br>
                <strong>Phone:</strong> {customer['phone']}<br>
                {f"<strong>Email:</strong> {customer['email']}<br>" if customer.get('email') else ""}
                {f"<strong>Address:</strong> {customer['address']}<br>" if customer.get('address') else ""}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for item in cart_items:
        item_total = item['quantity'] * item['price']
        html_content += f"""
                    <tr>
                        <td>{item['product']}</td>
                        <td>{item['quantity']}</td>
                        <td>${item['price']:.2f}</td>
                        <td>${item_total:.2f}</td>
                    </tr>
        """
    
    html_content += f"""
                    <tr class="total-row">
                        <td colspan="3">TOTAL:</td>
                        <td>${total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="text-align: center; color: #666; font-size: 14px;">
                <p>Thank you for your business!</p>
                <p>Invoice generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content, total_amount

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
    pdf_path = f"invoice_{invoice_number}.pdf"
    pdf.output(pdf_path)
    return pdf_path, total_amount

# Save invoice as downloadable file
def save_invoice_files(customer, cart_items, invoice_number):
    # Create invoices directory
    os.makedirs("invoices", exist_ok=True)
    
    # Generate HTML
    html_content, total_amount = generate_html_invoice(customer, cart_items, invoice_number)
    html_path = f"invoices/invoice_{invoice_number}.html"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate PDF
    pdf_path, _ = generate_pdf_invoice(customer, cart_items, invoice_number)
    
    # Move PDF to invoices folder
    new_pdf_path = f"invoices/invoice_{invoice_number}.pdf"
    if os.path.exists(pdf_path):
        shutil.move(pdf_path, new_pdf_path)
    
    return html_path, new_pdf_path, total_amount

# Create WhatsApp share link with web invoice
def create_whatsapp_link_with_invoice(phone, customer_name, invoice_number, amount, invoice_url):
    # Clean phone number (remove non-digits)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Create message with invoice link
    message = f"""Hello {customer_name}! 

Your invoice #{invoice_number} for ${amount:.2f} is ready.

View your invoice here: {invoice_url}

Thank you for your business!"""
    
    # Encode message for URL
    encoded_message = urllib.parse.quote(message)
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return whatsapp_url

# Initialize
load_customers()


load_products()


# Main title
st.title("🧾 Invoice Management System")

# Create tabs
tab1, tab2 = st.tabs(["👥 Add Customer", "🛒 Create Invoice"])

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
                        'created_date': datetime.now().isoformat()
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
        st.warning("Please upload a products CSV file first in the sidebar.")
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
            
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df['Total'] = cart_df['price'] * cart_df['quantity']
            
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
                        # Generate both HTML and PDF invoices
                        html_path, pdf_path, amount = save_invoice_files(selected_customer, st.session_state.cart, invoice_number)
                        
                        st.success(f"Invoice {invoice_number} created successfully!")
                        
                        # Show invoice preview
                        with st.expander("📄 Invoice Preview", expanded=True):
                            # Read and display HTML content
                            with open(html_path, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            st.components.v1.html(html_content, height=600, scrolling=True)
                        
                        # Download buttons
                        col_download1, col_download2 = st.columns(2)
                        
                        with col_download1:
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"invoice_{invoice_number}.pdf",
                                    mime="application/pdf"
                                )
                        
                        with col_download2:
                            with open(html_path, "r", encoding='utf-8') as html_file:
                                html_bytes = html_file.read()
                                st.download_button(
                                    label="📥 Download HTML",
                                    data=html_bytes,
                                    file_name=f"invoice_{invoice_number}.html",
                                    mime="text/html"
                                )
                        
                        # Method selection for sharing
                        st.markdown("### 📱 Share Invoice")
                        
                        sharing_method = st.radio(
                            "Choose sharing method:",
                            ["Web Link (Recommended)", "Manual File Sharing"],
                            help="Web Link creates a shareable URL, Manual requires you to send the files yourself"
                        )
                        
                        if sharing_method == "Web Link (Recommended)":
                            # For demo purposes, we'll show how it would work with a hosted solution
                            st.info("💡 **For Production Use:** You'll need to host these files on a web server")
                            
                            # Simulate hosted URL (in production, this would be your actual server)
                            demo_url = f"https://yourdomain.com/invoices/invoice_{invoice_number}.html"
                            
                            st.code(f"Example hosted URL: {demo_url}")
                            
                            # WhatsApp link with hosted URL
                            whatsapp_link = create_whatsapp_link_with_invoice(
                                selected_customer['phone'], 
                                selected_customer['name'], 
                                invoice_number, 
                                amount, 
                                demo_url
                            )
                            
                            st.markdown(f"**[📱 Send via WhatsApp]({whatsapp_link})**")
                            
                            # Instructions for hosting
                            with st.expander("ℹ️ How to set up web hosting"):
                                st.markdown("""
                                **Option 1: Simple File Hosting**
                                - Upload the HTML file to Google Drive, Dropbox, or GitHub Pages
                                - Get a shareable link
                                - Replace the demo URL above
                                
                                **Option 2: Web Server**
                                - Host files on your domain
                                - Set up a simple web server (Apache, Nginx, etc.)
                                - Upload invoice files to `/invoices/` directory
                                
                                **Option 3: Cloud Storage**
                                - Use AWS S3, Google Cloud Storage
                                - Enable public access for invoice files
                                - Use the public URL in WhatsApp
                                """)
                        
                        else:  # Manual File Sharing
                            st.warning("📎 **Manual Sharing**: Download the files and send them manually")
                            
                            # Simple WhatsApp message without link
                            simple_message = f"Hello {selected_customer['name']}! Your invoice #{invoice_number} for ${amount:.2f} is ready. I'll send you the invoice file shortly. Thank you for your business!"
                            encoded_simple_message = urllib.parse.quote(simple_message)
                            clean_phone = ''.join(filter(str.isdigit, selected_customer['phone']))
                            simple_whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_simple_message}"
                            
                            st.markdown(f"**[📱 Notify Customer via WhatsApp]({simple_whatsapp_url})**")
                            st.info("After clicking the link above, manually attach the PDF file in WhatsApp")
                        
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

# Footer
st.markdown("---")
st.markdown("*Invoice Management System - Built with Streamlit*")