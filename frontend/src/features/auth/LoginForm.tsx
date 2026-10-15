import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { useDispatch } from "react-redux";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { login as loginApi } from "./auth-service";
import { setProfile, setTokens } from "@/store/auth-slice";
import { useState } from "react";

interface QuickLogin {
    email: string;
    password: string;
    role: string;
    label: string;
}

const QUICK_LOGINS: QuickLogin[] = [
    { email: "superadmin@marketplace.dev", password: "SuperAdmin123!", role: "super_admin", label: "Супер-админ" },
    { email: "admin@marketplace.dev",       password: "Admin123!",      role: "admin",       label: "Админ" },
    { email: "moderator@marketplace.dev",   password: "Moderator123!",  role: "moderator",   label: "Модератор" },
    { email: "seller@marketplace.dev",      password: "Seller123!",     role: "seller",      label: "Продавец" },
    { email: "customer@marketplace.dev",    password: "Customer123!",   role: "customer",    label: "Покупатель" },
    { email: "customer2@marketplace.dev",   password: "Customer123!",   role: "customer",    label: "Покупатель 2" },
];

const loginSchema = z.object({
    email: z.string().min(1, "Введите email").email("Некорректный email"),
    password: z.string().min(1, "Введите пароль"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
    const navigate = useNavigate();
    const dispatch = useDispatch();
    const [loading, set_loading] = useState(false);

    const {
        register,
        handleSubmit,
        setValue,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
    });

    const doLogin = async (email: string, password: string) => {
        set_loading(true);
        try {
            const { tokens, profile } = await loginApi({ email, password });
            dispatch(setTokens({ access: tokens.access_token, refresh: tokens.refresh_token }));
            dispatch(setProfile(profile));
            toast.success("Вход выполнен");
            void navigate({ to: "/" });
        } catch (err: unknown) {
            const message =
                err && typeof err === "object" && "response" in err
                    ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Ошибка входа")
                    : "Ошибка сети";
            toast.error(message);
        } finally {
            set_loading(false);
        }
    };

    const onSubmit = (data: LoginFormData) => doLogin(data.email, data.password);

    const quickLogin = (ql: QuickLogin) => {
        setValue("email", ql.email);
        setValue("password", ql.password);
        void doLogin(ql.email, ql.password);
    };

    return (
        <Card className="w-full max-w-sm">
            <CardHeader className="text-center">
                <CardTitle className="text-2xl">Вход</CardTitle>
                <CardDescription>Войдите в свой аккаунт Marketplace</CardDescription>
            </CardHeader>
            <form onSubmit={(...args) => void handleSubmit(onSubmit)(...args)}>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="user@marketplace.dev"
                            autoComplete="email"
                            {...register("email")}
                        />
                        {errors.email && (
                            <p className="text-sm text-destructive">{errors.email.message}</p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="password">Пароль</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            autoComplete="current-password"
                            {...register("password")}
                        />
                        {errors.password && (
                            <p className="text-sm text-destructive">{errors.password.message}</p>
                        )}
                    </div>
                </CardContent>
                <CardFooter className="flex-col gap-4">
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? "Вход…" : "Войти"}
                    </Button>

                    {/* Быстрый вход — только в DEV-режиме */}
                    {import.meta.env.DEV && (
                        <div className="w-full space-y-2">
                            <p className="text-xs text-muted-foreground text-center">Быстрый вход:</p>
                            <div className="grid grid-cols-2 gap-1.5">
                                {QUICK_LOGINS.map((ql) => (
                                    <Button
                                        key={ql.email}
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        disabled={loading}
                                        onClick={() => quickLogin(ql)}
                                        className="h-auto flex-col gap-0.5 py-2 text-xs"
                                    >
                                        <span className="font-medium">{ql.label}</span>
                                        <Badge variant="secondary" className="text-[10px] h-4 px-1">
                                            {ql.role}
                                        </Badge>
                                    </Button>
                                ))}
                            </div>
                        </div>
                    )}

                    <p className="text-sm text-muted-foreground">
                        Нет аккаунта?{" "}
                        <Link
                            to="/register"
                            className="underline underline-offset-4 hover:text-foreground"
                        >
                            Зарегистрироваться
                        </Link>
                    </p>
                </CardFooter>
            </form>
        </Card>
    );
}
