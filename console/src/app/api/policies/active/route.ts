import { NextResponse } from "next/server";
import { backendFetch, handleApiError } from "@/lib/api-client";

export async function GET() {
  try {
    const data = await backendFetch("/v1/policies/active");
    return NextResponse.json(data);
  } catch (error: any) {
    if (error.message?.includes("Unauthorized")) {
      return handleApiError(error);
    }
    // Return empty string or 404 cleanly so UI doesn't crash if no policies exist yet
    return NextResponse.json({ error: error.message }, { status: 404 });
  }
}
