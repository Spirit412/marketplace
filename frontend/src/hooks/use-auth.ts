import { useDispatch, useSelector } from "react-redux";
import { useCallback } from "react";
import type { AppDispatch, RootState } from "@/store";
import { clearAuth, setProfile, setTokens } from "@/store/auth-slice";
import type { TokenPair, UserProfile } from "@/types";

/**
 * Хук аутентификации.
 * Возвращает состояние + функции login/logout.
 */
export function useAuth() {
    const dispatch = useDispatch<AppDispatch>();
    const is_authenticated = useSelector((s: RootState) => s.auth.is_authenticated);
    const profile = useSelector((s: RootState) => s.auth.profile);
    const access_token = useSelector((s: RootState) => s.auth.access_token);

    const login = useCallback(
        (tokens: TokenPair, user_profile: UserProfile) => {
            dispatch(setTokens({ access: tokens.access_token, refresh: tokens.refresh_token }));
            dispatch(setProfile(user_profile));
        },
        [dispatch],
    );

    const logout = useCallback(() => {
        dispatch(clearAuth());
    }, [dispatch]);

    return {
        is_authenticated,
        profile,
        access_token,
        login,
        logout,
    };
}
