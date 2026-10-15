import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { UserProfile } from "@/types";

interface AuthState {
    access_token: string | null;
    refresh_token: string | null;
    profile: UserProfile | null;
    is_authenticated: boolean;
}

const initialState: AuthState = {
    access_token: null,
    refresh_token: null,
    profile: null,
    is_authenticated: false,
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setTokens(state, action: PayloadAction<{ access: string; refresh: string }>) {
            state.access_token = action.payload.access;
            state.refresh_token = action.payload.refresh;
            state.is_authenticated = true;
        },
        setProfile(state, action: PayloadAction<UserProfile>) {
            state.profile = action.payload;
        },
        clearAuth(state) {
            state.access_token = null;
            state.refresh_token = null;
            state.profile = null;
            state.is_authenticated = false;
        },
    },
});

export const { setTokens, setProfile, clearAuth } = authSlice.actions;
export default authSlice.reducer;
