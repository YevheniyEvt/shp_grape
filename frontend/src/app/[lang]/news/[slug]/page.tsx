import type { Metadata } from "next";
import { Suspense } from "react";

import { publicationMetadata, PublicationView } from "@/components/content/publications";
import { Skeleton } from "@/components/ui/skeleton";

export async function generateMetadata({
  params,
}: PageProps<"/[lang]/news/[slug]">): Promise<Metadata> {
  return publicationMetadata("news", params);
}

export default function NewsItemPage({ params }: PageProps<"/[lang]/news/[slug]">) {
  return (
    <div className="px-4 py-10">
      <Suspense fallback={<Skeleton className="mx-auto h-96 max-w-3xl rounded-xl" />}>
        <PublicationView kind="news" params={params} />
      </Suspense>
    </div>
  );
}
