import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread

# 1. Render 무료 서버가 꺼지지 않게 웹페이지 주소를 열어두는 코드
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. 디스코드 봇 메인 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.is_mentioning = False  # 멘션 작동 여부를 제어하는 변수

    async def setup_hook(self):
        await self.tree.sync()
        print("슬래시 명령어 동기화 완료!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"📢 [{bot.user}] 봇이 성공적으로 온라인 상태가 되었습니다!")

# 헬퍼 함수: 유저 목록을 받아 멘션 문자열로 결합 (예: "@유저1 @유저2")
def make_mention_str(users):
    return " ".join([u.mention for u in users if u is not None])

# [기능 1] 채널 무한 맨션 (최대 5명 다중 선택 가능, /중지 전까지 무한 반복)
@bot.tree.command(name="맨션", description="선택한 유저들을 /중지 명령어를 치기 전까지 무한 멘션합니다.")
@app_commands.describe(
    유저1="첫 번째 유저를 선택하세요 (필수)",
    유저2="두 번째 유저를 선택하세요 (선택)",
    유저3="세 번째 유저를 선택하세요 (선택)",
    유저4="네 번째 유저를 선택하세요 (선택)",
    유저5="다섯 번째 유저를 선택하세요 (선택)"
)
async def mention(
    interaction: discord.Interaction, 
    유저1: discord.Member, 
    유저2: discord.Member = None, 
    유저3: discord.Member = None, 
    유저4: discord.Member = None, 
    유저5: discord.Member = None
):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    user_list = [u for u in [유저1, 유저2, 유저3, 유저4, 유저5] if u is not None]
    mention_text = make_mention_str(user_list)

    try:
        bot.is_mentioning = True
        # 첫 번째 멘션 발송 및 안내
        await interaction.response.send_message(f"📢 {mention_text} 무한 호출을 시작합니다! (멈추려면 `/중지`)")
        
        count = 2
        # bot.is_mentioning이 True인 동안 숫자를 올리며 무한 반복
        while bot.is_mentioning:
            await asyncio.sleep(0.9)
            if not bot.is_mentioning:
                break
            await interaction.channel.send(f"{mention_text} ({count}회째)")
            count += 1
            
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# [기능 2] 개인 메시지(DM) 무한 멘션 (최대 5명 다중 선택 가능, /중지 전까지 무한 반복)
@bot.tree.command(name="갠디맨션", description="선택한 유저들의 DM으로 /중지 명령어를 치기 전까지 무한 메시지를 보냅니다.")
@app_commands.describe(
    유저1="첫 번째 유저를 선택하세요 (필수)",
    유저2="두 번째 유저를 선택하세요 (선택)",
    유저3="세 번째 유저를 선택하세요 (선택)",
    유저4="네 번째 유저를 선택하세요 (선택)",
    유저5="다섯 번째 유저를 선택하세요 (선택)"
)
async def dm_mention(
    interaction: discord.Interaction, 
    유저1: discord.Member, 
    유저2: discord.Member = None, 
    유저3: discord.Member = None, 
    유저4: discord.Member = None, 
    유저5: discord.Member = None
):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    user_list = [u for u in [유저1, 유저2, 유저3, 유저4, 유저5] if u is not None]
    
    await interaction.response.send_message("📬 선택한 유저들의 DM으로 무한 메시지 전송을 시작합니다! (멈추려면 `/중지`)")

    try:
        bot.is_mentioning = True
        count = 1
        
        while bot.is_mentioning:
            for target_user in user_list:
                if not bot.is_mentioning:
                    break
                try:
                    await target_user.send(f"{target_user.mention} 님, 호출되었습니다! 📢 ({count}회째)")
                except discord.Forbidden:
                    print(f"오류: {target_user.name} 님이 DM을 차단했습니다.")
            
            # 여러 명에게 보낼 때 안전을 위해 딜레이를 1.2초로 설정
            await asyncio.sleep(1.2)
            count += 1
            
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# [기능 3] 무한 멘션 중지 명령어
@bot.tree.command(name="중지", description="현재 진행 중인 모든 무한 멘션(채널/DM)을 즉시 중단합니다.")
async def stop_mention(interaction: discord.Interaction):
    if not bot.is_mentioning:
        await interaction.response.send_message("❌ 현재 실행 중인 멘션 명령어가 없습니다.", ephemeral=True)
        return

    # 변수를 False로 바꾸어 while 루프를 즉시 종료시킴
    bot.is_mentioning = False
    await interaction.response.send_message("🛑 모든 멘션 호출을 강제로 중지했습니다!")

# 웹 서버 가동 후 봇 실행
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("에러: DISCORD_TOKEN 환경 변수를 찾을 수 없습니다.")

