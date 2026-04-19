import os
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient

load_dotenv()

# Test Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
result = supabase.table("asins").select("*").execute()
print("Supabase kết nối OK:", result)

# Test Apify
client = ApifyClient(os.getenv("APIFY_TOKEN"))
user = client.user().get()
print("Apify kết nối OK:", user["username"])