import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "VeriMed",
    short_name: "VeriMed",
    description: "AI-powered medicine authenticity risk assessment tool.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#f8fbff",
    theme_color: "#0ea5e9",
    orientation: "portrait",
    icons: [
      {
        src: "/verimed-og.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/verimed-og.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
