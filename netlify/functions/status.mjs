import { loadModel } from '../lib/model.mjs';
export default async function () {
  try {
    loadModel();
    return Response.json({ model_ready: true, experimental: true }, { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ model_ready: false, experimental: true }, { status: 503 });
  }
}
