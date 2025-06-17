import frappe
import os
import shutil
import csv

def after_install():
    """Set up Tunisia COA features after app installation"""
    try:
        # Auto setup Tunisia COA for all existing companies
        frappe.enqueue(
            "my_custom_app.setup.tunisia_coa.enhanced_config.auto_setup_tunisia_for_all_companies",
            queue="long",
            timeout=3600
        )
        
        print("Tunisia COA module has been installed successfully - setup has been queued for all companies")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Tunisia COA Installation Error")
        print(f"Error during Tunisia COA setup: {str(e)}")

def copy_tunisia_coa_csv():
    """Copy the Tunisia COA CSV file to the app's folder"""
    try:
        # Source file from the repo root
        source_file = frappe.get_app_path("my_custom_app", "..", "..", "tunisia_coa.csv")
        
        # Target directory in the app
        target_dir = frappe.get_app_path("my_custom_app", "setup", "tunisia_coa")
        target_file = os.path.join(target_dir, "tunisia_coa.csv")
        
        # Ensure the target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy the file
        if os.path.exists(source_file):
            # Copy and convert the file
            convert_csv_format(source_file, target_file)
            print(f"Tunisia COA CSV copied and converted to {target_file}")
        else:
            raise Exception(f"Source file not found: {source_file}")
    except Exception as e:
        frappe.log_error(f"Error copying Tunisia COA CSV: {str(e)}", "Tunisia COA Installation")
        print(f"Error copying Tunisia COA CSV: {str(e)}")

def convert_csv_format(source_file, target_file):
    """Convert Tunisia COA CSV to the required format with correct columns"""
    try:
        # Read the original CSV
        rows = []
        with open(source_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if not rows:
            raise Exception("Empty CSV file")
        
        # Check if the first row contains the header we need
        first_row = rows[0]
        if "Parent Account Number" in first_row and "Root Type" in first_row and "Account Currency" in first_row:
            # Already in the correct format, just copy it
            shutil.copy2(source_file, target_file)
            return
        
        # Track parent account numbers for mapping
        parent_accounts = {}
        for row in rows[1:]:  # Skip header
            account_name = row[0]
            account_number = row[2] if len(row) > 2 else ""
            if account_number:
                parent_accounts[account_name] = account_number
        
        # Create new rows with the updated structure
        new_rows = []
        # New header
        new_rows.append(["Account Name", "Parent Account", "Account Number", "Parent Account Number", "Is Group", "Account Type", "Root Type", "Account Currency"])
        
        # Process each row
        for row in rows[1:]:  # Skip header
            if len(row) < 5:  # Skip invalid rows
                continue
                
            account_name = row[0]
            parent_account = row[1] if len(row) > 1 else ""
            account_number = row[2] if len(row) > 2 else ""
            account_type = row[3] if len(row) > 3 else ""
            is_group = row[4] if len(row) > 4 else "0"
            
            # Determine parent account number
            parent_account_number = ""
            if parent_account in parent_accounts:
                parent_account_number = parent_accounts[parent_account]
            
            # Determine root type based on account name or type
            root_type = ""
            if "ACTIFS" in account_name or account_type in ["Fixed Asset", "Bank", "Cash", "Stock", "Receivable"]:
                root_type = "Asset"
            elif "CAPITAUX PROPRES" in account_name or account_type == "Equity":
                root_type = "Equity"
            elif "PASSIFS" in account_name or account_type in ["Liability", "Payable", "Tax"]:
                root_type = "Liability"
            elif "COMPTES DE CHARGES" in account_name or account_type in ["Expense Account", "Cost of Goods Sold"]:
                root_type = "Expense"
            elif "COMPTES DE PRODUITS" in account_name or account_type == "Income Account":
                root_type = "Income"
            
            # Append the new row
            new_rows.append([
                account_name,
                parent_account,
                account_number,
                parent_account_number,
                is_group,
                account_type,
                root_type,
                "TND"  # Default to Tunisian Dinar
            ])
        
        # Write the new CSV
        with open(target_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(new_rows)
            
    except Exception as e:
        frappe.log_error(f"Error converting CSV format: {str(e)}", "Tunisia COA Installation")
        print(f"Error converting CSV format: {str(e)}")
        # Fall back to direct copy if conversion fails
        shutil.copy2(source_file, target_file)

def add_to_installed_modules():
    """Add Tunisia COA module to installed modules"""
    try:
        # Add to Module Def if not exists
        if not frappe.db.exists("Module Def", "Tunisia COA"):
            module = frappe.new_doc("Module Def")
            module.module_name = "Tunisia COA"
            module.app_name = "my_custom_app"
            module.insert(ignore_permissions=True)
            print("Added Tunisia COA module definition")
    except Exception as e:
        print(f"Could not add Tunisia COA module: {str(e)}")
        # Not critical, continue with installation 