import type { Metadata } from "next";
import { Suspense } from "react";

import { publicationMetadata, PublicationView } from "@/components/content/publications";
import { Skeleton } from "@/components/ui/skeleton";

export async function generateMetadata({
  params,
}: PageProps<"/[lang]/articles/[slug]">): Promise<Metadata> {
  return publicationMetadata("articles", params);
}

export default function ArticlePage({ params }: PageProps<"/[lang]/articles/[slug]">) {
  return (
    <div className="px-4 py-10">
      <Suspense fallback={<Skeleton className="mx-auto h-96 max-w-3xl rounded-xl" />}>
        <PublicationView kind="articles" params={params} />
      </Suspense>
    </div>
  );
}
