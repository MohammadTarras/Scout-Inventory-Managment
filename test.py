import streamlit as st
from supabase import create_client
import json

# Load secrets
url = 'https://jwuzkrrmbzglhigaabqj.supabase.co'
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3dXprcnJtYnpnbGhpZ2FhYnFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY3ODUzMjUsImV4cCI6MjA3MjM2MTMyNX0.aH6eHn6QsNr-laZ4NCPLocm-quGAfPAnyuqSHi8CDiw"

# Initialize client
supabase = create_client(url, key)



st.title("📦 Upload Invoices JSON and Insert into Supabase")

uploaded_file = st.file_uploader("Choose a JSON file", type="json")

def get_customer_id(name):
    """Fetch customer_id from customers table using the name."""
    response = supabase.table("customers").select("id").eq("name", name).execute()
    if response.data:
        return response.data[0]["id"]
    return None

if uploaded_file:
    try:
        invoices = json.load(uploaded_file)
        if isinstance(invoices, dict):
            invoices = [invoices]

        invoices_to_insert = []

        for invoice in invoices:
            if "customer" in invoice:
                customer_id = get_customer_id(invoice["customer"])
                if not customer_id:
                    st.warning(f"Customer '{invoice['customer']}' not found. Skipping invoice.")
                    continue
                invoice["customer_id"] = customer_id
                del invoice["customer"]  # Remove the problematic key

            invoices_to_insert.append(invoice)

        if invoices_to_insert:
            inserted = supabase.table("invoices").insert(invoices_to_insert).execute()
            st.success(f"Inserted {len(invoices_to_insert)} invoices!")
            st.write(inserted.data)
        else:
            st.info("No invoices to insert.")

    except Exception as e:
        st.error(f"Error reading or inserting JSON: {e}")
