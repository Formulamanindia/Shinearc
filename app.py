with st.container(border=True):
            st.markdown("#### Move Material")
            c1, c2, c3 = st.columns(3)
            stages = db.get_stages_for_item(lot['item_name'])
            
            # Select Source Stage
            from_s = c1.selectbox("From", list(lot['current_stage_stock'].keys()))
            
            # Select Destination Stage
            to_s = c2.selectbox("To", stages)
            
            # Assign Karigar
            kar = c3.selectbox("Karigar", ["Karigar A", "Karigar B", "Karigar C", "Outsource"])
            
            c4, c5, c6 = st.columns(3)
            
            # Get Available Sizes for the Selected 'From' Stage
            avail = lot['current_stage_stock'].get(from_s, {})
            
            # Filter out sizes with 0 quantity to prevent errors
            valid_sizes = [k for k, v in avail.items() if v > 0]
            
            if valid_sizes:
                sz = c4.selectbox("Size", valid_sizes)
                max_q = avail.get(sz, 0)
                
                # --- SAFETY FIX HERE ---
                # Only show number input if max_q is at least 1
                if max_q >= 1:
                    qty = c5.number_input("Qty", min_value=1, max_value=max_q, value=1)
                else:
                    qty = 0
                    c5.warning("0 stock available")
                
                c6.markdown("<br>", unsafe_allow_html=True)
                if c6.button("Confirm Move"):
                    if qty > 0:
                        if db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage": to_s, "karigar": kar, "machine": "N/A", "size": sz, "qty": qty}):
                            st.success(f"Moved {qty} pcs of {sz}!")
                            st.rerun()
                    else:
                        st.error("Qty must be greater than 0")
            else:
                c4.warning("No stock available to move from this stage.")
