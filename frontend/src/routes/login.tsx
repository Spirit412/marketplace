import { createFileRoute } from "@tanstack/react-router";
import { LoginForm } from "@/features/auth/LoginForm";

export const Route = createFileRoute("/login")({
    component: LoginPage,
});

function LoginPage() {
    return (
        <div className="bg-muted/30 flex min-h-screen items-center justify-center p-4">
            <LoginForm />
        </div>
    );
}
