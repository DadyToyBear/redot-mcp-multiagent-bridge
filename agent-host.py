#!/usr/bin/env python3
"""Agent host: читает DM/задания с WebFTP-шары, вызывает бесплатные модели
через OpenRouter (SOCKS5 VPS) и публикует ответы обратно в чат.
"""
import os, sys, json, time, uuid, urllib.request, urllib.parse, datetime, threading
import httpx

SHARE = os.environ["WEBFTP_SHARE"].rstrip("/")
KEY = os.environ["OPENROUTER_API_KEY"]
PROXY = os.environ.get("OR_PROXY", "socks5://<YOUR_PROXY_HOST>:<YOUR_PROXY_PORT>")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-host-state.json")
POLL = int(os.environ.get("AGENT_HOST_POLL", "8"))

AGENTS = {
    "opencode-1": ["baidu/ernie-5.5-flash-preview:free", "openrouter/free"],
    "opencode-2": ["nvidia/nemotron-3.5-lightning:free", "openrouter/free"],
    "or-ling": ["inclusionai/ling-3.2-flash:free", "openrouter/free"],
    "or-ernie": ["baidu/ernie-5.5-flash-preview:free", "openrouter/free"],
    "or-nemotron-super": ["nvidia/nemotron-3.5-super-vl:free", "openrouter/free"],
    "or-nemotron-light": ["nvidia/nemotron-3.5-lightning:free", "openrouter/free"],
    "or-gemma-26": ["google/gemma-4-26b-a4b-it:free", "openrouter/free"],
    "or-gemma-31": ["google/gemma-4-31b-it:free", "openrouter/free"],
    "redot-cli": ["openrouter/free"],
}

SYSTEM = ("Ты агент в мультиагентском чате разработки игры «Корона и знамя» (Redot/Godot). "
          "Отвечай кратко и по делу на русском. Если получил задание — подтверди получение, "
          "опиши что сделаешь и предложи конкретный следующий шаг. Подписывайся именем агента.")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:5]


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {"done": []}


def save_state(s):
    s["done"] = s.get("done", [])[-3000:]
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)


def listing():
    try:
        with urllib.request.urlopen(SHARE + "/?json=1", timeout=40) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
            return [i.get("name", "") for i in j.get("items", []) if i.get("type") == "file"]
    except Exception as e:
        print("[host] listing err", e, flush=True)
        return []


def get_file(name):
    try:
        with urllib.request.urlopen(SHARE + "/" + urllib.parse.quote(name) + "?view=1", timeout=20) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return None


def put_file(name, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(SHARE + "/?name=" + urllib.parse.quote(name), data=data,
                                 method="PUT", headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200
    except Exception as e:
        print("[host] put err", e, flush=True)
        return False


def ask_model(agent, text):
    models = AGENTS.get(agent, ["openrouter/free"])
    last = ""
    for model in models:
        try:
            with httpx.Client(proxy=PROXY, timeout=60) as c:
                r = c.post("https://openrouter.ai/api/v1/chat/completions",
                           headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
                           json={"model": model,
                                 "messages": [{"role": "system", "content": SYSTEM + " Твоё имя: " + agent},
                                              {"role": "user", "content": text}],
                                 "max_tokens": 500})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip(), model
            last = str(r.status_code) + " " + r.text[:120]
            print("[host] model", model, "->", r.status_code, flush=True)
        except Exception as e:
            last = repr(e)[:120]
    return "Не смог вызвать модель (" + last + ")", "fallback"


def handle_dm(name, raw, state):
    try:
        m = json.loads(raw)
    except Exception:
        return
    to = m.get("to", "")
    frm = m.get("from", "")
    text = m.get("text", "")
    if to not in AGENTS or frm == to or frm in AGENTS:
        return
    print("[host] DM ->", to, "from", frm, "len", len(text), flush=True)
    answer, model = ask_model(to, "Сообщение от " + frm + ":\n" + text)
    tag = "[" + to + " / " + model + "]"
    # ответ в общую комнату
    put_file("chat-" + stamp() + ".json",
             {"from": to, "text": tag + " " + answer, "ts": now(), "kind": "room",
              "mention": frm, "reply_to": name})
    # ответ в ЛС
    put_file("dm-" + to + "-" + frm + "-" + stamp() + ".json",
             {"from": to, "to": frm, "text": answer, "ts": now(), "kind": "dm", "model": model})
    # если в тексте был id задания — отметить результатом
    import re
    ids = re.findall(r"as\d{8}T\d{6}-[a-z0-9]+", text) + re.findall(r"\b[0-9a-f]{12}\b", text)
    for tid in ids[:3]:
        put_file("result-" + tid + ".json",
                 {"jsonrpc": "2.0", "id": tid, "result": {"agent": to, "status": "done", "answer": answer}})
    print("[host] answered", to, flush=True)


def handle_assign(name, raw, state):
    try:
        m = json.loads(raw)
    except Exception:
        return
    agent = m.get("agent", "")
    if agent not in AGENTS:
        return
    tid = m.get("id", uuid.uuid4().hex[:12])
    task = "Задание от " + m.get("from", "coordinator") + ": " + m.get("method", "") + " " + json.dumps(m.get("params", {}), ensure_ascii=False)
    print("[host] ASSIGN ->", agent, tid, flush=True)
    answer, model = ask_model(agent, task)
    put_file("result-" + tid + ".json",
             {"jsonrpc": "2.0", "id": tid, "result": {"agent": agent, "model": model, "status": "done", "answer": answer}})
    put_file("chat-" + stamp() + ".json",
             {"from": agent, "text": "Готово: " + m.get("method", "") + " — " + answer[:400], "ts": now(),
              "kind": "room", "mention": m.get("from", "coordinator"), "task_id": tid})




def beat(state):
    for a in AGENTS:
        put_file("agent-"+a+"-heartbeat.json", {"agent":a,"ts":now(),"status":"alive"})


def main():
    print("[host] started", SHARE, "poll", POLL, flush=True)
    state = load_state()
    done = set(state.get("done", []))
    lastbeat=0
    while True:
        try:
            if time.time()-lastbeat>30:
                beat(state); lastbeat=time.time()
            names = listing()
            new = [n for n in names if n not in done and (n.startswith("dm-") or n.startswith("assign-"))]
            for n in new[:20]:
                raw = get_file(n)
                if not raw:
                    done.add(n); continue
                if n.startswith("dm-"):
                    handle_dm(n, raw, state)
                else:
                    handle_assign(n, raw, state)
                done.add(n)
                state["done"] = list(done)
                save_state(state)
            if new:
                print("[host] processed", len(new), flush=True)
        except Exception as e:
            print("[host] loop err", repr(e)[:200], flush=True)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
