import { Skeleton } from "@/components/ui/skeleton";

export function VarietyDetailsSkeleton() {
  return (
    <div className="grid gap-10" aria-hidden="true">
      <Skeleton className="h-5 w-64" />
      <div className="grid gap-8 lg:grid-cols-2">
        <Skeleton className="aspect-4/3 w-full rounded-xl" />
        <div className="grid content-start gap-4">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-36 w-full rounded-xl" />
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-6 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
