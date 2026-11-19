"use client";

import LiteYouTubeEmbed from "react-lite-youtube-embed";
import "react-lite-youtube-embed/dist/LiteYouTubeEmbed.css";

export type YouTubeVideo = { id: number; youtube_id: string; title?: string };

/**
 * YouTube videos as light previews: the real player (and YouTube's cookies) loads only
 * after a click, which keeps the page fast.
 */
export function YouTubeVideos({
  videos,
  fallbackTitle,
}: {
  videos: YouTubeVideo[];
  fallbackTitle: string;
}) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {videos.map((video) => (
        <li key={video.id} className="overflow-hidden rounded-xl">
          <LiteYouTubeEmbed id={video.youtube_id} title={video.title || fallbackTitle} noCookie />
          {video.title && <p className="mt-2 text-sm font-medium">{video.title}</p>}
        </li>
      ))}
    </ul>
  );
}
