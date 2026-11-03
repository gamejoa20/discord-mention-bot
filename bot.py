import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread

# 1. Render 무료 서버 유지용 코드
app = Flask('')

@app.route('/')
def home():
    return "Bot is running at MAX speed!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.is_mentioning = False 

    async def setup_hook(self):
        await self.tree.sync()
        print("슬래시 명령어 동기화 완료!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"📢 [{bot.user}] 봇이 성공적으로 온라인 상태가 되었습니다!")

def make_heavy_mention(users, count):
    mention_line = ""
    for u in users:
        if u is not None:
            # 한 번에 5번 겹쳐 써서 전송 효율을 극대화
            mention_line += f"{u.mention} {u.mention} {u.mention} {u.mention} {u.mention} "
    return f"# ⚡ {mention_line}\n({count}회째 고속 호출)"

# [기능 1] 채널 초고속 무한 맨션
@bot.tree.command(name="맨션", description="선택한 유저들을 허용된 최대 속도로 무한 호출합니다.")
@app_commands.describe(
    유저1="첫 번째 유저를 선택하세요 (필수)",
    유저2="두 번째 유저를 선택하세요 (선택)"
)
async def mention(interaction: discord.Interaction, 유저1: discord.Member, 유저2: discord.Member = None):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    user_list = [u for u in [유저1, 유저2] if u is not None]

    try:
        bot.is_mentioning = True
        await interaction.response.send_message("🚀 초고속 무한 호출을 시작합니다! (멈추려면 `/중지`)", ephemeral=True)
        
        count = 1
        while bot.is_mentioning:
            heavy_text = make_heavy_mention(user_list, count)
            
            # 메시지 전송 명령
            await interaction.channel.send(heavy_text)
            count += 1
            
            # 디스코드 차단을 피하는 최소한의 한계 속도 (0.45초)
            await asyncio.sleep(0.45)
            if not bot.is_mentioning:
                break
            
        bot.is_mentioning = False
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# [기능 2] 개인 메시지(DM) 고속 무한 멘션
@bot.tree.command(name="갠디맨션", description="선택한 유저들의 DM으로 고속 무한 메시지를 보냅니다.")
@app_commands.describe(유저1="첫 번째 유저를 선택하세요 (필수)")
async def dm_mention(interaction: discord.Interaction, 유저1: discord.Member):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    await interaction.response.send_message("📬 DM 고속 전송을 시작합니다! (멈추려면 `/중지`)", ephemeral=True)

    try:
        bot.is_mentioning = True
        count = 1
        
        while bot.is_mentioning:
            try:
                dm_text = f"{유저1.mention} " * 5
                await 유저1.send(f"⚡ {dm_text}\n확인하세요! ({count}회째)")
            except discord.Forbidden:
                print(f"오류: DM을 보낼 수 없습니다.")
                break
            
            # DM은 제한이 더 엄격하므로 안전 마지노선 0.6초 설정
            await asyncio.sleep(0.6)
            count += 1
            if not bot.is_mentioning:
                break
            
        bot.is_mentioning = False
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# [기능 3] 무한 멘션 중지 명령어
@bot.tree.command(name="중지", description="현재 진행 중인 모든 고속 멘션을 즉시 중단합니다.")
async def stop_mention(interaction: discord.Interaction):
    if not bot.is_mentioning:
        await interaction.response.send_message("❌ 현재 실행 중인 멘션 명령어가 없습니다.", ephemeral=True)
        return

    bot.is_mentioning = False
    await interaction.response.send_message("🛑 모든 멘션 호출을 강제로 중지했습니다!")

# 웹 서버 가동 후 봇 실행
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("에러: DISCORD_TOKEN 환경 변수를 찾을 수 없습니다.")
