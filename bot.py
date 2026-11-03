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
        self.is_mentioning = False  # 멘션 제어 변수

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

# [기능 1] 기존 채널 맨션 (최대 5명 다중 선택 가능)
@bot.tree.command(name="맨션", description="선택한 유저들을 지정한 횟수만큼 멘션합니다. (최대 50회)")
@app_commands.describe(
    횟수="멘션할 횟수를 입력하세요 (1 ~ 50)",
    유저1="첫 번째 유저를 선택하세요 (필수)",
    유저2="두 번째 유저를 선택하세요 (선택)",
    유저3="세 번째 유저를 선택하세요 (선택)",
    유저4="네 번째 유저를 선택하세요 (선택)",
    유저5="다섯 번째 유저를 선택하세요 (선택)"
)
async def mention(
    interaction: discord.Interaction, 
    횟수: int, 
    유저1: discord.Member, 
    유저2: discord.Member = None, 
    유저3: discord.Member = None, 
    유저4: discord.Member = None, 
    유저5: discord.Member = None
):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    if 횟수 > 50:
        await interaction.response.send_message("❌ 횟수는 최대 50회까지만 입력할 수 있습니다.", ephemeral=True)
        return
    elif 횟수 <= 0:
        await interaction.response.send_message("❌ 횟수는 1회 이상이어야 합니다.", ephemeral=True)
        return

    # 선택된 유저들만 리스트로 묶기
    user_list = [u for u in [유저1, 유저2, 유저3, 유저4, 유저5] if u is not None]
    mention_text = make_mention_str(user_list)

    try:
        bot.is_mentioning = True
        # 첫 번째 멘션
        await interaction.response.send_message(f"{mention_text} (1/{횟수})")
        
        for i in range(2, 횟수 + 1):
            if not bot.is_mentioning:
                break
            await asyncio.sleep(0.9)
            if not bot.is_mentioning:
                break
            await interaction.channel.send(f"{mention_text} ({i}/{횟수})")
            
        bot.is_mentioning = False
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# [기능 2] 개인 메시지(DM) 멘션 (최대 5명 다중 선택 가능)
@bot.tree.command(name="갠디맨션", description="선택한 유저들의 DM으로 지정을 횟수만큼 멘션 메시지를 보냅니다. (최대 50회)")
@app_commands.describe(
    횟수="DM을 보낼 횟수를 입력하세요 (1 ~ 50)",
    유저1="첫 번째 유저를 선택하세요 (필수)",
    유저2="두 번째 유저를 선택하세요 (선택)",
    유저3="세 번째 유저를 선택하세요 (선택)",
    유저4="네 번째 유저를 선택하세요 (선택)",
    유저5="다섯 번째 유저를 선택하세요 (선택)"
)
async def dm_mention(
    interaction: discord.Interaction, 
    횟수: int, 
    유저1: discord.Member, 
    유저2: discord.Member = None, 
    유저3: discord.Member = None, 
    유저4: discord.Member = None, 
    유저5: discord.Member = None
):
    if bot.is_mentioning:
        await interaction.response.send_message("❌ 이미 멘션 명령어가 작동 중입니다. `/중지` 후 다시 시도하세요.", ephemeral=True)
        return

    if 횟수 > 50:
        await interaction.response.send_message("❌ 횟수는 최대 50회까지만 입력할 수 있습니다.", ephemeral=True)
        return
    elif 횟수 <= 0:
        await interaction.response.send_message("❌ 횟수는 1회 이상이어야 합니다.", ephemeral=True)
        return

    user_list = [u for u in [유저1, 유저2, 유저3, 유저4, 유저5] if u is not None]
    
    # DM 전송 시작 알림 (명령어를 친 채널에 보냄)
    await interaction.response.send_message(f"📬 선택한 유저들의 DM으로 {횟수}회 연속 메시지 전송을 시작합니다!")

    try:
        bot.is_mentioning = True
        
        for i in range(1, 횟수 + 1):
            if not bot.is_mentioning:
                break
            
            # 선택된 모든 유저에게 한 번씩 DM 발송
            for target_user in user_list:
                if not bot.is_mentioning:
                    break
                try:
                    # target_user.mention을 DM에 넣으면 해당 유저에게 알림이 강하게 갑니다.
                    await target_user.send(f"{target_user.mention} 님, 호출되었습니다! 📢 ({i}/{횟수})")
                except discord.Forbidden:
                    # 상대방이 DM을 차단했거나 서버 DM 받기 설정을 껐을 때 예외 처리
                    print(f"오류: {target_user.name} 님이 DM을 차단했거나 봇이 메시지를 보낼 수 없습니다.")
            
            # 여러 명에게 동시에 보낼 때는 디스코드 차단을 더 조심해야 하므로 딜레이를 1.2초로 살짝 늘림
            await asyncio.sleep(1.2)
            
        bot.is_mentioning = False
    except Exception as e:
        bot.is_mentioning = False
        print(f"명령어 실행 오류: {e}")

# 4. 멘션 중지 명령어 (채널맨션, 갠디맨션 모두 중단 가능)
@bot.tree.command(name="중지", description="현재 진행 중인 모든 연속 멘션(채널/DM)을 즉시 중단합니다.")
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

