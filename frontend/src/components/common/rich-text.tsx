import { cn } from "@/lib/utils";

/**
 * HTML from the admin rich-text editor, styled by @tailwindcss/typography.
 *
 * Safe to inject: the backend sanitizes it with nh3 against the editor's allow-list.
 */
export function RichText({ html, className }: { html: string; className?: string }) {
  if (!html) return null;
  return (
    <div
      className={cn(
        "prose max-w-none prose-neutral dark:prose-invert prose-headings:font-heading prose-a:text-primary",
        className,
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
