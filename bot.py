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

    async def setup_hook(self):
        await self.tree.sync()
        print("슬래시 명령어 동기화 완료!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"📢 [{bot.user}] 봇이 성공적으로 온라인 상태가 되었습니다!")

# 3. 50회 연속 멘션 명령어
@bot.tree.command(name="맨션", description="선택한 유저를 지정한 횟수만큼 멘션합니다. (최대 50회)")
@app_commands.describe(유저="멘션할 서버 멤버를 선택하세요.", 횟수="멘션할 횟수를 입력하세요 (1 ~ 50)")
async def mention(interaction: discord.Interaction, 유저: discord.Member, 횟수: int):
    # 안전장치 설정 (최대 50회)
    if 횟수 > 50:
        await interaction.response.send_message("❌ 횟수는 최대 50회까지만 입력할 수 있습니다.", ephemeral=True)
        return
    elif 횟수 <= 0:
        await interaction.response.send_message("❌ 횟수는 1회 이상이어야 합니다.", ephemeral=True)
        return

    try:
        # 첫 번째 멘션 발송 (디스코드 명령어 상호작용 응답)
        await interaction.response.send_message(f"{유저.mention} (1/{횟수})")
        
        # 나머지 횟수만큼 반복 발송 (0.9초 간격으로 디스코드 서버 차단 방지)
        for i in range(2, 횟수 + 1):
            await asyncio.sleep(0.9)
            await interaction.channel.send(f"{유저.mention} ({i}/{횟수})")
            
    except Exception as e:
        print(f"명령어 실행 오류: {e}")

# 웹 서버 가동 후 봇 실행 (Render 환경변수에서 토큰을 안전하게 읽어옵니다)
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("에러: DISCORD_TOKEN 환경 변수를 찾을 수 없습니다.")
