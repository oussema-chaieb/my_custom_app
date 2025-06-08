frappe.ui.form.on('Landed Cost Voucher', {
    refresh: function(frm) {
        // Run calculations on refresh
        calculate_ngp_distribution(frm);
    },
    
    // Recalculate when any relevant field changes
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

// Add triggers for the taxes child table
frappe.ui.form.on('Landed Cost Taxes and Charges', {
    amount: function(frm) {
        // Use setTimeout to ensure form data is fully updated
        setTimeout(function() {
            calculate_ngp_distribution(frm);
        }, 100);
    },
    expense_account: function(frm) {
        calculate_ngp_distribution(frm);
    },
    custom_ngp_code: function(frm) {
        calculate_ngp_distribution(frm);
    },
    taxes_remove: function(frm) {
        calculate_ngp_distribution(frm);
    }
});

// Cache for storing item NGP codes to avoid repeated DB calls
const ngpCodeCache = {};

function calculate_ngp_distribution(frm) {
    if (!frm.doc.taxes || frm.doc.taxes.length === 0 || !frm.doc.items || frm.doc.items.length === 0) {
        return;
    }
    
    // Reset applicable charges
    frm.doc.items.forEach(function(item) {
        item.applicable_charges = 0;
    });
    frm.refresh_field('items');
    
    // Calculate initial totals
    let original_stock_value = 0;
    frm.doc.items.forEach(function(item) {
        original_stock_value += item.amount;
    });
    
    let all_debug_messages = [];
    let promise_chain = Promise.resolve();
    
    // First, pre-load all item NGP codes into cache
    const item_codes = frm.doc.items.map(item => item.item_code).filter(Boolean);
    const uncached_item_codes = item_codes.filter(code => !ngpCodeCache[code]);
    
    if (uncached_item_codes.length > 0) {
        promise_chain = promise_chain.then(() => {
            return new Promise((resolve) => {
                const promises = uncached_item_codes.map(item_code => {
                    return frappe.db.get_value('Item', item_code, 'custom_ngp_code')
                    .then(r => {
                        if (r.message) {
                            ngpCodeCache[item_code] = r.message.custom_ngp_code;
                        } else {
                            ngpCodeCache[item_code] = null;
                        }
                    });
                });
                
                Promise.all(promises).then(() => {
                    resolve();
                });
            });
        });
    }
    
    // Process each tax sequentially
    frm.doc.taxes.forEach(function(tax, tax_index) {
        promise_chain = promise_chain.then(() => {
            return new Promise((resolve) => {
                if (!tax.amount || tax.amount <= 0) {
                    resolve();
                    return;
                }
                
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
                    
                    frm.doc.items.forEach(function(item) {
                        const item_ngp_code = ngpCodeCache[item.item_code];
                        if (item_ngp_code === current_ngp_code) {
                            items_with_ngp.push(item);
                            all_debug_messages.push(`Article trouvé avec NGP: ${item.item_code}`);
                        }
                    });
                    
                    // If no matching NGP items, skip to next tax
                    if (items_with_ngp.length === 0) {
                        all_debug_messages.push(`Aucun article trouvé pour le code NGP ${current_ngp_code}`);
                        resolve();
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
                        resolve();
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
                    resolve();
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
                    
                    if (distribution_base === 0) {
                        resolve();
                        return;
                    }
                    
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
                    resolve();
                }
            });
        });
    });
    
    // After all taxes are processed, show summary
    promise_chain.then(() => {
        // Calculate final totals
        let total_applied_charges = 0;
        let final_value = 0;
        
        frm.doc.items.forEach(function(item) {
            total_applied_charges += item.applicable_charges;
            final_value += item.amount + item.applicable_charges;
        });
        
        // Show a small status indicator instead of a full alert
        frappe.show_alert({
            message: `Charges calculées: ${Math.round(total_applied_charges * 100) / 100}`,
            indicator: 'green'
        }, 3);
    });
} 