import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { register as registerApi } from "./auth-service";

const registerSchema = z
    .object({
        email: z.string().min(1, "Введите email").email("Некорректный email"),
        password: z.string().min(8, "Минимум 8 символов"),
        confirm_password: z.string().min(1, "Подтвердите пароль"),
    })
    .refine((data) => data.password === data.confirm_password, {
        message: "Пароли не совпадают",
        path: ["confirm_password"],
    });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
    const navigate = useNavigate();
    const [loading, set_loading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
    });

    const onSubmit = async (data: RegisterFormData) => {
        set_loading(true);
        try {
            await registerApi({ email: data.email, password: data.password });
            toast.success("Регистрация успешна. Теперь войдите.");
            void navigate({ to: "/login" });
        } catch (err: unknown) {
            const message =
                err && typeof err === "object" && "response" in err
                    ? ((err as { response?: { data?: { detail?: string } } }).response?.data
                          ?.detail ?? "Ошибка регистрации")
                    : "Ошибка сети";
            toast.error(message);
        } finally {
            set_loading(false);
        }
    };

    return (
        <Card className="w-full max-w-sm">
            <CardHeader className="text-center">
                <CardTitle className="text-2xl">Регистрация</CardTitle>
                <CardDescription>Создайте аккаунт в Marketplace</CardDescription>
            </CardHeader>
            <form onSubmit={(...args) => void handleSubmit(onSubmit)(...args)}>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="user@example.com"
                            autoComplete="email"
                            {...register("email")}
                        />
                        {errors.email && (
                            <p className="text-destructive text-sm">{errors.email.message}</p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="password">Пароль</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            autoComplete="new-password"
                            {...register("password")}
                        />
                        {errors.password && (
                            <p className="text-destructive text-sm">{errors.password.message}</p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="confirm_password">Подтверждение пароля</Label>
                        <Input
                            id="confirm_password"
                            type="password"
                            placeholder="••••••••"
                            autoComplete="new-password"
                            {...register("confirm_password")}
                        />
                        {errors.confirm_password && (
                            <p className="text-destructive text-sm">
                                {errors.confirm_password.message}
                            </p>
                        )}
                    </div>
                </CardContent>
                <CardFooter className="flex-col gap-4">
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? "Регистрация…" : "Зарегистрироваться"}
                    </Button>
                    <p className="text-muted-foreground text-sm">
                        Уже есть аккаунт?{" "}
                        <Link
                            to="/login"
                            className="hover:text-foreground underline underline-offset-4"
                        >
                            Войти
                        </Link>
                    </p>
                </CardFooter>
            </form>
        </Card>
    );
}
