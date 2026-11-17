import { z } from "zod";

import { queryStoreData, storeQuerySchema } from "@/lib/analytics";

/**
 * POST /api/analytics/query
 * Body: a `StoreQueryInput` JSON object. Returns a `StoreQueryResult`.
 */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Request body must be valid JSON." }, { status: 400 });
  }

  const parsed = storeQuerySchema.safeParse(body);
  if (!parsed.success) {
    return Response.json(
      { error: "Invalid query.", issues: z.flattenError(parsed.error) },
      { status: 400 },
    );
  }

  return Response.json(queryStoreData(parsed.data));
}
