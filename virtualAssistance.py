import discord
import random
import os
import asyncio
import cohere
from random import choice
from discord.ext import tasks, commands
import requests
from datetime import datetime, timedelta
import concurrent.futures
from dotenv import load_dotenv
from cohere.responses.classify import Example

sem = asyncio.Semaphore(5)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN_COHERE = os.getenv('COHERE_TOKEN')
TOKEN_SERVER = os.getenv('SERVER_TOKEN')
co = cohere.Client(TOKEN_COHERE)

people = {}
intents = discord.Intents.all()
client = commands.Bot(command_prefix="?", intents=intents)
medication_dict = {}
quotes = ["Keep smiling, because life is a beautiful thing and there's so much to smile about", "Life is a long lesson in humility."]
status = ["Discord bro, what did you expect?"]
labels_set = set()
ex=[Example("\"I feel like I need drugs or alcohol to function normally. Even when I try to quit or cut back, I experience intense cravings and withdrawal symptoms.\"", "Substance Abuse"), Example("\"My substance use has caused problems in my relationships, work, and other areas of my life. I feel like I\'m constantly chasing a high and neglecting my responsibilities.\"", "Substance Abuse"), Example("\"I feel like I\'m trapped in a cycle of addiction and shame. I know that my substance use is hurting me and those around me, but I can\'t seem to stop.\"", "Substance Abuse"), Example("\"I have a hard time staying focused on anything for very long, and my mind is always racing with different thoughts and ideas.\"", "ADHD"), Example("\"I struggle to stay organized and manage my time effectively. I\'m always running late or forgetting things, even if I\'ve written them down.\"", "ADHD"), Example("\"I get really restless and fidgety if I\'m forced to sit still for too long. It\'s like I need to be moving and doing something all the time.\"", "ADHD"), Example("\"I feel like my heart is racing and I can\'t catch my breath, and I\'m constantly worried about everything, even the smallest things.\"", "Anxiety Disorder"), Example("\"I don\'t know why, but I always feel on edge and like something bad is about to happen. It\'s hard to shake this feeling of dread and it\'s affecting my ability to enjoy things I used to love.\"", "Anxiety Disorder"), Example("\"I can\'t seem to turn off the worrying thoughts that go through my head, even when I know they\'re irrational. It\'s exhausting and I feel like I\'m constantly on high alert.\"", "Anxiety Disorder"), Example("\"Some days, I feel like I\'m on top of the world and can accomplish anything, but other times, I feel so low and hopeless that I can\'t even get out of bed.\"", "Bipolar Disorder"), Example("\"I have these episodes where I feel like I can\'t control my thoughts or actions, and I end up doing things that are really impulsive and risky.\"", "Bipolar Disorder"), Example("\"It\'s like I\'m constantly on a rollercoaster, and I never know when I\'m going to hit a sudden dip or a sharp turn. It\'s exhausting trying to keep up with my moods and energy levels.\"", "Bipolar Disorder"), Example("\"I just feel so sad and hopeless all the time. It\'s like a dark cloud is following me around and I can\'t escape it.\"", "Depression"), Example("\"I don\'t have any energy or motivation to do anything. Even small tasks feel overwhelming and exhausting.\"", "Depression"), Example("\"I feel like I\'m just going through the motions of life without really experiencing any joy or happiness. It\'s like I\'m stuck in this numb, empty state and I don\'t know how to get out of it.\"", "Depression"), Example("\"I feel like I\'m constantly thinking about food and my weight. Even when I\'m not hungry, I can\'t stop thinking about what I\'ve eaten or what I\'m going to eat.\"", "Eating Disorder"), Example("\"I have a lot of anxiety around eating in public or with other people. I\'m scared that they\'ll judge me for what I\'m eating or how much I\'m eating.\"", "Eating Disorder"), Example("\"I have a distorted view of my body image and feel like I\'m never thin enough. I go to great lengths to lose weight, even if it means skipping meals or exercising excessively.\"", "Eating Disorder"), Example("\"I have intrusive thoughts that cause me a lot of anxiety and make me feel like I have to perform certain rituals or behaviors to prevent something bad from happening.\"", "OCD"), Example("\"I feel like I\'m stuck in a loop of obsessive thoughts and compulsive actions. Even though I know they\'re irrational, I can\'t seem to stop myself from doing them.\"", "OCD"), Example("\"I have a lot of anxiety around cleanliness and germs, and I feel like I have to constantly wash my hands or clean my environment to stay safe.\"", "OCD"), Example("\"I\'m feeling pretty good today. I slept well last night and I\'m looking forward to getting some work done.\"", "Positive Group"), Example("\"I\'m generally a pretty laid-back person. I don\'t get too worked up about things and I try to go with the flow.\"", "Positive Group"), Example("\"I\'m feeling pretty confident in myself and my abilities right now. I\'ve been working hard and seeing some good results, which feels great.\"", "Positive Group"), Example("\"I have nightmares and flashbacks about traumatic events that I\'ve experienced, and they can be triggered by even the slightest reminder or sound.\"", "PTSD"), Example("\"I feel like I\'m always on edge and hypervigilant, constantly scanning my environment for potential threats or danger.\"", "PTSD"), Example("\"I have trouble trusting people and forming close relationships because I\'m so scared of being hurt or betrayed again.\"", "PTSD"), Example("\"I hear voices in my head that no one else can hear, and they can be really loud and overwhelming. They often tell me to do things or make me feel like I\'m being watched.\"", "Schizophrenia"), Example("\"I have trouble distinguishing what\'s real and what\'s not. Sometimes I see things that aren\'t there or believe things that others tell me aren\'t true.\"", "Schizophrenia"), Example("\"I feel like I\'m disconnected from my own thoughts and emotions, like they\'re not really mine. It can be hard to know what\'s going on in my own mind.\"", "Schizophrenia")]
hlth=[Example("Can you recommend a therapist who specializes in anxiety disorders?", "Health"), Example("I\'m feeling really overwhelmed lately, do you have any coping strategies to suggest?", "Health"), Example("How do I know if I\'m experiencing symptoms of depression?", "Health"), Example("Can you help me find resources for support groups in my area?", "Health"), Example("What are some effective treatments for post-traumatic stress disorder?", "Health"), Example("Tips on reducing my stress", "Health"), Example("Can you recommend a good restaurant in the area?", "Not Health"), Example("What\'s the weather going to be like tomorrow?", "Not Health"), Example("Do you know where the nearest post office is located?", "Not Health"), Example("How do I change the oil in my car?", "Not Health"), Example("What is your favourite colour", "Not Health")]


