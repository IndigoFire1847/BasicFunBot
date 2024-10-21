import discord
import requests
import asyncio

from discord import app_commands
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix = "!", intents=intents)
TOKEN = # YOUR TOKEN GOES HERE, ENSURE IT IS IN ""
WEATHERKEY = # GET YOUR API KEY FROM OPENWEATHERMAP
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

@client.event
async def on_ready():
  print("ready")
  try:
    synced = await client.tree.sync()
    print(f"synced {len(synced)} command(s)")
  except Exception as e:
    print(e)

@client.tree.command(description="gets the bots ping!")
async def ping(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="ARL Bot ping")
        embed.add_field(name="Bot ping", value=f"{round(client.latency * 1000)}ms")
        await interaction.response.send_message(embed=embed, ephemeral = True)
    except Exception as e:
       await interaction.response.send_message(f"Error: {e}", ephemeral = True)

def get_weather(city):
  params = {
      'q': city,
      'appid': WEATHERKEY,
      'units': 'metric'  # You can use 'imperial' for Fahrenheit
  }
  response = requests.get(BASE_URL, params=params)
  return response.json()


# Function to get the weather data
def get_weather_data(city: str, units: str = 'metric'):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': WEATHERKEY,
        'units': units
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to convert Unix time to a readable format
def unix_to_readable_time(unix_time: int):
    return datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S UTC')

# Weather Command
@client.tree.command(name="weather", description="Get the current weather for a city.")
@app_commands.describe(city="Enter the city", units="Temperature unit (Celsius or Fahrenheit)")
async def weather_command(interaction: discord.Interaction, city: str, units: str = 'Celsius'):
    units = 'imperial' if units.lower() == 'fahrenheit' else 'metric'
    data = get_weather_data(city, units)

    if data:
        # Extracting necessary data
        city_name = data['name']
        country_code = data['sys']['country']
        weather_desc = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind_speed = data['wind']['speed']
        visibility = data.get('visibility', 'N/A') / 1000  # Convert meters to kilometers
        icon = data['weather'][0]['icon']
        sunrise = unix_to_readable_time(data['sys']['sunrise'])
        sunset = unix_to_readable_time(data['sys']['sunset'])

        # Create an embed with the weather information
        embed = discord.Embed(
            title=f"Weather in {city_name}, {country_code}",
            color=discord.Color.blue(),
            description=f"**{weather_desc}**"
        )
        embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{icon}.png")

        # Adding weather fields
        embed.add_field(name="Temperature", value=f"{temp}°{'C' if units == 'metric' else 'F'}", inline=True)
        embed.add_field(name="Feels Like", value=f"{feels_like}°{'C' if units == 'metric' else 'F'}", inline=True)
        embed.add_field(name="Humidity", value=f"{humidity}%", inline=True)
        embed.add_field(name="Pressure", value=f"{pressure} hPa", inline=True)
        embed.add_field(name="Visibility", value=f"{visibility} km", inline=True)
        embed.add_field(name="Wind Speed", value=f"{wind_speed} m/s", inline=True)
        embed.add_field(name="Sunrise", value=sunrise, inline=True)
        embed.add_field(name="Sunset", value=sunset, inline=True)

        embed.set_footer(text="Weather data provided by OpenWeatherMap")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:
        await interaction.response.send_message(f"Could not retrieve weather data for **{city}**. Please check the city name and try again.", ephemeral=True)


# Autocomplete for city names (Optional: Requires a list of cities)
@weather_command.autocomplete('city')
async def city_autocomplete(interaction: discord.Interaction, current: str):
    cities = ["New York", "Los Angeles", "London", "Tokyo", "Paris", "Berlin", "Sydney", "Edinburgh"]
    # Return city suggestions that match the current input
    return [app_commands.Choice(name=city, value=city) for city in cities if current.lower() in city.lower()]

# Define the counting channel ID and initialize the current count
COUNTING_CHANNEL_ID = # Insert your counting channel ID
current_count = 0

# Event to handle counting in the specified channel
@client.event
async def on_message(message):
    global current_count

    if message.channel.id == COUNTING_CHANNEL_ID and not message.author.bot:
        try:
            # Try to parse the message content as an integer
            count = int(message.content)
            if count == current_count + 1:
                # If the count is correct, update the current count
                current_count = count
                client_message = await message.reply(f'✅ Correct! The current count is now {current_count}.')
                await asyncio.sleep(5)
                await client_message.delete()
            else:
                # If the count is incorrect, notify the user and optionally delete the message
                client_message = await message.reply(f'❌ Wrong count! The count should be {current_count + 1}.')
                await asyncio.sleep(5)
                await message.delete()
                await client_message.delete()
        except ValueError:
            # If the message is not a valid number, notify the user and optionally delete the message
            client_message = await message.reply('❌ Please enter a valid number.')
            await asyncio.sleep(5)
            await message.delete()
            await client_message.delete()
    # Ensure other commands still work
    await client.process_commands(message)

# Slash command to reset the count, restricted to users with manage_messages permission
@client.tree.command(name='reset', description='Reset the counting channel')
@app_commands.checks.has_permissions(manage_messages=True)
async def reset_count(interaction: discord.Interaction):
    global current_count
    current_count = 13
    await interaction.response.send_message('The counting has been reset!', ephemeral=True)

# Slash command to get the current count
@client.tree.command(name='count', description='Get the current count')
async def current_count_command(interaction: discord.Interaction):
    await interaction.response.send_message(f'The current count is {current_count}.', ephemeral=True)

# Command to set the count (admin only)
@client.tree.command(name='setcount', description='Set the current count to a specific number (admin only)')
@app_commands.describe(number='The number to set the count to')
@app_commands.checks.has_permissions(manage_messages=True)  # Restrict to users with manage_messages permission
async def set_count(interaction: discord.Interaction, number: int):
    global current_count
    current_count = number
    await interaction.response.send_message(f'The count has been set to {current_count}.', ephemeral=True)
    client_message = await interaction.channel.send(f"The current count has been changed to {current_count} by {interaction.user}")
    await asyncio.sleep(5)
    await client_message.delete()

@client.tree.command(description = "Say what you say")
@app_commands.describe(message = "What am i saying on your behalf")
async def say(interaction: discord.Interaction, message: str):
    try:
        await interaction.response.send_message("Message sent.")
        await interaction.channel.send(message)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description="warm a user")
@app_commands.describe(user ="Who am i warming")
@app_commands.checks.has_permissions(manage_messages=True)
async def warm(interaction: discord.Interaction, user: discord.User):
    try:
        await interaction.response.send_message(f"warmed {user.mention}")
        await user.send(f"You were warmed in FAC by {interaction.user}")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description="create a poll")
@app_commands.describe(question = "What am i making a poll about?", option1 = "What is your first option?", option2 = "what is your second option?", option3 = "What is your third option")
@app_commands.checks.has_permissions(manage_messages=True)
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None):
    try:
        if option3 != None:
            await interaction.response.send_message("Poll Created", ephemeral = True)
            message = f"{question}: \n1️⃣ = {option1}\n2️⃣ = {option2}\n3️⃣ = {option3}"
            message = await interaction.channel.send(message) # Store the message object
            await message.add_reaction('1️⃣')
            await message.add_reaction('2️⃣')
            await message.add_reaction('3️⃣')
        else:
            await interaction.response.send_message("poll created!", ephemeral = True)
            message = f"{question}: \n1️⃣ = {option1}**\n**2️⃣ = {option2}"
            message = await interaction.channel.send(message) # Store the message object
            await message.add_reaction('1️⃣')
            await message.add_reaction('2️⃣')
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral = True)

client.run(TOKEN)