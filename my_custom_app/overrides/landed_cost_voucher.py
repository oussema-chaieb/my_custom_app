import frappe
from frappe import _

def custom_distribute_charges_by_ngp(doc, method=None):
    """
    Custom method to distribute landed cost based on NGP codes
    To be called from hooks.py before_validate for Landed Cost Voucher
    """
    # Réinitialiser les charges applicables
    for item in doc.items:
        item.applicable_charges = 0

    # Calculer les totaux initiaux
    original_stock_value = 0
    for item in doc.items:
        original_stock_value = original_stock_value + item.amount

    all_debug_messages = []

    # Traiter séparément les taxes NGP et non-NGP
    for tax in doc.taxes:
        current_amount = tax.amount
        
        if tax.expense_account and "ngp" in tax.expense_account.lower() and tax.custom_ngp_code:
            # Traitement des taxes NGP
            current_ngp_code = tax.custom_ngp_code
            
            all_debug_messages.append("=== TRAITEMENT TAXE NGP ===")
            all_debug_messages.append(f"Code NGP: {current_ngp_code}")
            all_debug_messages.append(f"Montant: {current_amount}")
            all_debug_messages.append(f"Compte: {tax.expense_account}")
            
            # Identifier les articles avec ce code NGP
            items_with_ngp = []
            for item in doc.items:
                try:
                    item_doc = frappe.get_doc("Item", item.item_code)
                    if item_doc.get("custom_ngp_code") == current_ngp_code:
                        items_with_ngp.append(item)
                        all_debug_messages.append(f"Article trouvé avec NGP: {item.item_code}")
                except Exception:
                    pass

            # Si aucun article NGP trouvé, on passe à la taxe suivante
            if not items_with_ngp:
                all_debug_messages.append(f"Aucun article trouvé pour le code NGP {current_ngp_code}")
                continue

            # Distribution uniquement aux articles NGP
            distribution_base = 0
            is_amount_based = doc.distribute_charges_based_on == "Amount"
            
            # Calculer la base de distribution
            for item in items_with_ngp:
                if is_amount_based:
                    distribution_base = distribution_base + item.amount
                else:
                    distribution_base = distribution_base + item.qty

            if distribution_base == 0:
                continue

            # Distribution proportionnelle aux articles NGP
            total_distributed = 0
            last_item = items_with_ngp[-1]

            for item in items_with_ngp:
                if item == last_item:
                    # Pour le dernier article, on attribue le reste pour éviter les écarts d'arrondi
                    charge = current_amount - total_distributed
                else:
                    if is_amount_based:
                        proportion = item.amount / distribution_base
                    else:
                        proportion = item.qty / distribution_base
                    charge = round(proportion * current_amount, 2)
                    total_distributed = total_distributed + charge

                item.applicable_charges = item.applicable_charges + charge
                all_debug_messages.append(f"Répartition NGP pour {item.item_code}: {charge}")
                
        else:
            # Traitement standard pour les taxes non-NGP
            all_debug_messages.append("=== TRAITEMENT TAXE STANDARD ===")
            all_debug_messages.append(f"Montant: {current_amount}")
            all_debug_messages.append(f"Compte: {tax.expense_account}")
            
            # Distribution standard pour toutes les lignes
            distribution_base = 0
            is_amount_based = doc.distribute_charges_based_on == "Amount"
            
            # Calculer la base totale
            for item in doc.items:
                if is_amount_based:
                    distribution_base = distribution_base + item.amount
                else:
                    distribution_base = distribution_base + item.qty

            # Distribution proportionnelle
            total_distributed = 0
            last_item = doc.items[-1]

            for item in doc.items:
                if item == last_item:
                    # Pour le dernier article, on attribue le reste
                    charge = current_amount - total_distributed
                else:
                    if is_amount_based:
                        proportion = item.amount / distribution_base
                    else:
                        proportion = item.qty / distribution_base
                    charge = round(proportion * current_amount, 2)
                    total_distributed = total_distributed + charge

                item.applicable_charges = item.applicable_charges + charge
                all_debug_messages.append(f"Répartition standard pour {item.item_code}: {charge}")

    # Calculer les totaux finaux
    total_applied_charges = 0
    final_value = 0
    for item in doc.items:
        total_applied_charges = total_applied_charges + item.applicable_charges
        final_value = final_value + item.amount + item.applicable_charges

    # Afficher les résultats
    frappe.msgprint(
        f"""=== VÉRIFICATION FINALE ===
Valeur initiale: {round(original_stock_value, 2)}
Charges totales: {round(total_applied_charges, 2)}
Valeur finale: {round(final_value, 2)}""",
        title='Débug Final'
    )

    if all_debug_messages:
        frappe.msgprint("\n".join(all_debug_messages), title='Détails de calcul')

    frappe.msgprint(
        f"""=== ÉCRITURES COMPTABLES PRÉVUES ===
DÉBIT:
- Stock: {round(final_value, 2)}

CRÉDIT:
- Charges: {round(total_applied_charges, 2)}
- Stock initial: {round(original_stock_value, 2)}""",
        title='Écritures Comptables'
    ) 