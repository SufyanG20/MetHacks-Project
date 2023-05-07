import discord
import random
import os
import asyncio
from random import choice
from discord.ext import tasks, commands
import requests
from datetime import datetime, timedelta
import concurrent.futures
from dotenv import load_dotenv

sem = asyncio.Semaphore(5)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
people = {}
intents = discord.Intents.all()
client = commands.Bot(command_prefix="?", intents=intents)
medication_dict = {}
quotes = ["Keep smiling, because life is a beautiful thing and there's so much to smile about", "Life is a long lesson in humility."]
status = ["Discord bro, what did you expect?"]

@client.event
async def on_ready():
  apply_status.start()
  print('Logged in as {0.user}'.format(client))

@tasks.loop(seconds=600)
async def apply_status():
  await client.change_presence(activity=discord.Game(choice(status)))

@client.command(name="hello", help="Greets user")
async def hello(ctx):
  username=str(ctx.author).split('#')[0]
  await ctx.send(f'Hello {username}!')

@client.command(name="medication", help="medication name")
async def medication(ctx):
  user_id = str(ctx.author.id)
  individual=str(ctx.author).split('#')[0]
  medication = ctx.message.content.split(" ")[1] 
  keyList = []
  if user_id in medication_dict:
        addTuple = (medication, None)
        medication_dict[user_id].append(addTuple)
  else:
        addTuple = (medication, None)
        keyList.append(addTuple)
        medication_dict[user_id] = keyList
  await ctx.send(f'{medication} added for {individual}!')

@client.command(name="listmeds", help="list all medications")
async def listmeds(ctx):
  user_id = str(ctx.author.id)
  individual=str(ctx.author).split('#')[0] 
  strMed = ""
  if medication_dict.get(user_id):    
    for x,y in medication_dict.get(user_id):
        strMed += "medication: " + str(x) + ", interval: " + str(y) + " minute(s)\n"
  await ctx.send(f'{individual} medications:\n{strMed.strip()}')

@client.command(name="interval", help="interval duration for medication")
async def interval(ctx, medName, duration):
    user_id = str(ctx.author.id)
    medication_info = medication_dict.get(user_id) 
    if medication_info:
        for x,y in medication_dict[user_id]:
            if x == medName:    
                  medication_dict[user_id].remove((x,y))
                  medication_dict[user_id].append((x, int(duration)))
        await ctx.send(f'The daily interval for {medName} is {duration} minute(s)!')
        startTime = datetime.now()
        await run_medication(ctx.author, int(duration), medName)
    else:
        await ctx.send('Please set a medication name first using the ?medication command.')

@client.command(name="removeping", help="Removes your medication from the list of users to be pinged.")
async def remove_ping(ctx, medication):
    user_id = str(ctx.author.id)
    medication = ctx.message.content.split(" ")[1]
    medication_info = medication_dict.get(user_id)
    if user_id in medication_info:
       for x, y in medication_info:
         if medication_info == x:
            medication_info.remove((x,y))
         await ctx.send("Your medication have been removed from the ping list.")
    else:
        await ctx.send("Your medications is currently not on the ping list or the user does not exist.")

@client.command(name ="network", help="add user to close network")
async def network(ctx, member: discord.Member):
    user_id = str(ctx.author.id)
    closeFriend = str(member.id)
    closeFriendName = member.display_name

    if member is None:
       await ctx.send("Please provide a valid member.")
       return

    if user_id not in people:
        people[user_id] = []

    if closeFriend in people[user_id]:
      await ctx.send(f"{closeFriendName} is already added to your close friend/family list.")
    else:
      people[user_id].append(closeFriendName)
      await ctx.send(f"{closeFriendName} has been added to your close friend/family list.")


@client.command(name = "listnet", help = "lists all your available networks")
async def printNetwork(ctx):
  user_id = str(ctx.author.id) 
  individual=str(ctx.author).split('#')[0] 
  rank = 1
  closeIndividuals= ""
  if user_id in people:
     for x in people[user_id]:
        closeIndividuals += "Network #" + str(rank) + " " + x + "\n"
        rank = rank + 1
  await ctx.send(f'{individual} Networks:\n{closeIndividuals.strip()}')

async def run_medication(user, duration, medName):
  @tasks.loop(minutes=duration)
  async def check_medicationReminder(user, medName):
    if check_medicationReminder.current_loop != 0:
      user_id = str(user.id)
      message = await user.send(f"Hey, it's time to take your medication, {medName}! ")
      
      await message.add_reaction('✅')
      def check(reaction, reacting):
        return reacting == user and str(reaction.emoji) == '✅'
      try:
        reacting = user
        reaction, reacting = await client.wait_for('reaction_add', timeout=60, check=check)
      except asyncio.TimeoutError:
        await reacting.send("Sorry, I need an update on your medication status")
        user_display_name = user.display_name
        for x in people[user_id]:
          message = f"Hey, your network {user_display_name} has not taken their medication for the past 2 minutes!"
          member = discord.utils.get(user.guild.members, name=x)
          if member:
            await member.send(message)
      else:
        await reacting.send("Great job on completing your task!")

  await check_medicationReminder.start(user, medName)
  
@client.command(name="bye", help="Farewell message")
async def bye(ctx):
  username=str(ctx.author).split('#')[0]
  await ctx.send(f'Bye {username}!')

client.run(TOKEN)
