import { supabase } from "./supabase";

export async function getLatestNewsletter() {
  const { data } = await supabase
    .from("newsletters")
    .select("*")
    .order("publish_date", { ascending: false })
    .limit(1)
    .single();

  return data;
}

export async function getArticles(newsletterId: string) {
  const { data } = await supabase
    .from("articles")
    .select("*")
    .eq("newsletter_id", newsletterId);

  return data;
}

export async function getInsights(newsletterId: string) {
  const { data } = await supabase
    .from("insights")
    .select("*")
    .eq("newsletter_id", newsletterId);

  return data;
}
