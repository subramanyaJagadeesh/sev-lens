export type KnowledgeDocument = {
  document_id: string;
  title: string;
  doc_type: string;
  content: string;
  service: string | null;
  tags: string[];
  source: string | null;
  archived: boolean;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  indexed_at: string | null;
  chunk_count: number;
  chunk_ids: string[];
};

export type KnowledgeChunk = {
  chunk_id: string;
  document_id: string;
  title: string;
  doc_type: string;
  text: string;
  chunk_index: number;
  service: string | null;
  tags: string[];
  source: string | null;
  metadata: Record<string, unknown>;
};

export type KnowledgeDocumentDetail = {
  document: KnowledgeDocument;
  chunks: KnowledgeChunk[];
};

export type KnowledgeSearchResult = {
  document_id: string;
  title: string;
  doc_type: string;
  text: string;
  score: number;
  service: string | null;
  tags: string[];
  source: string | null;
  chunk_index: number;
  metadata: Record<string, unknown>;
};

export type KnowledgeDocumentCreatePayload = {
  document_id: string;
  title: string;
  doc_type: string;
  content: string;
  service?: string | null;
  tags?: string[];
  source?: string | null;
  metadata?: Record<string, unknown>;
};

export type KnowledgeDocumentUpdatePayload = {
  title?: string;
  doc_type?: string;
  content?: string;
  service?: string | null;
  tags?: string[];
  source?: string | null;
  archived?: boolean;
  metadata?: Record<string, unknown>;
};

export type KnowledgeSearchPayload = {
  query: string;
  top_k?: number;
  service_name?: string | null;
  doc_types?: string[] | null;
  tags?: string[] | null;
};
