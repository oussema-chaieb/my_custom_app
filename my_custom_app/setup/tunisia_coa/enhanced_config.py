# Complete Tunisia COA Configuration - ENHANCED VERSION
# Copyright (c) 2023, DON and contributors
# For license information, please see license.txt

import frappe
import os
import csv
from frappe.utils.csvutils import read_csv_content

def import_tunisia_coa_for_company(company_name):
    """Import Tunisia Chart of Accounts from CSV for a specific company"""
    
    # Get the path to the CSV file in the app's folder
    csv_file_path = frappe.get_app_path("my_custom_app", "setup", "tunisia_coa", "tunisia_coa.csv")
    
    if not os.path.exists(csv_file_path):
        frappe.log_error("Tunisia COA CSV file not found", "COA Import Error")
        return False
    
    try:
        # Read the CSV content
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            rows = read_csv_content(f.read())
        
        if not rows:
            frappe.log_error("Empty CSV file", "COA Import Error")
            return False
        
        # Process the CSV rows to create accounts
        for i, row in enumerate(rows):
            if i == 0:  # Skip header row
                continue
            
            # Extract data according to the new column structure
            # Account Name,Parent Account,Account Number,Parent Account Number,Is Group,Account Type,Root Type,Account Currency
            account_name = row[0]
            parent_account_raw = row[1]
            account_number = row[2]
            parent_account_number = row[3] if len(row) > 3 and row[3] else ""
            is_group = int(row[4]) if len(row) > 4 and row[4] else 0
            account_type = row[5] if len(row) > 5 and row[5] else ""
            root_type = row[6] if len(row) > 6 and row[6] else ""
            account_currency = row[7] if len(row) > 7 and row[7] else "TND"  # Default to Tunisian Dinar
            
            # ------------------------------------------------------------------
            # Build the display name we will save inside ERPNext.
            # We always prefix the account number (if any) so that later look-ups
            # such as "5411 - Caisse en dinars - <Company>" work reliably.
            # ------------------------------------------------------------------
            base_account_name = f"{account_number} - {account_name}" if account_number else account_name

            # Determine if this line represents a root "Classe" account.
            # It is root if the CSV shows no parent (parent_account_raw is empty) OR the label starts with "Classe" / "CLASSE".
            is_root_classe = (not parent_account_raw) \
                or account_name.upper().startswith("CLASSE") \
                or account_name.upper().startswith((
                    "1 - CLASSE", "2 - CLASSE", "3 - CLASSE",
                    "4 - CLASSE", "5 - CLASSE", "6 - CLASSE", "7 - CLASSE"))

            # Append company suffix for all company-specific accounts (i.e. the
            # vast majority) but NOT for the root "Classe" nodes.
            account_name_with_company = base_account_name if is_root_classe else f"{base_account_name} - {company_name}"

            # Resolve the parent account name (if any) using the same convention
            parent_account = ""
            if parent_account_raw:
                parent_base = f"{parent_account_number} - {parent_account_raw}" if parent_account_number else parent_account_raw
                parent_account = parent_base if parent_account_raw.startswith("CLASSE") or parent_account_raw.startswith("Classe ") else f"{parent_base} - {company_name}"

            # Check if account already exists
            if frappe.db.exists("Account", account_name_with_company):
                continue

            # For root accounts (with no parent)
            if not parent_account and is_root_classe:
                try:
                    # Create root account (no company suffix)
                    root_account = frappe.get_doc({
                        "doctype": "Account",
                        "account_name": base_account_name,
                        "account_type": account_type or "",
                        "root_type": root_type or map_root_type(account_name),
                        "is_group": 1,
                        "company": company_name,
                        "account_number": account_number,
                        "account_currency": account_currency
                    })
                    root_account.insert(ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Error creating root account {account_name}: {str(e)}", "COA Import Error")
            else:
                # Create regular account
                try:
                    account = frappe.get_doc({
                        "doctype": "Account",
                        "account_name": account_name_with_company,
                        "parent_account": parent_account,
                        "account_type": account_type or "",
                        "root_type": root_type or "",
                        "is_group": is_group,
                        "company": company_name,
                        "account_number": account_number,
                        "account_currency": account_currency
                    })
                    account.insert(ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Error creating account {account_name}: {str(e)}", "COA Import Error")
        
        frappe.db.commit()
        print(f"✅ Tunisia Chart of Accounts imported successfully for {company_name}")
        return True
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error importing Tunisia COA: {str(e)}", "COA Import Error")
        return False


def map_root_type(account_name):
    """Map root account names to root types"""
    if "ACTIFS" in account_name:
        return "Asset"
    elif "CAPITAUX PROPRES" in account_name:
        return "Equity"
    elif "PASSIFS" in account_name:
        return "Liability" 
    elif "COMPTES DE CHARGES" in account_name:
        return "Expense"
    elif "COMPTES DE PRODUITS" in account_name:
        return "Income"
    else:
        return "Asset"  # Default


def auto_setup_tunisia_for_all_companies():
    """Automatically set up Tunisia COA for all existing companies"""
    companies = frappe.get_all("Company", fields=["name"])
    
    for company in companies:
        try:
            # Step 1: Import the chart of accounts
            print(f"Setting up Tunisia COA for {company.name}...")
            success = import_tunisia_coa_for_company(company.name)
            
            if success:
                # Step 2: Configure company defaults
                configure_complete_tunisia_company_defaults(company.name)
                
                # Step 3: Create tax templates
                create_comprehensive_tunisia_tax_templates(company.name)
                
                # Step 4: Configure payment methods
                configure_tunisia_payment_methods(company.name)
                
                # Step 5: Set up warehouse connections
                setup_warehouse_account_connections(company.name)
                
                # Step 6: Create cost centers
                create_tunisia_cost_centers(company.name)
                
                # Step 7: Validate
                validate_complete_tunisia_setup(company.name)
                
                print(f"✅ Tunisia COA setup completed for {company.name}")
        except Exception as e:
            print(f"❌ Error setting up Tunisia COA for {company.name}: {str(e)}")


def auto_setup_tunisia_for_new_company(doc, method=None):
    """Automatically set up Tunisia COA for newly created company"""
    try:
        print(f"Setting up Tunisia COA for new company {doc.name}...")
        
        # Step 1: Import the chart of accounts
        success = import_tunisia_coa_for_company(doc.name)
        
        if success:
            # Step 2: Configure company defaults
            configure_complete_tunisia_company_defaults(doc.name)
            
            # Step 3: Create tax templates
            create_comprehensive_tunisia_tax_templates(doc.name)
            
            # Step 4: Configure payment methods
            configure_tunisia_payment_methods(doc.name)
            
            # Step 5: Set up warehouse connections
            setup_warehouse_account_connections(doc.name)
            
            # Step 6: Create cost centers
            create_tunisia_cost_centers(doc.name)
            
            print(f"✅ Tunisia COA setup completed for new company {doc.name}")
    except Exception as e:
        print(f"❌ Error setting up Tunisia COA for new company {doc.name}: {str(e)}")


def configure_complete_tunisia_company_defaults(company_name):
    """Complete configuration for Tunisian companies with all required accounts"""
    
    company = frappe.get_doc("Company", company_name)
    
    # Comprehensive operational accounts mapping
    tunisia_defaults = {
        # Cash & Bank Operations
        "default_cash_account": f"5411 - Caisse en dinars - {company_name}",
        "default_bank_account": f"5321 - Comptes en dinars - {company_name}",
        
        # Customer & Supplier Management
        "default_receivable_account": f"4111 - Clients - ventes de biens ou de prestations de services - {company_name}",
        "default_payable_account": f"4011 - Fournisseurs - achats de biens ou de prestations de services - {company_name}",
        
        # Sales & Purchase Operations
        "default_income_account": f"707 - Ventes de marchandises - {company_name}",
        "default_expense_account": f"607 - Achats de marchandises - {company_name}",
        
        # Inventory Management
        "default_inventory_account": f"37 - Stocks de marchandises - {company_name}",
        "stock_adjustment_account": f"603 - Variation des stocks (approvisionnements et marchandises) - {company_name}",
        "cost_center": f"Main - {company_name}",
        
        # Financial Adjustments & Corrections
        "round_off_account": f"657 - Autres charges financières - {company_name}",
        "write_off_account": f"634 - Pertes sur créances irrécouvrables - {company_name}",
        "exchange_gain_loss_account": f"655 - Pertes de change - {company_name}",
        "unrealized_exchange_gain_loss_account": f"465 - Différence de conversion sur éléments courants (ACTIF) - {company_name}",
        
        # Discounts & Accruals
        "default_discount_account": f"654 - Escomptes accordés - {company_name}",
        "default_deferred_revenue_account": f"472 - Produits constatés d'avance - {company_name}",
        "default_deferred_expense_account": f"471 - Charges constatées d'avance - {company_name}",
        
        # Asset Management & Depreciation
        "accumulated_depreciation_account": f"282 - Amortissements des immobilisations corporelles (même ventilation que celle du compte 28) - {company_name}",
        "depreciation_expense_account": f"6811 - Dotations aux amortissements des immobilisations incorporelles et corporelles - {company_name}",
        "capital_work_in_progress_account": f"232 - Immobilisations corporelles en cours - {company_name}",
        
        # Accrued Transactions
        "asset_received_but_not_billed": f"4081 - Fournisseurs d'exploitation - {company_name}",
        "service_received_but_not_billed": f"4081 - Fournisseurs d'exploitation - {company_name}",
        "default_provisional_account": f"461 - Compte d'attente (ACTIF) - {company_name}",
        
        # Customer & Supplier Advances
        "default_advance_received_account": f"419 - Clients créditeurs - {company_name}",
        "default_advance_paid_account": f"409 - Fournisseurs débiteurs - {company_name}",
        
        # CRITICAL: Warehouse & Inventory Accounts (ADDED)
        "stock_received_but_not_billed": f"4081 - Fournisseurs d'exploitation - {company_name}",
        "expenses_included_in_asset_valuation": f"608 - Achats liés à une modification comptable à prendre en compte dans le résultat de - {company_name}",
        "stock_liability_account": f"4081 - Fournisseurs d'exploitation - {company_name}",
        "default_warehouse_account": f"37 - Stocks de marchandises - {company_name}",
        
        # Additional Tunisia-specific accounts
        "gain_loss_account": f"756 - Gains de change - {company_name}",
        "default_temporary_account": f"461 - Compte d'attente (ACTIF) - {company_name}",
    }
    
    # CRITICAL: Enable perpetual inventory for proper stock accounting
    company.enable_perpetual_inventory = 1
    
    # Update company with defaults
    for field, account in tunisia_defaults.items():
        if frappe.db.exists("Account", account):
            setattr(company, field, account)
        else:
            print(f"Warning: Account {account} not found for {field}")
    
    company.save()
    print(f"✅ Complete company defaults configured for {company_name}")


def create_comprehensive_tunisia_tax_templates(company_name):
    """Create comprehensive Tunisian tax templates for all VAT rates"""
    
    tax_templates = [
        # Sales Tax Templates (TVA Collectée) - For outgoing invoices
        {
            "title": "TVA Collectée 19% - Tunisia",
            "company": company_name,
            "type": "sales",
            "accounts": [
                {
                    "account_head": f"4366 - Etat - TVA collectée - {company_name}",
                    "rate": 19,
                    "description": "TVA Collectée 19%",
                    "charge_type": "On Net Total",
                    "account_type": "Tax"
                }
            ]
        },
        {
            "title": "TVA Collectée 13% - Tunisia", 
            "company": company_name,
            "type": "sales",
            "accounts": [
                {
                    "account_head": f"4366 - Etat - TVA collectée - {company_name}",
                    "rate": 13,
                    "description": "TVA Collectée 13%", 
                    "charge_type": "On Net Total",
                    "account_type": "Tax"
                }
            ]
        },
        {
            "title": "TVA Collectée 7% - Tunisia",
            "company": company_name,
            "type": "sales",
            "accounts": [
                {
                    "account_head": f"4366 - Etat - TVA collectée - {company_name}",
                    "rate": 7,
                    "description": "TVA Collectée 7%",
                    "charge_type": "On Net Total",
                    "account_type": "Tax"
                }
            ]
        },
        {
            "title": "TVA Collectée 0% - Tunisia",
            "company": company_name,
            "type": "sales",
            "accounts": [
                {
                    "account_head": f"4366 - Etat - TVA collectée - {company_name}",
                    "rate": 0,
                    "description": "TVA Collectée 0% (Exonérée)",
                    "charge_type": "On Net Total",
                    "account_type": "Tax"
                }
            ]
        },
        
        # Purchase Tax Templates (TVA Déductible) - For incoming bills
        {
            "title": "TVA Déductible 19% - Tunisia",
            "company": company_name,
            "type": "purchase",
            "accounts": [
                {
                    "account_head": f"4365 - Etat - TVA déductible - {company_name}",
                    "rate": 19,
                    "description": "TVA Déductible 19%",
                    "charge_type": "On Net Total", 
                    "account_type": "Tax"
                }
            ]
        },
        {
            "title": "TVA Déductible 13% - Tunisia",
            "company": company_name,
            "type": "purchase",
            "accounts": [
                {
                    "account_head": f"4365 - Etat - TVA déductible - {company_name}",
                    "rate": 13,
                    "description": "TVA Déductible 13%",
                    "charge_type": "On Net Total", 
                    "account_type": "Tax"
                }
            ]
        },
        {
            "title": "TVA Déductible 7% - Tunisia",
            "company": company_name,
            "type": "purchase",
            "accounts": [
                {
                    "account_head": f"4365 - Etat - TVA déductible - {company_name}",
                    "rate": 7,
                    "description": "TVA Déductible 7%",
                    "charge_type": "On Net Total", 
                    "account_type": "Tax"
                }
            ]
        }
    ]
    
    # Create Sales Tax Templates
    for template_data in tax_templates:
        try:
            if template_data["type"] == "sales":
                if not frappe.db.exists("Sales Taxes and Charges Template", template_data["title"]):
                    template = frappe.get_doc({
                        "doctype": "Sales Taxes and Charges Template",
                        "title": template_data["title"],
                        "company": template_data["company"],
                        "taxes": template_data["accounts"]
                    })
                    template.insert()
                    print(f"✅ Created sales tax template: {template_data['title']}")
            
            # Create Purchase Tax Templates
            elif template_data["type"] == "purchase":
                if not frappe.db.exists("Purchase Taxes and Charges Template", template_data["title"]):
                    purchase_template = frappe.get_doc({
                        "doctype": "Purchase Taxes and Charges Template",
                        "title": template_data["title"],
                        "company": template_data["company"],
                        "taxes": template_data["accounts"]
                    })
                    purchase_template.insert()
                    print(f"✅ Created purchase tax template: {template_data['title']}")
        except Exception as e:
            print(f"Error creating tax template {template_data['title']}: {str(e)}")


def configure_tunisia_payment_methods(company_name):
    """Configure payment methods with correct Tunisian accounts"""
    
    payment_methods = [
        {
            "mode_of_payment": "Cash",
            "default_account": f"5411 - Caisse en dinars - {company_name}",
            "type": "Cash"
        },
        {
            "mode_of_payment": "Bank Transfer", 
            "default_account": f"5321 - Comptes en dinars - {company_name}",
            "type": "Bank"
        },
        {
            "mode_of_payment": "Check",
            "default_account": f"531 - Valeurs à l'encaissement - {company_name}",
            "type": "Bank"
        },
        {
            "mode_of_payment": "Credit Card",
            "default_account": f"5321 - Comptes en dinars - {company_name}",
            "type": "Bank"
        },
        {
            "mode_of_payment": "Wire Transfer",
            "default_account": f"5321 - Comptes en dinars - {company_name}",
            "type": "Bank"
        },
        {
            "mode_of_payment": "Mobile Payment",
            "default_account": f"5321 - Comptes en dinars - {company_name}",
            "type": "Bank"
        }
    ]
    
    for method in payment_methods:
        try:
            # Check if Mode of Payment exists, create if not
            if not frappe.db.exists("Mode of Payment", method["mode_of_payment"]):
                mop = frappe.get_doc({
                    "doctype": "Mode of Payment",
                    "mode_of_payment": method["mode_of_payment"],
                    "type": method["type"]
                })
                mop.insert()
            
            # Set default account for this company
            mop_doc = frappe.get_doc("Mode of Payment", method["mode_of_payment"])
            
            # Check if account already exists for this company
            existing = False
            for account in mop_doc.accounts:
                if account.company == company_name:
                    account.default_account = method["default_account"]
                    existing = True
                    break
            
            if not existing and frappe.db.exists("Account", method["default_account"]):
                mop_doc.append("accounts", {
                    "company": company_name,
                    "default_account": method["default_account"]
                })
            
            mop_doc.save()
            print(f"✅ Configured payment method: {method['mode_of_payment']}")
        except Exception as e:
            print(f"Error configuring payment method {method['mode_of_payment']}: {str(e)}")


def setup_tunisia_item_defaults(company_name):
    """Set up default accounts for items with Tunisia COA"""
    
    try:
        # Get all items and set Tunisia-specific defaults
        items = frappe.get_all("Item", {"disabled": 0})
        
        default_accounts = {
            "income_account": f"707 - Ventes de marchandises - {company_name}",
            "expense_account": f"607 - Achats de marchandises - {company_name}",
            "buying_cost_center": f"Main - {company_name}",
            "selling_cost_center": f"Main - {company_name}"
        }
        
        updated_items = 0
        for item in items[:50]:  # Limit to first 50 items to avoid timeout
            try:
                item_doc = frappe.get_doc("Item", item.name)
                
                # Check if company defaults already exist
                existing = False
                for default in item_doc.item_defaults:
                    if default.company == company_name:
                        # Update existing
                        for field, account in default_accounts.items():
                            if hasattr(default, field) and frappe.db.exists("Account", account):
                                setattr(default, field, account)
                        existing = True
                        break
                
                if not existing:
                    # Add new company defaults - only if accounts exist
                    valid_accounts = {}
                    for field, account in default_accounts.items():
                        if frappe.db.exists("Account", account):
                            valid_accounts[field] = account
                    
                    if valid_accounts:
                        item_doc.append("item_defaults", {
                            "company": company_name,
                            **valid_accounts
                        })
                
                item_doc.save()
                updated_items += 1
            except Exception as e:
                print(f"Warning: Could not update item {item.name}: {str(e)}")
        
        print(f"✅ Updated item defaults for {updated_items} items")
    except Exception as e:
        print(f"Error in item defaults setup: {str(e)}")


def create_tunisia_cost_centers(company_name):
    """Create essential cost centers for Tunisian operations"""
    
    cost_centers = [
        {
            "cost_center_name": "Main",
            "parent_cost_center": f"All Cost Centers - {company_name}",
            "company": company_name,
            "is_group": 0
        },
        {
            "cost_center_name": "Sales",
            "parent_cost_center": f"Main - {company_name}",
            "company": company_name,
            "is_group": 0
        },
        {
            "cost_center_name": "Administration",
            "parent_cost_center": f"Main - {company_name}",
            "company": company_name,
            "is_group": 0
        },
        {
            "cost_center_name": "Operations",
            "parent_cost_center": f"Main - {company_name}",
            "company": company_name,
            "is_group": 0
        }
    ]
    
    for cc_data in cost_centers:
        try:
            cc_name = f"{cc_data['cost_center_name']} - {company_name}"
            if not frappe.db.exists("Cost Center", cc_name):
                cc = frappe.get_doc({
                    "doctype": "Cost Center",
                    "cost_center_name": cc_data["cost_center_name"],
                    "parent_cost_center": cc_data["parent_cost_center"],
                    "company": cc_data["company"],
                    "is_group": cc_data["is_group"]
                })
                cc.insert()
                print(f"✅ Created cost center: {cc_name}")
        except Exception as e:
            print(f"Error creating cost center {cc_data['cost_center_name']}: {str(e)}")


def setup_warehouse_account_connections(company_name):
    """Set up critical warehouse account connections"""
    
    try:
        # 1. Link warehouses to stock accounts
        warehouses = frappe.get_all("Warehouse", 
            filters={"company": company_name}, 
            fields=["name", "account"])
        
        stock_account = f"37 - Stocks de marchandises - {company_name}"
        
        for wh in warehouses:
            if not wh.account and frappe.db.exists("Account", stock_account):
                warehouse_doc = frappe.get_doc("Warehouse", wh.name)
                warehouse_doc.account = stock_account
                warehouse_doc.save()
                print(f"✅ Linked warehouse {wh.name} to stock account")
        
        # 2. Configure Stock Settings
        try:
            stock_settings = frappe.get_doc("Stock Settings")
            if not stock_settings.default_warehouse_account and frappe.db.exists("Account", stock_account):
                stock_settings.default_warehouse_account = stock_account
                stock_settings.save()
                print(f"✅ Set default warehouse account in Stock Settings")
        except Exception as e:
            print(f"Warning: Could not update Stock Settings: {str(e)}")
        
    except Exception as e:
        print(f"Error in warehouse setup: {str(e)}")


def validate_complete_tunisia_setup(company_name):
    """Comprehensive validation of Tunisia setup with better error handling"""
    
    required_mappings = [
        ("default_cash_account", "541", "Cash operations"),
        ("default_bank_account", "532", "Banking operations"), 
        ("default_receivable_account", "4111", "Customer invoices"),
        ("default_payable_account", "4011", "Supplier bills"),
        ("default_expense_account", "607", "Purchase expenses"),
        ("default_income_account", "707", "Sales revenue"),
        ("stock_adjustment_account", "603", "Inventory adjustments"),
        ("default_inventory_account", "37", "Inventory management"),
        ("round_off_account", "657", "Rounding differences"),
        ("write_off_account", "634", "Bad debts"),
        ("stock_received_but_not_billed", "4081", "Stock received but not billed"),
        ("expenses_included_in_asset_valuation", "608", "Freight and customs"),
    ]
    
    try:
        company = frappe.get_doc("Company", company_name)
        
        issues = []
        configured = []
        
        # Check perpetual inventory
        if company.enable_perpetual_inventory:
            configured.append("✅ Perpetual Inventory: Enabled")
        else:
            issues.append("❌ Perpetual Inventory: Disabled (CRITICAL)")
        
        for field, expected_code, description in required_mappings:
            account = getattr(company, field, None)
            if not account:
                issues.append(f"❌ Missing {field} ({description})")
            elif not account.startswith(expected_code):
                issues.append(f"❌ {field} not using correct Tunisian account (expected {expected_code})")
            else:
                configured.append(f"✅ {field}: {account}")
        
        # Check tax templates
        required_tax_templates = [
            ("Sales Taxes and Charges Template", "TVA Collectée 19% - Tunisia"),
            ("Purchase Taxes and Charges Template", "TVA Déductible 19% - Tunisia"),
        ]
        
        for doctype, template in required_tax_templates:
            if frappe.db.exists(doctype, template):
                configured.append(f"✅ Tax template: {template}")
            else:
                issues.append(f"❌ Missing {doctype}: {template}")
        
        # Check warehouses
        warehouses = frappe.get_all("Warehouse", 
            filters={"company": company_name}, 
            fields=["name", "account"])
        
        unlinked_warehouses = [wh.name for wh in warehouses if not wh.account]
        if unlinked_warehouses:
            issues.append(f"❌ Warehouses without accounts: {', '.join(unlinked_warehouses[:3])}")
        else:
            configured.append(f"✅ All {len(warehouses)} warehouses linked to accounts")
        
        print("\n" + "="*60)
        print("TUNISIA COA VALIDATION REPORT")
        print("="*60)
        
        if configured:
            print("\n✅ CORRECTLY CONFIGURED:")
            for item in configured:
                print(f"  {item}")
        
        if issues:
            print("\n❌ ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            print(f"\nTotal Issues: {len(issues)}")
            return False
        else:
            print("\n🎉 ALL TUNISIA CONFIGURATIONS ARE PERFECT!")
            print(f"✅ {len(configured)} components successfully configured")
            return True
    
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False


@frappe.whitelist()
def setup_complete_tunisia_configuration(company_name=None):
    """Run complete Tunisia configuration after CSV import - ENHANCED VERSION"""
    
    if not company_name:
        company_name = frappe.defaults.get_user_default("Company")
    
    if not company_name:
        return {"success": False, "message": "No company specified"}
    
    print(f"\n🇹🇳 STARTING COMPLETE TUNISIA COA CONFIGURATION FOR {company_name}")
    print("="*60)
    
    try:
        # Step 1: Configure comprehensive company defaults (includes warehouse accounts)
        print("Step 1: Configuring company account defaults...")
        configure_complete_tunisia_company_defaults(company_name)
        
        # Step 2: Create comprehensive tax templates
        print("Step 2: Creating comprehensive tax templates...")
        create_comprehensive_tunisia_tax_templates(company_name)
        
        # Step 3: Configure payment methods
        print("Step 3: Configuring payment methods...")
        configure_tunisia_payment_methods(company_name)
        
        # Step 4: Set up item defaults (limited to avoid timeout)
        print("Step 4: Setting up item defaults...")
        setup_tunisia_item_defaults(company_name)
        
        # Step 5: Create cost centers
        print("Step 5: Creating cost centers...")
        create_tunisia_cost_centers(company_name)
        
        # Step 6: Set up warehouse connections
        print("Step 6: Setting up warehouse connections...")
        setup_warehouse_account_connections(company_name)
        
        # Step 7: Comprehensive validation
        print("Step 7: Running comprehensive validation...")
        is_valid = validate_complete_tunisia_setup(company_name)
        
        frappe.db.commit()
        
        if is_valid:
            print("\n🎉 TUNISIA COA CONFIGURATION COMPLETED SUCCESSFULLY!")
            return {"success": True, "message": "Complete Tunisia configuration finished successfully"}
        else:
            print("\n⚠️  Configuration completed with some issues. Please review the validation report above.")
            return {"success": True, "message": "Configuration completed with some issues", "has_issues": True}
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Error during setup: {str(e)}"
        print(f"\n❌ {error_msg}")
        frappe.log_error(frappe.get_traceback(), "Tunisia COA Configuration Error")
        return {"success": False, "message": error_msg}


@frappe.whitelist()
def quick_validate_tunisia_setup(company_name=None):
    """Quick validation check for Tunisia setup"""
    
    if not company_name:
        company_name = frappe.defaults.get_user_default("Company")
    
    if not company_name:
        return {"success": False, "message": "No company specified"}
    
    print(f"🔍 Quick validation for {company_name}...")
    is_valid = validate_complete_tunisia_setup(company_name)
    
    return {
        "success": True, 
        "is_valid": is_valid,
        "message": "Validation completed" if is_valid else "Issues found in configuration"
    }


@frappe.whitelist()
def fix_tunisia_warehouse_accounts(company_name=None):
    """Standalone function to fix warehouse account issues"""
    
    if not company_name:
        company_name = frappe.defaults.get_user_default("Company")
    
    print(f"🔧 Fixing warehouse accounts for {company_name}...")
    
    try:
        # Enable perpetual inventory
        company = frappe.get_doc("Company", company_name)
        company.enable_perpetual_inventory = 1
        
        # Set critical warehouse accounts
        stock_account = f"37 - Stocks de marchandises - {company_name}"
        stock_liability_account = f"4081 - Fournisseurs d'exploitation - {company_name}"
        
        if frappe.db.exists("Account", stock_liability_account):
            company.stock_received_but_not_billed = stock_liability_account
            company.stock_liability_account = stock_liability_account
        
        company.save()
        
        # Fix warehouse connections
        setup_warehouse_account_connections(company_name)
        
        frappe.db.commit()
        print("✅ Warehouse account issues fixed!")
        return {"success": True, "message": "Warehouse accounts fixed successfully"}
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Error fixing warehouse accounts: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "message": error_msg} 