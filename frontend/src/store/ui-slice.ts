import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

type Theme = "light" | "dark" | "system";

interface UIState {
    theme: Theme;
    sidebar_open: boolean;
    active_modal: string | null;
}

const initialState: UIState = {
    theme: "system",
    sidebar_open: true,
    active_modal: null,
};

const uiSlice = createSlice({
    name: "ui",
    initialState,
    reducers: {
        setTheme(state, action: PayloadAction<Theme>) {
            state.theme = action.payload;
        },
        toggleSidebar(state) {
            state.sidebar_open = !state.sidebar_open;
        },
        openModal(state, action: PayloadAction<string>) {
            state.active_modal = action.payload;
        },
        closeModal(state) {
            state.active_modal = null;
        },
    },
});

export const { setTheme, toggleSidebar, openModal, closeModal } = uiSlice.actions;
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export default uiSlice.reducer;
