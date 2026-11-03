import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread
import logging

# 디스코드 및 웹서버 로그 간소화
logging.basicConfig(level=logging.INFO)

# 1. Render 무료 서버 유지용 코드 (UptimeRobot 연동 필수)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running at optimized speed!"

def run():
    # Render는 PORT 환경변수를 자동으로 주입합니다.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True) # 데몬 스레드로 설정하여 메인 프로세스 종료 시 함께 종료
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
        print("📢 슬래시 명령어 동기화 완료!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"📢 [{bot.user}] 봇이 성공적으로 온라인 상태가 되었습니다!")

# 헬퍼 함수: 일반 글자 크기로 깔끔하게 멘션 텍스트 생성
def make_single_mention(users, count):
    mention_line = " ".join([u.mention for u in users if u is not None])
    return f"{mention_line} ({count}회째)"

# [기능 1] 채널 최적화 고속 무한 맨션 (최대 5명)
@bot.tree.command(name="맨션", description="선택한 유저들을 일반 글자 크기로 허용된 최대 속도로 무한 호출합니다. (최대 5명)")
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

    try:
        bot.is_mentioning = True
        await interaction.response.send_message("🚀 무한 호출을 시작합니다! (멈추려면 `/중지`)", ephemeral=True)
        
        count = 1
        while bot.is_mentioning:
            single_text = make_single_mention(user_list, count)
            await interaction.channel.send(single_text)
            count += 1
            
            # --- 디스코드 정지 방지 안전 브레이크 ---
            if count % 10 == 0:
                await asyncio.sleep(2.5) # 안전 확보를 위해 대기시간 소폭 상향
            else:
                await asyncio.sleep(0.5)
                
            if not bot.is_mentioning:
                break
            
    except Exception as e:
        print(f"명령어 실행 오류: {e}")
    finally:
        bot.is_mentioning = False

# [기능 2] 개인 메시지(DM) 고속 무한 멘션 (최대 5명)
@bot.tree.command(name="갠디맨션", description="선택한 유저들의 DM으로 일반 글자 크기의 무한 메시지를 보냅니다. (최대 5명)")
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
    await interaction.response.send_message("📬 DM 무한 전송을 시작합니다! (멈추려면 `/중지`)", ephemeral=True)

    try:
        bot.is_mentioning = True
        count = 1
        
        while bot.is_mentioning:
            for target_user in user_list:
                if not bot.is_mentioning:
                    break
                try:
                    await target_user.send(f"{target_user.mention} 호출되었습니다! ({count}회째)")
                except discord.Forbidden:
                    print(f"오류: {target_user.name} 님이 DM을 차단했습니다.")
                await asyncio.sleep(0.2) # 유저 간 전송 텀 두어 디스코드 제재 방지
            
            count += 1
            
            # 다중 DM 발송 시 차단 안전 브레이크
            if count % 5 == 0:
                await asyncio.sleep(3.0)
            else:
                await asyncio.sleep(0.6)
            
    except Exception as e:
        print(f"명령어 실행 오류: {e}")
    finally:
        bot.is_mentioning = False

# [기능 3] 무한 멘션 중지 명령어
@bot.tree.command(name="중지", description="현재 진행 중인 모든 멘션을 즉시 중단합니다.")
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
