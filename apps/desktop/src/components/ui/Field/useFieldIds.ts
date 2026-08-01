import { useId } from "react";

interface UseFieldIdsOptions {
  description?: unknown;
  error?: unknown;
  id?: string;
}

export interface FieldIds {
  controlId: string;
  descriptionId?: string;
  errorId?: string;
}

export function useFieldIds({ description, error, id }: UseFieldIdsOptions): FieldIds {
  const generatedId = useId();
  const controlId = id ?? generatedId;

  return {
    controlId,
    descriptionId: description ? `${controlId}-description` : undefined,
    errorId: error ? `${controlId}-error` : undefined,
  };
}
