import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const plans: Record<number, any[]> = {
  3: [
    { day: "Day 1", title: "Accra Heritage & Tafi Atome", activities: ["Black Star Square", "Tafi Atome Monkey Sanctuary", "Local lunch in Hohoe"] },
    { day: "Day 2", title: "Winneba & Cape Coast", activities: ["Aboakyer Festival traditions", "Cape Coast Castle tour", "Ocean sunset"] },
    { day: "Day 3", title: "Crafts & Markets", activities: ["Accra Arts Centre", "Kente cloth shopping", "Farewell Jollof & Highlife evening"] },
  ],
  7: [
    { day: "Days 1-2", title: "Accra & Central Coast Fortresses", activities: ["Accra monuments", "Cape Coast Castle", "Kakum Canopy Walk", "Elmina Castle"] },
    { day: "Days 3-4", title: "Boabeng-Fiema & Ashanti Culture", activities: ["Boabeng-Fiema Monkey Sanctuary", "Manhyia Palace Museum", "Bonwire Kente Village"] },
    { day: "Days 5-7", title: "Volta Region Adventures", activities: ["Tafi Atome Monkeys", "Wli Waterfalls", "Mount Afadjato summit"] },
  ],
  14: [
    { day: "Week 1", title: "Coastal Fortresses & Kumasi Heritage", activities: ["Accra", "Cape Coast", "Kakum", "Boabeng-Fiema", "Kumasi Royal Heritage"] },
    { day: "Week 2", title: "Northern Safaris & Volta Waterfalls", activities: ["Tamale Damba", "Mole Elephant Safari", "Paga Crocodiles", "Tafi Atome", "Wli Waterfalls"] },
  ],
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ success: false, error: "Method not allowed" }), {
      status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
  try {
    const body = await req.json();
    const days = Number(body.days || 7);
    const style = body.style || "balanced";
    const plan = plans[days] || plans[14];
    const payload = { success: true, data: { days, style, plan } };
    return new Response(JSON.stringify(payload), {
      status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ success: false, error: "Bad request" }), {
      status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
