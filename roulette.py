import sqlite3
import random

import nextcord
import asyncio
from nextcord.ext import commands
from nextcord.ui import View, button
from math import ceil

from db_core import get_conn

database = get_conn()
cursor = database.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movielist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL COLLATE NOCASE,
    UNIQUE (title)
);
""")
database.commit()



ITEMS_PER_PAGE = 10

class PagedEmbeds(View):
    """
    Vista con botones para navegar entre páginas de embeds.
    Úsala con una lista de nextcord.Embed ya construidos.
    """
    def __init__(self, pages: list[nextcord.Embed], author_id: int, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.pages = pages or [nextcord.Embed(description="No results.")]
        self.index = 0
        self.author_id = author_id
        if len(self.pages) <= 1:
            for child in self.children:
                child.disabled = True

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @button(label="⬅️", style=nextcord.ButtonStyle.secondary)
    async def prev_button(self, _btn, interaction: nextcord.Interaction):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @button(label="➡️", style=nextcord.ButtonStyle.secondary)
    async def next_button(self, _btn, interaction: nextcord.Interaction):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

def _split_pages_description(
    lines: list[str],
    title: str,
    color: nextcord.Colour
) -> list[nextcord.Embed]:
    """
    Corta una lista de líneas en páginas y arma embeds con la DESCRIPCIÓN.
    Cada página contiene hasta ITEMS_PER_PAGE líneas.
    """
    pages: list[nextcord.Embed] = []
    total_pages = max(1, ceil((len(lines) or 0) / ITEMS_PER_PAGE))

    for i in range(total_pages):
        start = i * ITEMS_PER_PAGE
        end = (i + 1) * ITEMS_PER_PAGE
        chunk = lines[start:end]

        embed = nextcord.Embed(title=title, color=color)
        if not chunk:
            embed.description = "No results."
        else:
            desc = "\n".join(chunk)
            embed.description = desc[:4096] if len(desc) > 4096 else desc

        embed.set_footer(text=f"Page {i+1}/{total_pages}")
        pages.append(embed)

    return pages

def build_movielist_pages(
    rows: list[tuple[int, str]],
    title: str = "All movies from the roulette:",
    color: nextcord.Colour = nextcord.Color.from_rgb(0, 0, 0)
) -> list[nextcord.Embed]:
    lines = [f"{i}. {r[1]} — ID: {r[0]}" for i, r in enumerate(rows, start=1)]
    return _split_pages_description(lines, title, color)



class db_roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = get_conn()
        self.cursor = self.db.cursor()



    @nextcord.slash_command(name="radd")
    async def radd(self,
                   interaction: nextcord.Interaction,
                   title: str = nextcord.SlashOption(description="Title of the movie", required=True)):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("INSERT INTO movielist (title) VALUES (?)", (title,))
            database.commit()
            cursor.execute("SELECT id, title FROM movielist WHERE title = ?", (title,))
            movie = cursor.fetchone()
            embed = nextcord.Embed(title=f"{title}", description=f"ID: {movie[0]}", color=nextcord.Color.from_rgb(0, 255, 0))
            await interaction.followup.send(f"Movie {title} added to the roulette.", embed=embed)
        except sqlite3.IntegrityError:
            await interaction.followup.send(f"Movie {title} already exists in the database.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    @nextcord.slash_command(name="redit")
    async def redit(self,
                   interaction: nextcord.Interaction,
                   id: str = nextcord.SlashOption(description="ID of the movie", required=True),
                   title: str = nextcord.SlashOption(description="New title of the movie", required=True)):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("UPDATE movielist SET title = ? WHERE id = ?", (title, id))
            database.commit()
            embed = nextcord.Embed(title=f"{title}", description=f"ID: {id}", color=nextcord.Color.from_rgb(0, 0, 255))
            await interaction.followup.send(f"Movie {title} edited in the roulette.", embed=embed)
        except sqlite3.IntegrityError:
            await interaction.followup.send(f"Movie {title} already exists in the database.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    @nextcord.slash_command(name="rshow")
    async def rshow(self,
                    interaction: nextcord.Interaction,
                    id: str = nextcord.SlashOption(description="ID of the movie", required=False, default=None),
                    title: str = nextcord.SlashOption(description="Title of the movie", required=False, default=None)):
        await interaction.response.defer(ephemeral=False)
        try:
            if not id and not title:
                cursor.execute("SELECT id, title FROM movielist ORDER BY title ASC, id ASC")
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send("No movies found.")
                    return
                lines = [f"{i}. {r[1]} — ID: {r[0]}" for i, r in enumerate(rows, start=1)]
                pages = _split_pages_description(
                    lines,
                    title="All movies from the roulette:",
                    color=nextcord.Color.from_rgb(0, 0, 0)
                )
                view = PagedEmbeds(pages, author_id=interaction.user.id)
                await interaction.followup.send(embed=pages[0], view=view)
                return
            if id and not title:
                cursor.execute("SELECT id, title FROM movielist WHERE id = ?", (id,))
                movie = cursor.fetchone()
                if not movie:
                    await interaction.followup.send(f"No movie found with ID {id}.")
                    return
                embed = nextcord.Embed(
                    title=movie[1],
                    description=f"ID: {movie[0]}",
                    color=nextcord.Color.from_rgb(0, 0, 255)
                )
                await interaction.followup.send(embed=embed)
                return
            if title and not id:
                cursor.execute("SELECT id, title FROM movielist WHERE title = ?", (title,))
                movie = cursor.fetchone()
                if not movie:
                    await interaction.followup.send(f"No movie found with title \"{title}\".")
                    return
                embed = nextcord.Embed(
                    title=movie[1],
                    description=f"ID: {movie[0]}",
                    color=nextcord.Color.from_rgb(0, 0, 255)
                )
                await interaction.followup.send(embed=embed)
                return
            cursor.execute("SELECT id, title FROM movielist WHERE id = ? AND title = ?", (id, title))
            movie = cursor.fetchone()
            if not movie:
                await interaction.followup.send(f"No movie found with ID {id} and title \"{title}\".")
                return
            embed = nextcord.Embed(
                title=movie[1],
                description=f"ID: {movie[0]}",
                color=nextcord.Color.from_rgb(0, 0, 255)
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    @nextcord.slash_command(name="rdel")
    async def rdelete(self,
                   interaction: nextcord.Interaction,
                   id: str = nextcord.SlashOption(description="ID of the movie", required=True),
                   title: str = nextcord.SlashOption(description="Title of the movie", required=True)):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("SELECT * FROM movielist WHERE id = ? AND title = ?", (id, title))
            movie = cursor.fetchone()
            if not movie:
                await interaction.followup.send(f"No movie found with ID {id} and title \"{title}\".")
                return
            cursor.execute("DELETE FROM movielist WHERE id = ? AND title = ?", (id, title))
            embed = nextcord.Embed(
                title=movie[1],
                description=f"ID: {movie[0]}",
                color=nextcord.Color.from_rgb(255, 0, 0)
            )
            await interaction.followup.send(f"Movie {title} deleted from the roulette.", embed=embed)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    @nextcord.slash_command(name="rspin")
    async def rspin(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("SELECT id, title FROM movielist ORDER BY title ASC, id ASC")
            rows = cursor.fetchall()
            if not rows:
                await interaction.followup.send("No movies found.")
                return
            movienum = random.randint(1, len(rows))
            movie = rows[movienum-1]
            embed = nextcord.Embed(color=nextcord.Color.from_rgb(128, 128, 128))
            embed.set_image(url="https://media.tenor.com/s7b_b-VcyHwAAAAM/spin.gif")
            message = await interaction.followup.send(embed=embed)
            await asyncio.sleep(4.8)
            embed = nextcord.Embed(
                title=movie[1],
                description=f"ID: {movie[0]}",
                color=nextcord.Color.from_rgb(255, 255, 255)
            )
            await message.edit(embed=embed)
            return
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



def setup(bot):
    bot.add_cog(db_roulette(bot))
