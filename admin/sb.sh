CONN="postgresql://postgres.dzpdualvwspgqghrysyz:IemPCUydbbSg2NFvnNve@aws-1-us-west-1.pooler.supabase.com:5432/postgres"

if [ -n "$1" ]; then
  psql "$CONN" -f "$1"
else
  psql "$CONN"
fi
