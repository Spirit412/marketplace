import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/seller/products/new")({
    component: Page,
});

function Page() {
    return (
        <div className="space-y-4">
            <h1 className="text-2xl font-bold tracking-tight">Новый товар</h1>
            <p className="text-muted-foreground">Раздел в разработке.</p>
        </div>
    );
}