@client.event
async def on_ready():
  apply_status.start()
  print('Logged in as {0.user}'.format(client))
  for example in ex:
      category = example.label.lower().strip().replace(" ", "-")
      labels_set.add(category)
  client.loop.create_task(send_quotes())

@client.event
async def on_guild_join(guild):    
  for i in labels_set:
    existing_channel = discord.utils.get(guild.channels, name=i)
    if not existing_channel:
      # Create the new private channels
      permissions = {
      guild.default_role: discord.PermissionOverwrite(read_messages=False),
      guild.me: discord.PermissionOverwrite(read_messages=True)
      }
      await guild.create_text_channel(i, overwrites=permissions)

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

@client.command(name="removeGroups", help="Remove therapy group text channels")
async def remove_groups(ctx):
    guild = ctx.guild
    for i in labels_set:
      existing_channel = discord.utils.get(guild.channels, name=i)
      if existing_channel:
        await existing_channel.delete()
        # await ctx.send(f"Channel '{channel_name}' has been deleted!")
      else:
        pass
        # await ctx.send(f"Channel '{channel_name}' does not exist.")

@client.command(name="createGroups", help="Make channel")
async def create_groups(ctx):
  guild = ctx.guild
  for i in labels_set:
    existing_channel = discord.utils.get(guild.channels, name=i)
    if not existing_channel:
      # Create the new channel
      permissions = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
      }
      await guild.create_text_channel(i, overwrites=permissions)
      # await ctx.send(f"Channel '{channel_name}' has been created!")
    else:
      pass
      # If the channel already exists, send a message saying so
      # await ctx.send(f"Channel '{channel_name}' already exists!")

