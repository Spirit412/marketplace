import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { CartItem } from "@/types";

interface CartState {
    items: CartItem[];
}

const initialState: CartState = { items: [] };

const cartSlice = createSlice({
    name: "cart",
    initialState,
    reducers: {
        addItem(state, action: PayloadAction<CartItem>) {
            const existing = state.items.find((i) => i.product_id === action.payload.product_id);
            if (existing) {
                existing.quantity += action.payload.quantity;
            } else {
                state.items.push(action.payload);
            }
        },
        removeItem(state, action: PayloadAction<string>) {
            state.items = state.items.filter((i) => i.product_id !== action.payload);
        },
        updateQuantity(state, action: PayloadAction<{ product_id: string; quantity: number }>) {
            const item = state.items.find((i) => i.product_id === action.payload.product_id);
            if (item) {
                if (action.payload.quantity <= 0) {
                    state.items = state.items.filter(
                        (i) => i.product_id !== action.payload.product_id,
                    );
                } else {
                    item.quantity = action.payload.quantity;
                }
            }
        },
        clearCart(state) {
            state.items = [];
        },
    },
});

export const { addItem, removeItem, updateQuantity, clearCart } = cartSlice.actions;

export const selectCartItems = (state: { cart: CartState }) => state.cart.items;
export const selectCartTotal = (state: { cart: CartState }) =>
    state.cart.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
export const selectCartCount = (state: { cart: CartState }) =>
    state.cart.items.reduce((sum, i) => sum + i.quantity, 0);

export default cartSlice.reducer;
