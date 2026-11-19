import { Skeleton } from "@/components/ui/skeleton";

/** Placeholder cards shown while a list of varieties loads. */
export function CardGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
          <Skeleton className="aspect-4/3 rounded-none" />
          <div className="grid gap-3 p-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Whole catalog area: alphabet, toolbar, filter sidebar and cards. */
export function CatalogSkeleton() {
  return (
    <div className="grid gap-6" data-testid="catalog-skeleton">
      <Skeleton className="mx-auto h-7 w-full max-w-3xl" />
      <div className="flex flex-wrap gap-3">
        <Skeleton className="h-9 w-full sm:w-72" />
        <Skeleton className="ml-auto h-9 w-56" />
      </div>
      <div className="flex gap-8">
        <div className="hidden w-64 shrink-0 gap-4 lg:grid">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-24" />
          ))}
        </div>
        <div className="flex-1">
          <CardGridSkeleton />
        </div>
      </div>
    </div>
  );
}
