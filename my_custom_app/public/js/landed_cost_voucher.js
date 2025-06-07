frappe.ui.form.on('Landed Cost Voucher', {
    refresh: function(frm) {
        // Add a custom button to calculate charges without saving
        frm.add_custom_button(__('Calculate Charges'), function() {
            calculate_ngp_distribution(frm);
        });
    },
    
    // Optional: Recalculate when taxes or items change
    taxes_add: function(frm) {
        calculate_ngp_distribution(frm);
    },
    taxes_remove: function(frm) {
        calculate_ngp_distribution(frm);
    },
    items_add: function(frm) {
        calculate_ngp_distribution(frm);
    },
    items_remove: function(frm) {
        calculate_ngp_distribution(frm);
    },
    distribute_charges_based_on: function(frm) {
        calculate_ngp_distribution(frm);
    }
});

function calculate_ngp_distribution(frm) {
    if (!frm.doc.taxes || frm.doc.taxes.length === 0 || !frm.doc.items || frm.doc.items.length === 0) {
        return;
    }
    
    // Reset applicable charges
    frm.doc.items.forEach(function(item) {
        item.applicable_charges = 0;
    });
    
    // Calculate initial totals
    let original_stock_value = 0;
    frm.doc.items.forEach(function(item) {
        original_stock_value += item.amount;
    });
    
    let all_debug_messages = [];
    
    // Process NGP and non-NGP taxes separately
    frm.doc.taxes.forEach(function(tax) {
        let current_amount = tax.amount;
        
        if (tax.expense_account && tax.expense_account.toLowerCase().includes('ngp') && tax.custom_ngp_code) {
            // NGP tax processing
            let current_ngp_code = tax.custom_ngp_code;
            
            all_debug_messages.push("=== TRAITEMENT TAXE NGP ===");
            all_debug_messages.push(`Code NGP: ${current_ngp_code}`);
            all_debug_messages.push(`Montant: ${current_amount}`);
            all_debug_messages.push(`Compte: ${tax.expense_account}`);
            
            // Get items with matching NGP codes
            let items_with_ngp = [];
            let promises = [];
            
            frm.doc.items.forEach(function(item) {
                promises.push(
                    frappe.db.get_value('Item', item.item_code, 'custom_ngp_code')
                    .then(r => {
                        if (r.message && r.message.custom_ngp_code === current_ngp_code) {
                            items_with_ngp.push(item);
                            all_debug_messages.push(`Article trouvé avec NGP: ${item.item_code}`);
                        }
                    })
                );
            });
            
            Promise.all(promises).then(() => {
                // If no matching NGP items, skip to next tax
                if (items_with_ngp.length === 0) {
                    all_debug_messages.push(`Aucun article trouvé pour le code NGP ${current_ngp_code}`);
                    return;
                }
                
                // Distribution only to NGP items
                let distribution_base = 0;
                let is_amount_based = frm.doc.distribute_charges_based_on === "Amount";
                
                // Calculate distribution base
                items_with_ngp.forEach(function(item) {
                    if (is_amount_based) {
                        distribution_base += item.amount;
                    } else {
                        distribution_base += item.qty;
                    }
                });
                
                if (distribution_base === 0) {
                    return;
                }
                
                // Proportional distribution to NGP items
                let total_distributed = 0;
                let last_item = items_with_ngp[items_with_ngp.length - 1];
                
                items_with_ngp.forEach(function(item) {
                    let charge;
                    if (item === last_item) {
                        // For the last item, assign the remainder to avoid rounding errors
                        charge = current_amount - total_distributed;
                    } else {
                        let proportion;
                        if (is_amount_based) {
                            proportion = item.amount / distribution_base;
                        } else {
                            proportion = item.qty / distribution_base;
                        }
                        charge = Math.round(proportion * current_amount * 100) / 100;
                        total_distributed += charge;
                    }
                    
                    item.applicable_charges += charge;
                    all_debug_messages.push(`Répartition NGP pour ${item.item_code}: ${charge}`);
                });
                
                frm.refresh_field('items');
                update_summary(frm, original_stock_value, all_debug_messages);
            });
        } else {
            // Standard processing for non-NGP taxes
            all_debug_messages.push("=== TRAITEMENT TAXE STANDARD ===");
            all_debug_messages.push(`Montant: ${current_amount}`);
            all_debug_messages.push(`Compte: ${tax.expense_account || 'Non spécifié'}`);
            
            // Standard distribution for all lines
            let distribution_base = 0;
            let is_amount_based = frm.doc.distribute_charges_based_on === "Amount";
            
            // Calculate total base
            frm.doc.items.forEach(function(item) {
                if (is_amount_based) {
                    distribution_base += item.amount;
                } else {
                    distribution_base += item.qty;
                }
            });
            
            // Proportional distribution
            let total_distributed = 0;
            let last_item = frm.doc.items[frm.doc.items.length - 1];
            
            frm.doc.items.forEach(function(item) {
                let charge;
                if (item === last_item) {
                    // For the last item, assign the remainder
                    charge = current_amount - total_distributed;
                } else {
                    let proportion;
                    if (is_amount_based) {
                        proportion = item.amount / distribution_base;
                    } else {
                        proportion = item.qty / distribution_base;
                    }
                    charge = Math.round(proportion * current_amount * 100) / 100;
                    total_distributed += charge;
                }
                
                item.applicable_charges += charge;
                all_debug_messages.push(`Répartition standard pour ${item.item_code}: ${charge}`);
            });
            
            frm.refresh_field('items');
            update_summary(frm, original_stock_value, all_debug_messages);
        }
    });
}

function update_summary(frm, original_stock_value, all_debug_messages) {
    // Calculate final totals
    let total_applied_charges = 0;
    let final_value = 0;
    
    frm.doc.items.forEach(function(item) {
        total_applied_charges += item.applicable_charges;
        final_value += item.amount + item.applicable_charges;
    });
    
    // Display results
    frappe.show_alert({
        message: `<b>=== VÉRIFICATION FINALE ===</b><br>
                 Valeur initiale: ${Math.round(original_stock_value * 100) / 100}<br>
                 Charges totales: ${Math.round(total_applied_charges * 100) / 100}<br>
                 Valeur finale: ${Math.round(final_value * 100) / 100}`,
        indicator: 'green'
    }, 10);
    
    // Optional: show detailed calculation
    if (all_debug_messages.length > 0) {
        frm.add_custom_button(__('Voir les détails de calcul'), function() {
            frappe.msgprint(all_debug_messages.join('<br>'), {
                title: 'Détails de calcul'
            });
        });
    }
} 