import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/admin/users/")({
    component: Page,
});

function Page() {
    return (
        <div className="space-y-4">
            <h1 className="text-2xl font-bold tracking-tight">Users</h1>
            <p className="text-muted-foreground">Раздел в разработке.</p>
        </div>
    );
}