def generate_quote(item):
  response = co.generate(
  model='command-xlarge-nightly',
  prompt='Give me one positive quote for someone suffering from ' + str(item),
  max_tokens=300,
  temperature=0.9,
  k=0,
  stop_sequences=[],
  return_likelihoods='NONE')
  x = response.generations[0].text

  return x

# Define a function that sends the quote to the specified channel
async def send_quote(channel_id):
  quote = generate_quote(channel_id)
  await channel_id.send(quote)
  await asyncio.sleep(12)

# Define an asynchronous function that sends the quote to each channel every 30 seconds
async def send_quotes():
  while True:
    for channel_name in labels_set:
      channel = discord.utils.get(client.get_all_channels(), name=channel_name)
      if channel is not None:
        await send_quote(channel)
      else:
        print(f"Could not find channel named {channel_name}")
    await asyncio.sleep(30)

@client.command(name="bye", help="Farewell message")
async def bye(ctx):
  username=str(ctx.author).split('#')[0]
  await ctx.send(f'Bye {username}!')

@client.command(name="classify", help="Be put in a therapy group based on your symptoms")
async def classify(ctx, *, text):
  
  response = co.classify(
  model='large',
  inputs=[text],
  examples=ex)

  prediction = response.classifications
  first_classification = prediction[0]
  first_prediction = max(first_classification.labels.items(), key=lambda x: x[1].confidence)
  # print(f"{first_prediction[0]}: {first_prediction[1].confidence}")

  category = first_prediction[0].lower().strip().replace(" ", "-")

  if category in labels_set:
    guild = ctx.guild
    # print(ctx.author.id)
    member = guild.get_member(ctx.author.id)

    # Find the matching channel name
    # channel_name = input_color

    # Find the matching channel object
    channel = discord.utils.get(guild.text_channels, name=category)

    if channel is not None:
      # Set permissions for the user to read and write messages in the channel
      await channel.set_permissions(member, read_messages=True, send_messages=True)
      await ctx.send(f"{ctx.author.mention}, you have been added to the {category} channel!")
    else:
      await ctx.send(f"{ctx.author.mention}, the {category} channel does not exist.")
  else:
    await ctx.send(f"{ctx.author.mention}, you do not qualify for any private channels.")
  await ctx.send(f'Group: {first_prediction[0]}')

@client.command(name="support", help="Ask for help or resources")
async def support(ctx, *, text):

  string = "Assume that you are a doctor and your time is very precious so will only respond to the following prompt if it is related to human physical, mental, or emotional health, otherwise you respond with 'Sorry, I can only answer your health queries': "  

  response = co.classify(
  model='large',
  inputs=[text],
  examples=hlth)

  prediction = response.classifications
  first_classification = prediction[0]
  first_prediction = max(first_classification.labels.items(), key=lambda x: x[1].confidence)

  if first_prediction[0] == 'Health':
    response = co.generate(
    model='command-xlarge-nightly',
    prompt=(text),
    max_tokens=300,
    temperature=0.9,
    k=0,
    stop_sequences=[],
    return_likelihoods='NONE')
    x = response.generations[0].text

    await ctx.send(f'{x}')
  else:
    await ctx.send(f'Sorry, I can only answer your health queries')

#@client.command(name="schedule", help="Schedule appointment with therapist")
async def schedule_event(ctx, date, time, *description):
  """Schedule an event on a Google Calendar."""
  credentials = Credentials.from_authorized_user_info(info=ctx.author)
  service = build('calendar', 'v3', credentials=credentials)

  event = {
    'summary': ' '.join(description),
    'start': {
      'dateTime': f'{date}T{time}:00-00:00',
      'timeZone': 'UTC',
    },
    'end': {
      'dateTime': f'{date}T{time}:00-00:00',
      'timeZone': 'UTC',
    },
  }

  event = calendar.events().insert(calendarId=CALENDAR_ID, body=event).execute()
  await ctx.send(f'Event created: {event["htmlLink"]}')

  # except HttpError as error:
  #   await ctx.send(f'An error  occurred: {error}')

client.run(TOKEN)
