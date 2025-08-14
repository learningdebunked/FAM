import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function for merging class names.
 * 
 * @param inputs - Variable number of class names to merge.
 * @returns The merged class name.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
