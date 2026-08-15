export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  searchPerformed?: boolean;
  searchQuery?: string;
  sources?: SearchSource[];
}

export interface SearchSource {
  title: string;
  url: string;
  snippet: string;
  source: string;  // domain name
}
