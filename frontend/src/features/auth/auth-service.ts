import { auth_client } from "@/lib/api-client";
import type { LoginRequest, RegisterRequest, TokenPair, UserProfile } from "@/types";

interface CheckCredentialsResponse {
    valid: boolean;
    user_id: string;
    role: string;
    is_admin: boolean;
    error: string | null;
}

export async function login(
    data: LoginRequest,
): Promise<{ tokens: TokenPair; profile: UserProfile }> {
    const response = await auth_client.post<TokenPair>("/auth/login", data);
    const tokens = response.data;

    // Получаем профиль через check_credentials (Bearer-токен)
    const cred_response = await auth_client.post<CheckCredentialsResponse>(
        "/auth/check_credentials",
        null,
        { headers: { Authorization: `Bearer ${tokens.access_token}` } },
    );

    const cred = cred_response.data;
    const profile: UserProfile = {
        id: cred.user_id,
        email: data.email, // email знаем из формы логина
        role: cred.role as UserProfile["role"],
        is_admin: cred.is_admin,
        timezone: "UTC",
        is_blocked: false,
    };

    return { tokens, profile };
}

export async function register(data: RegisterRequest): Promise<void> {
    await auth_client.post("/auth/register", data);
}

export async function refresh(refresh_token: string): Promise<TokenPair> {
    const response = await auth_client.post<TokenPair>("/auth/refresh", { refresh_token });
    return response.data;
}

export async function logout(access_token: string): Promise<void> {
    try {
        await auth_client.post(
            "/auth/logout",
            {},
            { headers: { Authorization: `Bearer ${access_token}` } },
        );
    } catch {
        // Игнорируем ошибку — токен всё равно очищаем на клиенте
    }
}
