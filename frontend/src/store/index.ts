import { combineReducers, configureStore } from "@reduxjs/toolkit";
import { persistReducer, persistStore } from "redux-persist";
import authReducer from "./auth-slice";
import cartReducer from "./cart-slice";
import uiReducer from "./ui-slice";

const storage = {
    getItem(key: string) {
        return Promise.resolve(localStorage.getItem(key));
    },
    setItem(key: string, value: string) {
        return Promise.resolve(localStorage.setItem(key, value));
    },
    removeItem(key: string) {
        return Promise.resolve(localStorage.removeItem(key));
    },
};

const rootReducer = combineReducers({
    auth: authReducer,
    cart: cartReducer,
    ui: uiReducer,
});

const persistConfig = {
    key: "marketplace",
    storage,
    whitelist: ["auth", "ui"],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({ serializableCheck: false }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
