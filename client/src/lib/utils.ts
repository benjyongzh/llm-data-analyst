import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { MessageContent } from "./api"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatMessageContents(contents: MessageContent[]): string {
  return contents
    .map((c) => (c.type === "text" ? c.content : JSON.stringify(c.content, null, 2)))
    .join("\n")
}
