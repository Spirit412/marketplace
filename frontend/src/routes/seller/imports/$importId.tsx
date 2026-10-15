import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/seller/imports/$importId")({
    component: Page,
});

function Page() {
    return (
        <div className="space-y-4">
            <h1 className="text-2xl font-bold tracking-tight">Детали импорта</h1>
            <p className="text-muted-foreground">Раздел в разработке.</p>
        </div>
    );
}
