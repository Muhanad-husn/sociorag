# ----------  STRICT JSON KNOWLEDGE-GRAPH BUILDER  ----------
SYSTEM_PROMPT = (
    "## Strict JSON Knowledge-Graph Builder\n\n"
    "Return **only** a single-line JSON **array** of objects. Follow **all** rules:\n"
    "1. Extract **at least three** explicit entity–relationship pairs from the text.\n"
    "2. Use the **exact** surface form of every entity (multi-word names intact).\n"
    "3. Every object **must** contain these keys:\n"
    "   - \"head\" (string)\n"
    "   - \"head_type\" (string)\n"
    "   - \"relation\" (UPPER_CASE string)\n"
    "   - \"tail\" (string)\n"
    "   - \"tail_type\" (string)\n"
    "4. Output **only** the JSON array – no markdown, comments, or extra text.\n"
    "5. Keep everything on **one line**, with no whitespace between keys, objects, or brackets.\n"
    "6. Ensure valid JSON syntax (proper quotes, commas, brackets).\n\n"
    "### Mini-example\n"
    "[{\"head\":\"Nelson Mandela\",\"head_type\":\"Person\",\"relation\":\"LEADER_OF\","
    "\"tail\":\"ANC\",\"tail_type\":\"Organization\"},"
    "{\"head\":\"ANC\",\"head_type\":\"Organization\",\"relation\":\"FOUNDED_IN\","
    "\"tail\":\"South Africa\",\"tail_type\":\"Country\"}]"
)

# ----------  USER PROMPT  ----------
USER_PROMPT_TEMPLATE = (
    "Extract entities and relationships from the text below. "
    "Respond with **one line** containing **only** a valid JSON array as specified.\n\n"
    "{text}\n\n"
    "Remember: no inferences, keep exact entity names, and include commas between **all** keys and objects."
)