import { createFileRoute } from "@tanstack/react-router";
import { RegisterForm } from "@/features/auth/RegisterForm";

export const Route = createFileRoute("/register")({
    component: RegisterPage,
});

function RegisterPage() {
    return (
        <div className="bg-muted/30 flex min-h-screen items-center justify-center p-4">
            <RegisterForm />
        </div>
    );
}
