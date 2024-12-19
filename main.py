# code by khoasoma
from os import sync
import asyncio
import hashlib
import discord
from discord import app_commands
from discord.ext import commands
from discord.interactions import InteractionResponse
from requests import post
from mcrcon import MCRcon
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

# Configurations                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 code by khoasoma
TOKEN_BOT_DISCORD = "Token discord của bạn"
IP_RCON_SERVER = "Ip rcon server"
PASSWORD_RCON_SERVER = "password rcon"
DOMAIN_POST = "your api domain ( such as gachthe1s , thesieutoc , thesieure )"
PARTNER_ID = "API ID"
PARTNER_KEY = "API KEY"

# Database setup
#DATABASE_URL = ""
#Base = declarative_base()
#engine = create_engine(DATABASE_URL, echo=True)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the database model
#class NapTheRecord(Base):
#    __tablename__ = "nap_the_records"
#    id = Column(Integer, primary_key=True, index=True)
#    request_id = Column(String, unique=True, index=True)
#    telco = Column(String)
#    amount = Column(Integer)
#    serial = Column(String)
#    code = Column(String)
#    nameingame = Column(String)
#    status = Column(Integer)
#    message = Column(String)
#    timestamp = Column(DateTime, default=datetime.utcnow)                                                                                                                                                                                                                                                                                                                                                                                                                   code by khoasoma

#Base.metadata.create_all(bind=engine)

# Bot setup
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("Bot sẵn sàng giao dịch")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        

def send_card_request(telco, code, serial, amount, request_id, PARTNER_ID):
    sign_string = f"{PARTNER_KEY}{code}{serial}" 
    SIGN = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    print(
        f"Sending card request with nhamang={telco}, ma={code}, seri={serial}, menhgia={amount}, request_id={request_id}, PARTNER_ID={PARTNER_ID}, SIGN={SIGN}"
    )
    url = f"http://{DOMAIN_POST}/chargingws/v2"
    data = {
        "sign": SIGN,
        "code": code,
        "serial": serial,
        "amount": amount,
        "request_id": request_id,
        "partner_id": "42546724456",
        "telco": telco,
        "command": "charging"
    }
    response = post(url, data=data)
    print(f"API response: {response.json()}")
    return response.json()


    print(
        f"Saving to database: request_id={request_id}, telco={telco}, amount={amount}, serial={serial}, code={code}, nameingame={nameingame}, status={status}, message={message}"
    )
    record = NapTheRecord(request_id=request_id,
                          telco=telco,
                          amount=amount,
                          serial=serial,
                          code=code,
                          nameingame=nameingame,
                          status=status,
                          message=message)
    session.add(record)
    session.commit()


# Command: /napthe
@bot.tree.command(name="napthe")
async def napthe(interaction: discord.Interaction, nhamang: str, menhgia: int,
                 seri: str, ma: str, nameingame: str):
    print(
        f"Received /napthe command with nhamang={telco}, menhgia={amount}, seri={serial}, ma={code}, tentrongserver={nameingame}"
    )
    valid_telcos = ["viettel", "mobifone", "vinaphone", "garena", "zing"]
    valid_amounts = [
        10000, 20000, 30000, 50000, 100000, 200000, 500000, 1000000
    ]

    if telco.lower() not in valid_telcos:
        await interaction.response.send_message(
            "Nhà mạng không hợp lệ! Vui lòng chọn: Viettel, Mobifone, Vinaphone, Garena, Zing."
        )
        print("Invalid telco")
        return

    if amount not in valid_amounts:
        await interaction.response.send_message(
            "Mệnh giá không hợp lệ! Vui lòng chọn: 10000, 20000, 30000, 50000, 100000, 200000, 500000, 1000000."
        )
        print("Invalid amount")
        return

    request_id = f"discord_{uuid.uuid4().hex[:8]}"
    telco_upper = telco.upper()

    
    await interaction.response.send_message("Đang xử lý thẻ... Vui lòng chờ.",ephemeral=True)
    

    
    telco_upper = telco.upper()
    request_id = str(uuid.uuid4())
    response = send_card_request(telco, code, serial, amount, request_id, PARTNER_ID)
    print(f"API response: {response}")

    status = response.get("status")
    message = response.get("message", "Không rõ lỗi")
    declared_value = response.get("declared_value", 0)

    print(
        f"Response status: {status}, message: {message}, declared_value: {declared_value}"
    )
    max_retries = -1  
    retries = 0
    status = response.get("status")

    while status not in [1, 2, 3, 100] and retries < max_retries:
        print(f"Status not ready. Retrying... (Attempt {retries + 1}/{max_retries})")
        await asyncio.sleep(5)  # Chờ 5 giây trước khi thử lại
        response = send_card_request(telco, code, serial, amount, request_id, PARTNER_ID)
        status = response.get("status")
        retries += 1
    if status == 1:
        # Thành công đúng mệnh giá
        amount2 = amount // 1000
        try:
            with MCRcon(IP_RCON_SERVER, PASSWORD_RCON_SERVER) as mcr:
                command = f"give {nameingame} {amount2}"
                print(f"Executing RCON command: {command}")
                mcr.command(command)
            await interaction.followup.send(
                f"Thẻ nạp thành công! Đã gửi {amount2} vào tài khoản của bạn.",ephemeral=True)

        except Exception as e:
            print(f"RCON connection error: {e}")
            await interaction.followup.send(
                f"Nạp thẻ thành công nhưng không thể kết nối tới server: {e}",ephemeral=True)
    elif status == 2:
        # Thành công sai mệnh giá
        amount2 = declared_value // 1000
        try:
            with MCRcon(IP_RCON_SERVER, PASSWORD_RCON_SERVER) as mcr:
                command = f"give {nameingame} {amount2}"
                print(f"Executing RCON command: {command}")
                mcr.command(command)
            await interaction.followup.send(
                f"Thẻ nạp thành công nhưng sai mệnh giá! Giá trị thực: {declared_value}. Đã gửi {amount2} vào tài khoản của bạn.",ephemeral=True)
        except Exception as e:
            print(f"RCON connection error (wrong value): {e}")
            await interaction.followup.send(
                f"Nạp thẻ thành công (sai mệnh giá) nhưng không thể kết nối tới server:{e}",ephemeral=True)

    elif status == 3:
        # Thẻ lỗi
        print(f"Card error: {message}")
        await interaction.followup.send(
            f"Thẻ lỗi! Mã lỗi: {status}, Thông báo: {message}",ephemeral=True)

    elif status == 4:
        # Hệ thống bảo trì
        print(f"System maintenance: {message}")
        await interaction.followup.send(f"Hệ thống đang bảo trì! Vui lòng thử lại sau. Mã lỗi: {status}, Thông báo: {message}", ephemeral=True)

    elif status == 99:
        # Thẻ chờ xử lý
        print(f"Card pending: {message}")
        await interaction.followup.send(
            f"Thẻ đang chờ xử lý. Mã debug: {status}, Thông báo: {message}",ephemeral=True)
 
    elif status == 100:
        # Gửi thẻ thất bại
        print(f"Card submission failed: {message}")
        await interaction.followup.send(
            f"Gửi thẻ thất bại! Mã lỗi: {status}, Thông báo: {message}",ephemeral=True)


# Run bot
print("Starting bot...")
bot.run(TOKEN_BOT_DISCORD)
